"""Tests pour le routeur de modèles ML."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from src.model.model_pool import ModelPool
from src.model.model_router import ModelRouter, ModelType


@pytest.fixture
def mock_sklearn_pool():
    """Fixture pour un pool sklearn mocké."""
    pool = MagicMock(spec=ModelPool)
    pool.get_stats.return_value = {
        "pool_size": 4,
        "available": 4,
        "in_use": 0,
        "total_predictions": 0
    }
    return pool


@pytest.fixture
def mock_onnx_pool():
    """Fixture pour un pool ONNX mocké."""
    pool = MagicMock(spec=ModelPool)
    pool.get_stats.return_value = {
        "pool_size": 4,
        "available": 4,
        "in_use": 0,
        "total_predictions": 0
    }
    return pool


@pytest.fixture
def router():
    """Fixture pour un nouveau routeur."""
    # Réinitialiser le singleton
    ModelRouter._instance = None
    return ModelRouter()


class TestModelRouterSingleton:
    """Tests pour le pattern Singleton."""

    def test_singleton_same_instance(self, router):
        """Test que le singleton retourne la même instance."""
        router2 = ModelRouter()
        assert router is router2

    def test_singleton_initialization_once(self, router):
        """Test que l'initialisation ne se fait qu'une fois."""
        assert router._initialized is True

        # Créer une nouvelle instance
        router2 = ModelRouter()
        assert router2._initialized is True
        assert router is router2


class TestModelRouterRegisterPool:
    """Tests pour l'enregistrement de pools."""

    def test_register_sklearn_pool(self, router, mock_sklearn_pool):
        """Test enregistrement d'un pool sklearn."""
        router.register_pool(ModelType.SKLEARN, mock_sklearn_pool)

        assert ModelType.SKLEARN in router._pools
        assert router._pools[ModelType.SKLEARN] is mock_sklearn_pool

    def test_register_onnx_pool(self, router, mock_onnx_pool):
        """Test enregistrement d'un pool ONNX."""
        router.register_pool(ModelType.ONNX, mock_onnx_pool)

        assert ModelType.ONNX in router._pools
        assert router._pools[ModelType.ONNX] is mock_onnx_pool

    def test_register_multiple_pools(
        self,
        router,
        mock_sklearn_pool,
        mock_onnx_pool
    ):
        """Test enregistrement de plusieurs pools."""
        router.register_pool(ModelType.SKLEARN, mock_sklearn_pool)
        router.register_pool(ModelType.ONNX, mock_onnx_pool)

        assert len(router._pools) == 2
        assert ModelType.SKLEARN in router._pools
        assert ModelType.ONNX in router._pools


class TestModelRouterSetDefaultType:
    """Tests pour la définition du type par défaut."""

    def test_set_default_type_sklearn(self, router, mock_sklearn_pool):
        """Test définition du type par défaut sklearn."""
        router.register_pool(ModelType.SKLEARN, mock_sklearn_pool)
        router.set_default_type(ModelType.SKLEARN)

        assert router._default_type == ModelType.SKLEARN

    def test_set_default_type_onnx(self, router, mock_onnx_pool):
        """Test définition du type par défaut ONNX."""
        router.register_pool(ModelType.ONNX, mock_onnx_pool)
        router.set_default_type(ModelType.ONNX)

        assert router._default_type == ModelType.ONNX

    def test_set_default_type_not_registered(self, router):
        """Test tentative de définir un type non enregistré."""
        # Ne devrait pas lever d'exception, juste un warning log
        router.set_default_type(ModelType.ONNX)

        # Le type par défaut reste sklearn
        assert router._default_type == ModelType.SKLEARN


class TestModelRouterGetPool:
    """Tests pour la récupération de pools."""

    def test_get_pool_default(self, router, mock_sklearn_pool):
        """Test récupération du pool par défaut."""
        router.register_pool(ModelType.SKLEARN, mock_sklearn_pool)

        pool = router.get_pool()

        assert pool is mock_sklearn_pool

    def test_get_pool_sklearn(self, router, mock_sklearn_pool):
        """Test récupération du pool sklearn."""
        router.register_pool(ModelType.SKLEARN, mock_sklearn_pool)

        pool = router.get_pool(ModelType.SKLEARN)

        assert pool is mock_sklearn_pool

    def test_get_pool_onnx(self, router, mock_onnx_pool):
        """Test récupération du pool ONNX."""
        router.register_pool(ModelType.ONNX, mock_onnx_pool)

        pool = router.get_pool(ModelType.ONNX)

        assert pool is mock_onnx_pool

    def test_get_pool_not_found(self, router):
        """Test récupération d'un pool non trouvé."""
        pool = router.get_pool(ModelType.ONNX)

        assert pool is None


class TestModelRouterAcquireModel:
    """Tests pour l'acquisition de modèles."""

    def test_acquire_model_default(self, router, mock_sklearn_pool):
        """Test acquisition depuis le pool par défaut."""
        router.register_pool(ModelType.SKLEARN, mock_sklearn_pool)

        with patch(
            "src.model.model_router.ModelContextManager"
        ) as mock_context:
            router.acquire_model()

            mock_context.assert_called_once_with(
                pool=mock_sklearn_pool,
                timeout=30.0
            )

    def test_acquire_model_sklearn(self, router, mock_sklearn_pool):
        """Test acquisition depuis le pool sklearn."""
        router.register_pool(ModelType.SKLEARN, mock_sklearn_pool)

        with patch(
            "src.model.model_router.ModelContextManager"
        ) as mock_context:
            router.acquire_model(ModelType.SKLEARN)

            mock_context.assert_called_once_with(
                pool=mock_sklearn_pool,
                timeout=30.0
            )

    def test_acquire_model_onnx(self, router, mock_onnx_pool):
        """Test acquisition depuis le pool ONNX."""
        router.register_pool(ModelType.ONNX, mock_onnx_pool)

        with patch(
            "src.model.model_router.ModelContextManager"
        ) as mock_context:
            router.acquire_model(ModelType.ONNX, timeout=60.0)

            mock_context.assert_called_once_with(
                pool=mock_onnx_pool,
                timeout=60.0
            )

    def test_acquire_model_not_available(self, router):
        """Test acquisition d'un pool non disponible."""
        with pytest.raises(ValueError) as exc_info:
            router.acquire_model(ModelType.ONNX)

        assert "non disponible" in str(exc_info.value)


class TestModelRouterGetStats:
    """Tests pour la récupération des statistiques."""

    def test_get_stats_empty(self, router):
        """Test récupération des stats sans pools."""
        stats = router.get_stats()

        assert stats["default_type"] == "sklearn"
        assert stats["pools"] == {}

    def test_get_stats_single_pool(self, router, mock_sklearn_pool):
        """Test récupération des stats avec un pool."""
        router.register_pool(ModelType.SKLEARN, mock_sklearn_pool)

        stats = router.get_stats()

        assert stats["default_type"] == "sklearn"
        assert "sklearn" in stats["pools"]
        assert stats["pools"]["sklearn"]["pool_size"] == 4

    def test_get_stats_multiple_pools(
        self,
        router,
        mock_sklearn_pool,
        mock_onnx_pool
    ):
        """Test récupération des stats avec plusieurs pools."""
        router.register_pool(ModelType.SKLEARN, mock_sklearn_pool)
        router.register_pool(ModelType.ONNX, mock_onnx_pool)

        stats = router.get_stats()

        assert "sklearn" in stats["pools"]
        assert "onnx" in stats["pools"]

    def test_get_stats_with_error(self, router, mock_sklearn_pool):
        """Test récupération des stats avec erreur."""
        mock_sklearn_pool.get_stats.side_effect = Exception("Pool error")
        router.register_pool(ModelType.SKLEARN, mock_sklearn_pool)

        stats = router.get_stats()

        assert "sklearn" in stats["pools"]
        assert "error" in stats["pools"]["sklearn"]
        assert "Pool error" in stats["pools"]["sklearn"]["error"]


class TestModelRouterGetAvailableTypes:
    """Tests pour la récupération des types disponibles."""

    def test_get_available_types_empty(self, router):
        """Test récupération des types sans pools."""
        types = router.get_available_types()

        assert types == []

    def test_get_available_types_sklearn(self, router, mock_sklearn_pool):
        """Test récupération des types avec sklearn."""
        router.register_pool(ModelType.SKLEARN, mock_sklearn_pool)

        types = router.get_available_types()

        assert "sklearn" in types
        assert len(types) == 1

    def test_get_available_types_multiple(
        self,
        router,
        mock_sklearn_pool,
        mock_onnx_pool
    ):
        """Test récupération des types avec plusieurs pools."""
        router.register_pool(ModelType.SKLEARN, mock_sklearn_pool)
        router.register_pool(ModelType.ONNX, mock_onnx_pool)

        types = router.get_available_types()

        assert "sklearn" in types
        assert "onnx" in types
        assert len(types) == 2


class TestModelRouterIsAvailable:
    """Tests pour la vérification de disponibilité."""

    def test_is_available_sklearn_true(self, router, mock_sklearn_pool):
        """Test disponibilité sklearn."""
        router.register_pool(ModelType.SKLEARN, mock_sklearn_pool)

        assert router.is_available(ModelType.SKLEARN) is True

    def test_is_available_onnx_true(self, router, mock_onnx_pool):
        """Test disponibilité ONNX."""
        router.register_pool(ModelType.ONNX, mock_onnx_pool)

        assert router.is_available(ModelType.ONNX) is True

    def test_is_available_false(self, router):
        """Test non-disponibilité."""
        assert router.is_available(ModelType.ONNX) is False


class TestModelRouterShutdown:
    """Tests pour l'arrêt du routeur."""

    def test_shutdown_empty(self, router):
        """Test arrêt sans pools."""
        # Ne devrait pas lever d'exception
        router.shutdown()

        assert len(router._pools) == 0

    def test_shutdown_with_pools(
        self,
        router,
        mock_sklearn_pool,
        mock_onnx_pool
    ):
        """Test arrêt avec des pools."""
        router.register_pool(ModelType.SKLEARN, mock_sklearn_pool)
        router.register_pool(ModelType.ONNX, mock_onnx_pool)

        router.shutdown()

        # Les pools sont affichés avant shutdown
        mock_sklearn_pool.get_stats.assert_called()
        mock_onnx_pool.get_stats.assert_called()

        # Les pools sont vidés
        assert len(router._pools) == 0

    def test_shutdown_with_error(self, router, mock_sklearn_pool):
        """Test arrêt avec erreur dans get_stats."""
        mock_sklearn_pool.get_stats.side_effect = Exception("Stats error")
        router.register_pool(ModelType.SKLEARN, mock_sklearn_pool)

        # Ne devrait pas lever d'exception
        router.shutdown()

        assert len(router._pools) == 0


class TestModelRouterRepr:
    """Tests pour la représentation du routeur."""

    def test_repr_empty(self, router):
        """Test représentation sans pools."""
        repr_str = repr(router)

        assert "ModelRouter" in repr_str
        assert "default=sklearn" in repr_str

    def test_repr_with_pools(
        self,
        router,
        mock_sklearn_pool,
        mock_onnx_pool
    ):
        """Test représentation avec des pools."""
        router.register_pool(ModelType.SKLEARN, mock_sklearn_pool)
        router.register_pool(ModelType.ONNX, mock_onnx_pool)

        repr_str = repr(router)

        assert "ModelRouter" in repr_str
        assert "default=sklearn" in repr_str
        assert "sklearn" in repr_str
        assert "onnx" in repr_str
