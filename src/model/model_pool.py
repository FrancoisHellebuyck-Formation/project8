"""
Module pour gérer un pool de modèles ML permettant le parallélisme.

Ce module implémente un pool de singletons de modèles pour permettre
des prédictions simultanées sans contention, améliorant ainsi les
performances sous charge.
"""

import asyncio
import pickle
import threading
from pathlib import Path
from queue import Queue, Empty
from typing import Any, List, Optional

from ..config import settings


class ModelInstance:
    """
    Instance de modèle avec son propre état.

    Chaque instance possède sa propre copie du modèle pour
    éviter les problèmes de thread-safety.
    """

    def __init__(self, model: Any, instance_id: int):
        """
        Initialise une instance de modèle.

        Args:
            model: Le modèle ML chargé.
            instance_id: Identifiant unique de cette instance.
        """
        self.model = model
        self.instance_id = instance_id
        self.lock = threading.Lock()
        self.usage_count = 0

    def predict(self, data):
        """
        Effectue une prédiction avec ce modèle.

        Args:
            data: Les données préparées pour la prédiction.

        Returns:
            Les prédictions du modèle.
        """
        with self.lock:
            self.usage_count += 1
            return self.model.predict(data)

    def predict_proba(self, data):
        """
        Effectue une prédiction de probabilités avec ce modèle.

        Args:
            data: Les données préparées pour la prédiction.

        Returns:
            Les probabilités prédites.
        """
        with self.lock:
            self.usage_count += 1
            return self.model.predict_proba(data)


class ModelPool:
    """
    Pool de modèles ML pour permettre le parallélisme.

    Le pool maintient plusieurs instances du modèle pour permettre
    des prédictions simultanées sans contention. Utilise le pattern
    Object Pool pour réutiliser les instances de modèle.
    """

    _instance: Optional["ModelPool"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "ModelPool":
        """
        Crée ou retourne l'instance unique de ModelPool (Singleton).

        Returns:
            ModelPool: L'instance unique du pool.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialise le pool de modèles."""
        if self._initialized:
            return

        self._pool: Queue[ModelInstance] = Queue()
        self._model_instances: List[ModelInstance] = []
        self._pool_size: int = 0
        self._model_path: Optional[Path] = None
        self._initialized = True

    def initialize(
        self, pool_size: Optional[int] = None, model_path: Optional[str] = None
    ) -> None:
        """
        Initialise le pool avec des instances de modèle.

        Args:
            pool_size: Nombre d'instances de modèle à créer.
                      Si None, utilise MODEL_POOL_SIZE depuis config.
            model_path: Chemin vers le fichier du modèle.
                       Si None, utilise MODEL_PATH depuis config.

        Raises:
            FileNotFoundError: Si le fichier du modèle n'existe pas.
            Exception: Si le chargement du modèle échoue.
        """
        if self._pool_size > 0:
            print(f"Pool déjà initialisé avec {self._pool_size} instances")
            return

        # Déterminer la taille du pool
        if pool_size is None:
            pool_size = settings.MODEL_POOL_SIZE
        self._pool_size = pool_size

        # Déterminer le chemin du modèle
        if model_path is None:
            model_path = Path(settings.MODEL_PATH)
            if not model_path.is_absolute():
                project_root = Path(__file__).parent.parent.parent
                model_path = project_root / model_path
        else:
            model_path = Path(model_path)

        self._model_path = model_path

        if not model_path.exists():
            raise FileNotFoundError(
                f"Le fichier du modèle n'existe pas : {model_path}"
            )

        print(f"Initialisation du pool de {pool_size} modèles...")

        # Charger le modèle de base
        try:
            with open(model_path, "rb") as f:
                base_model = pickle.load(f)
            print(f"Modèle de base chargé depuis {model_path}")
        except Exception as e:
            raise Exception(
                f"Erreur lors du chargement du modèle : {str(e)}"
            ) from e

        # Créer les instances du pool
        for i in range(pool_size):
            # Créer une copie du modèle pour chaque instance
            # Note: pour certains modèles, on pourrait utiliser
            # sklearn.base.clone()
            # mais pickle.loads(pickle.dumps()) est plus universel
            try:
                model_copy = pickle.loads(pickle.dumps(base_model))
                instance = ModelInstance(model_copy, i)
                self._model_instances.append(instance)
                self._pool.put(instance)
                print(f"  Instance {i} créée et ajoutée au pool")
            except Exception as e:
                raise Exception(
                    f"Erreur lors de la création de l'instance {i}: {str(e)}"
                ) from e

        print(f"✅ Pool initialisé avec {pool_size} instances de modèle")

    def acquire(self, timeout: float = 30.0) -> ModelInstance:
        """
        Acquiert une instance de modèle depuis le pool.

        Args:
            timeout: Temps d'attente maximum en secondes.

        Returns:
            ModelInstance: Une instance de modèle disponible.

        Raises:
            TimeoutError: Si aucune instance n'est disponible
                         dans le délai imparti.
            RuntimeError: Si le pool n'est pas initialisé.
        """
        if self._pool_size == 0:
            raise RuntimeError(
                "Le pool n'est pas initialisé. "
                "Appelez initialize() d'abord."
            )

        try:
            instance = self._pool.get(timeout=timeout)
            return instance
        except Empty:
            raise TimeoutError(
                f"Aucune instance de modèle disponible après {timeout}s. "
                f"Pool saturé ({self._pool_size} instances)."
            )

    def release(self, instance: ModelInstance) -> None:
        """
        Libère une instance de modèle et la remet dans le pool.

        Args:
            instance: L'instance de modèle à libérer.
        """
        self._pool.put(instance)

    async def acquire_async(self, timeout: float = 30.0) -> ModelInstance:
        """
        Acquiert une instance de modèle de manière asynchrone.

        Args:
            timeout: Temps d'attente maximum en secondes.

        Returns:
            ModelInstance: Une instance de modèle disponible.

        Raises:
            TimeoutError: Si aucune instance n'est disponible
                         dans le délai imparti.
            RuntimeError: Si le pool n'est pas initialisé.
        """
        if self._pool_size == 0:
            raise RuntimeError(
                "Le pool n'est pas initialisé. "
                "Appelez initialize() d'abord."
            )

        loop = asyncio.get_event_loop()
        try:
            instance = await loop.run_in_executor(
                None, self._pool.get, True, timeout
            )
            return instance
        except Empty:
            raise TimeoutError(
                f"Aucune instance de modèle disponible après {timeout}s. "
                f"Pool saturé ({self._pool_size} instances)."
            )

    def get_stats(self) -> dict:
        """
        Retourne les statistiques du pool.

        Returns:
            dict: Statistiques incluant la taille du pool,
                  le nombre d'instances disponibles et l'utilisation.
        """
        available = self._pool.qsize()
        in_use = self._pool_size - available

        total_usage = sum(
            instance.usage_count for instance in self._model_instances
        )
        avg_usage = total_usage / self._pool_size if self._pool_size > 0 else 0

        return {
            "pool_size": self._pool_size,
            "available": available,
            "in_use": in_use,
            "total_predictions": total_usage,
            "avg_usage_per_instance": round(avg_usage, 2),
            "model_path": str(self._model_path) if self._model_path else None,
        }

    def is_initialized(self) -> bool:
        """
        Vérifie si le pool est initialisé.

        Returns:
            bool: True si le pool est initialisé, False sinon.
        """
        return self._pool_size > 0


# Context manager pour faciliter l'utilisation du pool
class ModelContextManager:
    """
    Context manager pour acquérir et libérer automatiquement
    une instance de modèle.

    Usage:
        async with ModelContextManager() as model_instance:
            predictions = model_instance.predict(data)
    """

    def __init__(
        self,
        pool: Optional['ModelPool'] = None,
        timeout: float = 30.0
    ):
        """
        Initialise le context manager.

        Args:
            pool: Instance du pool à utiliser. Si None, utilise le Singleton.
            timeout: Temps d'attente maximum pour acquérir une instance.
        """
        self.timeout = timeout
        self.instance: Optional[ModelInstance] = None
        self.pool = pool if pool is not None else ModelPool()

    async def __aenter__(self) -> ModelInstance:
        """
        Acquiert une instance de modèle au début du contexte.

        Returns:
            ModelInstance: L'instance de modèle acquise.
        """
        self.instance = await self.pool.acquire_async(self.timeout)
        return self.instance

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Libère l'instance de modèle à la fin du contexte.

        Args:
            exc_type: Type de l'exception (si une exception a été levée).
            exc_val: Valeur de l'exception.
            exc_tb: Traceback de l'exception.
        """
        if self.instance is not None:
            self.pool.release(self.instance)
        return False
