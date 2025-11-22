"""Routeur de modèles ML.

Ce module fournit un routeur qui permet de choisir entre différents
types de modèles (ONNX, scikit-learn) en utilisant leurs pools respectifs.
"""

import logging
from enum import Enum
from typing import Optional

from .model_pool import ModelPool, ModelContextManager

logger = logging.getLogger(__name__)


class ModelType(str, Enum):
    """Types de modèles supportés."""
    SKLEARN = "sklearn"
    ONNX = "onnx"


class ModelRouter:
    """Routeur de modèles ML.

    Gère plusieurs pools de modèles et permet de router les requêtes
    vers le pool approprié selon le type de modèle demandé.

    Pattern: Singleton + Strategy Pattern
    """

    _instance: Optional['ModelRouter'] = None

    def __new__(cls):
        """Pattern Singleton."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialise le routeur."""
        if self._initialized:
            return

        self._pools: dict[ModelType, ModelPool] = {}
        self._default_type = ModelType.SKLEARN
        self._initialized = True
        logger.info("ModelRouter initialisé")

    def register_pool(
        self,
        model_type: ModelType,
        pool: ModelPool
    ) -> None:
        """Enregistre un pool de modèles.

        Args:
            model_type: Type de modèle (SKLEARN ou ONNX)
            pool: Instance du pool de modèles
        """
        self._pools[model_type] = pool
        logger.info(f"Pool {model_type.value} enregistré dans le routeur")

    def set_default_type(self, model_type: ModelType) -> None:
        """Définit le type de modèle par défaut.

        Args:
            model_type: Type de modèle par défaut
        """
        if model_type not in self._pools:
            logger.warning(
                f"Type {model_type.value} non enregistré, "
                f"impossible de le définir par défaut"
            )
            return

        self._default_type = model_type
        logger.info(f"Type de modèle par défaut: {model_type.value}")

    def get_pool(
        self,
        model_type: Optional[ModelType] = None
    ) -> Optional[ModelPool]:
        """Récupère un pool de modèles.

        Args:
            model_type: Type de modèle demandé (None = type par défaut)

        Returns:
            Le pool de modèles correspondant ou None si non trouvé
        """
        if model_type is None:
            model_type = self._default_type

        pool = self._pools.get(model_type)
        if pool is None:
            logger.error(f"Pool {model_type.value} non trouvé")

        return pool

    def acquire_model(
        self,
        model_type: Optional[ModelType] = None,
        timeout: float = 30.0
    ):
        """Acquiert un modèle du pool approprié.

        Args:
            model_type: Type de modèle demandé (None = type par défaut)
            timeout: Timeout en secondes

        Returns:
            Context manager pour l'acquisition du modèle

        Raises:
            ValueError: Si le pool demandé n'existe pas
        """
        pool = self.get_pool(model_type)
        if pool is None:
            raise ValueError(
                f"Pool {model_type.value if model_type else 'default'} "
                "non disponible"
            )

        return ModelContextManager(pool=pool, timeout=timeout)

    def get_stats(self) -> dict:
        """Récupère les statistiques de tous les pools.

        Returns:
            Dictionnaire avec les stats de chaque pool
        """
        stats = {
            "default_type": self._default_type.value,
            "pools": {}
        }

        for model_type, pool in self._pools.items():
            try:
                pool_stats = pool.get_stats()
                stats["pools"][model_type.value] = pool_stats
            except Exception as e:
                logger.error(
                    f"Erreur lors de la récupération des stats "
                    f"du pool {model_type.value}: {e}"
                )
                stats["pools"][model_type.value] = {
                    "error": str(e)
                }

        return stats

    def get_available_types(self) -> list[str]:
        """Récupère la liste des types de modèles disponibles.

        Returns:
            Liste des types de modèles enregistrés
        """
        return [t.value for t in self._pools.keys()]

    def is_available(self, model_type: ModelType) -> bool:
        """Vérifie si un type de modèle est disponible.

        Args:
            model_type: Type de modèle à vérifier

        Returns:
            True si le pool est disponible, False sinon
        """
        return model_type in self._pools

    def shutdown(self) -> None:
        """Arrête tous les pools proprement."""
        logger.info("Arrêt du ModelRouter...")
        for model_type, pool in self._pools.items():
            try:
                logger.info(f"Arrêt du pool {model_type.value}...")
                # Afficher les stats avant shutdown
                stats = pool.get_stats()
                logger.info(f"Stats finales {model_type.value}: {stats}")
            except Exception as e:
                logger.error(
                    f"Erreur lors de l'arrêt du pool {model_type.value}: {e}"
                )

        self._pools.clear()
        logger.info("ModelRouter arrêté")

    def __repr__(self) -> str:
        """Représentation du routeur."""
        pools_info = ", ".join([
            f"{t.value}" for t in self._pools.keys()
        ])
        return (
            f"ModelRouter(default={self._default_type.value}, "
            f"pools=[{pools_info}])"
        )
