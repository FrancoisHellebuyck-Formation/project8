"""
Tests pour le module model_pool.

Ce module teste le pool de modèles permettant le parallélisme
des prédictions.
"""

import pickle
from unittest.mock import MagicMock

import pytest

from src.model.model_pool import (
    ModelContextManager,
    ModelInstance,
    ModelPool,
)


# Classe de modèle simple qui peut être pickled
class SimpleModel:
    """Modèle simple pour les tests (peut être pickled)."""

    def __init__(self):
        self.call_count = 0

    def predict(self, data):
        """Simule une prédiction."""
        self.call_count += 1
        return [1]

    def predict_proba(self, data):
        """Simule une prédiction de probabilités."""
        self.call_count += 1
        return [[0.3, 0.7]]


class TestModelInstance:
    """Tests pour la classe ModelInstance."""

    def test_model_instance_creation(self):
        """Test de la création d'une instance de modèle."""
        simple_model = SimpleModel()
        instance = ModelInstance(simple_model, instance_id=0)

        assert instance.model == simple_model
        assert instance.instance_id == 0
        assert instance.usage_count == 0

    def test_model_instance_predict(self):
        """Test de la méthode predict d'une instance."""
        simple_model = SimpleModel()
        instance = ModelInstance(simple_model, instance_id=0)

        result = instance.predict("test_data")

        assert result == [1]
        assert instance.usage_count == 1

    def test_model_instance_predict_proba(self):
        """Test de la méthode predict_proba d'une instance."""
        simple_model = SimpleModel()
        instance = ModelInstance(simple_model, instance_id=0)

        result = instance.predict_proba("test_data")

        assert result == [[0.3, 0.7]]
        assert instance.usage_count == 1

    def test_model_instance_usage_count_increments(self):
        """Test que usage_count s'incrémente correctement."""
        simple_model = SimpleModel()
        instance = ModelInstance(simple_model, instance_id=0)

        instance.predict("data1")
        instance.predict("data2")
        instance.predict_proba("data3")

        assert instance.usage_count == 3


class TestModelPool:
    """Tests pour la classe ModelPool."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset le singleton entre chaque test."""
        ModelPool._instance = None
        yield
        ModelPool._instance = None

    def test_model_pool_singleton(self):
        """Test que ModelPool est bien un singleton."""
        pool1 = ModelPool()
        pool2 = ModelPool()

        assert pool1 is pool2

    def test_model_pool_initialize_success(self, tmp_path):
        """Test de l'initialisation réussie du pool."""
        # Créer un modèle factice
        simple_model = SimpleModel()
        model_path = tmp_path / "test_model.pkl"
        with open(model_path, "wb") as f:
            pickle.dump(simple_model, f)

        pool = ModelPool()
        pool.initialize(pool_size=2, model_path=str(model_path))

        assert pool.is_initialized()
        stats = pool.get_stats()
        assert stats["pool_size"] == 2
        assert stats["available"] == 2
        assert stats["in_use"] == 0
        assert stats["total_predictions"] == 0

    def test_model_pool_initialize_file_not_found(self):
        """Test que l'initialisation échoue si le fichier n'existe pas."""
        pool = ModelPool()

        with pytest.raises(FileNotFoundError):
            pool.initialize(
                pool_size=2,
                model_path="/nonexistent/path/model.pkl"
            )

    def test_model_pool_acquire_and_release(self, tmp_path):
        """Test de l'acquisition et libération d'une instance."""
        # Créer un modèle factice
        simple_model = SimpleModel()
        model_path = tmp_path / "test_model.pkl"
        with open(model_path, "wb") as f:
            pickle.dump(simple_model, f)

        pool = ModelPool()
        pool.initialize(pool_size=2, model_path=str(model_path))

        # Acquérir une instance
        instance = pool.acquire(timeout=1.0)
        assert instance is not None
        assert isinstance(instance, ModelInstance)

        # Vérifier les stats
        stats = pool.get_stats()
        assert stats["available"] == 1
        assert stats["in_use"] == 1

        # Libérer l'instance
        pool.release(instance)

        # Vérifier les stats
        stats = pool.get_stats()
        assert stats["available"] == 2
        assert stats["in_use"] == 0

    def test_model_pool_acquire_timeout(self, tmp_path):
        """Test du timeout lors de l'acquisition."""
        # Créer un modèle factice
        simple_model = SimpleModel()
        model_path = tmp_path / "test_model.pkl"
        with open(model_path, "wb") as f:
            pickle.dump(simple_model, f)

        pool = ModelPool()
        pool.initialize(pool_size=1, model_path=str(model_path))

        # Acquérir la seule instance
        instance1 = pool.acquire(timeout=1.0)

        # Essayer d'en acquérir une autre (devrait timeout)
        with pytest.raises(TimeoutError, match="Aucune instance"):
            pool.acquire(timeout=0.1)

        # Libérer
        pool.release(instance1)

    def test_model_pool_acquire_not_initialized(self):
        """Test que acquire échoue si le pool n'est pas initialisé."""
        pool = ModelPool()

        with pytest.raises(RuntimeError, match="n'est pas initialisé"):
            pool.acquire()

    @pytest.mark.asyncio
    async def test_model_pool_acquire_async(self, tmp_path):
        """Test de l'acquisition asynchrone."""
        # Créer un modèle factice
        simple_model = SimpleModel()
        model_path = tmp_path / "test_model.pkl"
        with open(model_path, "wb") as f:
            pickle.dump(simple_model, f)

        pool = ModelPool()
        pool.initialize(pool_size=2, model_path=str(model_path))

        # Acquérir de manière asynchrone
        instance = await pool.acquire_async(timeout=1.0)
        assert instance is not None

        # Vérifier les stats
        stats = pool.get_stats()
        assert stats["in_use"] == 1

        # Libérer
        pool.release(instance)

    @pytest.mark.asyncio
    async def test_model_pool_acquire_async_timeout(self, tmp_path):
        """Test du timeout lors de l'acquisition asynchrone."""
        # Créer un modèle factice
        simple_model = SimpleModel()
        model_path = tmp_path / "test_model.pkl"
        with open(model_path, "wb") as f:
            pickle.dump(simple_model, f)

        pool = ModelPool()
        pool.initialize(pool_size=1, model_path=str(model_path))

        # Acquérir la seule instance
        instance1 = await pool.acquire_async(timeout=1.0)

        # Essayer d'en acquérir une autre (devrait timeout)
        with pytest.raises(TimeoutError):
            await pool.acquire_async(timeout=0.1)

        # Libérer
        pool.release(instance1)

    def test_model_pool_get_stats_not_initialized(self):
        """Test de get_stats sur un pool non initialisé."""
        pool = ModelPool()

        stats = pool.get_stats()
        assert stats["pool_size"] == 0
        assert stats["available"] == 0
        assert stats["in_use"] == 0
        assert stats["model_path"] is None

    def test_model_pool_initialize_twice(self, tmp_path):
        """Test qu'on ne peut pas initialiser deux fois."""
        # Créer un modèle factice
        simple_model = SimpleModel()
        model_path = tmp_path / "test_model.pkl"
        with open(model_path, "wb") as f:
            pickle.dump(simple_model, f)

        pool = ModelPool()
        pool.initialize(pool_size=2, model_path=str(model_path))

        # Essayer de réinitialiser (devrait être ignoré)
        pool.initialize(pool_size=4, model_path=str(model_path))

        # Vérifier que la taille est toujours 2
        stats = pool.get_stats()
        assert stats["pool_size"] == 2

    def test_model_pool_usage_tracking(self, tmp_path):
        """Test du suivi de l'utilisation du pool."""
        # Créer un modèle factice
        simple_model = SimpleModel()
        model_path = tmp_path / "test_model.pkl"
        with open(model_path, "wb") as f:
            pickle.dump(simple_model, f)

        pool = ModelPool()
        pool.initialize(pool_size=2, model_path=str(model_path))

        # Faire des prédictions
        instance1 = pool.acquire()
        instance1.predict("data1")
        instance1.predict("data2")
        pool.release(instance1)

        instance2 = pool.acquire()
        instance2.predict("data3")
        pool.release(instance2)

        # Vérifier les stats
        stats = pool.get_stats()
        assert stats["total_predictions"] == 3
        # Moyenne: 2 pour instance1, 1 pour instance2 = 3/2 = 1.5
        assert stats["avg_usage_per_instance"] == 1.5


class TestModelContextManager:
    """Tests pour le context manager ModelContextManager."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset le singleton entre chaque test."""
        ModelPool._instance = None
        yield
        ModelPool._instance = None

    @pytest.mark.asyncio
    async def test_context_manager_acquire_release(self, tmp_path):
        """Test que le context manager acquiert et libère correctement."""
        # Créer un modèle factice
        simple_model = SimpleModel()
        model_path = tmp_path / "test_model.pkl"
        with open(model_path, "wb") as f:
            pickle.dump(simple_model, f)

        pool = ModelPool()
        pool.initialize(pool_size=2, model_path=str(model_path))

        # Utiliser le context manager
        async with ModelContextManager() as instance:
            assert instance is not None
            # Pendant l'utilisation, une instance est en cours d'utilisation
            stats = pool.get_stats()
            assert stats["in_use"] == 1

        # Après le context, l'instance est libérée
        stats = pool.get_stats()
        assert stats["in_use"] == 0
        assert stats["available"] == 2

    @pytest.mark.asyncio
    async def test_context_manager_with_exception(self, tmp_path):
        """Test que le context manager libère même en cas d'exception."""
        # Créer un modèle factice
        simple_model = SimpleModel()
        model_path = tmp_path / "test_model.pkl"
        with open(model_path, "wb") as f:
            pickle.dump(simple_model, f)

        pool = ModelPool()
        pool.initialize(pool_size=2, model_path=str(model_path))

        # Utiliser le context manager avec une exception
        with pytest.raises(ValueError):
            async with ModelContextManager() as instance:
                assert instance is not None
                raise ValueError("Test exception")

        # L'instance devrait être libérée malgré l'exception
        stats = pool.get_stats()
        assert stats["in_use"] == 0
        assert stats["available"] == 2

    @pytest.mark.asyncio
    async def test_context_manager_timeout(self, tmp_path):
        """Test du timeout du context manager."""
        # Créer un modèle factice
        simple_model = SimpleModel()
        model_path = tmp_path / "test_model.pkl"
        with open(model_path, "wb") as f:
            pickle.dump(simple_model, f)

        pool = ModelPool()
        pool.initialize(pool_size=1, model_path=str(model_path))

        # Acquérir la seule instance
        async with ModelContextManager(timeout=1.0):
            # Essayer d'en acquérir une autre avec un timeout court
            with pytest.raises(TimeoutError):
                async with ModelContextManager(timeout=0.1):
                    pass
