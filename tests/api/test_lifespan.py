"""
Tests for the FastAPI lifespan events.

This module tests the application startup and shutdown logic,
especially the model loading and fallback mechanisms.
"""

from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from src.api.main import app, ModelType

# Use a central place for mock paths to avoid typos
DUMMY_SKLEARN_MODEL_PATH = "dummy_sklearn.pkl"
DUMMY_ONNX_MODEL_PATH = "dummy_onnx.onnx"

@patch("src.api.main.ModelPool")
def test_successful_sklearn_pool_startup(mock_model_pool, monkeypatch):
    """
    Tests that the sklearn model pool is initialized on startup.
    """
    monkeypatch.setattr("src.config.settings.MODEL_PATH", DUMMY_SKLEARN_MODEL_PATH)
    monkeypatch.setattr("src.config.settings.ENABLE_ONNX", False)

    mock_sklearn_pool_instance = MagicMock()
    mock_model_pool.return_value = mock_sklearn_pool_instance

    with TestClient(app) as client:
        mock_sklearn_pool_instance.initialize.assert_called_once_with(
            pool_size=4,  # default value
            model_path=DUMMY_SKLEARN_MODEL_PATH
        )
        from src.api.main import model_router
        assert model_router.is_available(ModelType.SKLEARN)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

def test_sklearn_pool_failure_fallback(monkeypatch):
    """
    Tests that the application falls back to singleton mode if the
    sklearn pool fails to initialize, and that health check is correct.
    """
    monkeypatch.setattr("src.config.settings.MODEL_PATH", DUMMY_SKLEARN_MODEL_PATH)
    monkeypatch.setattr("src.config.settings.ENABLE_ONNX", False)

    # Mock ModelPool to fail
    with patch("src.api.main.ModelPool") as mock_model_pool:
        mock_model_pool.return_value.initialize.side_effect = Exception("Pool error")

        # Create a mock loader class that reports the model as loaded
        mock_loader_class = MagicMock()
        mock_loader_class.return_value.is_loaded.return_value = True
        mock_loader_class.return_value.load_model.return_value = None

        # Patch the ModelLoader class where it's imported and used
        monkeypatch.setattr("src.api.main.ModelLoader", mock_loader_class)
        monkeypatch.setattr("src.model.predictor.ModelLoader", mock_loader_class)

        with TestClient(app) as client:
            from src.api.main import model_router, predictor
            assert not model_router.is_available(ModelType.SKLEARN)
            assert predictor is not None
            response = client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"
            assert response.json()["model_loaded"] is True

@patch("src.api.main.ModelPool")
@patch("src.api.main.ONNXModelLoader")
@patch("pathlib.Path")
def test_successful_onnx_pool_startup(mock_path, mock_onnx_loader, mock_model_pool, monkeypatch):
    """
    Tests that the ONNX model pool is initialized on startup when enabled.
    """
    monkeypatch.setattr("src.config.settings.ENABLE_ONNX", True)
    monkeypatch.setattr("src.config.settings.ONNX_POOL_SIZE", 1)
    monkeypatch.setattr("src.config.settings.ONNX_MODEL_PATH", DUMMY_ONNX_MODEL_PATH)

    mock_path.return_value.exists.return_value = True
    mock_onnx_instance = MagicMock()
    mock_onnx_loader.return_value = mock_onnx_instance

    mock_sklearn_pool = MagicMock()
    mock_onnx_pool = MagicMock()
    mock_model_pool.side_effect = [mock_sklearn_pool, mock_onnx_pool]

    with TestClient(app):
        mock_onnx_pool.initialize.assert_called_with(
            pool_size=1, # default value
            model_path=DUMMY_ONNX_MODEL_PATH,
            base_model=mock_onnx_instance
        )
        from src.api.main import model_router
        assert model_router.is_available(ModelType.ONNX)

@patch("src.api.main.ModelPool")
@patch("pathlib.Path")
def test_onnx_pool_file_not_found(mock_path, mock_model_pool, monkeypatch):
    """
    Tests that the ONNX pool is not initialized if the model file is not found.
    """
    monkeypatch.setattr("src.config.settings.ENABLE_ONNX", True)
    monkeypatch.setattr("src.config.settings.ONNX_MODEL_PATH", "non_existent.onnx")

    mock_path.return_value.exists.side_effect = [True, False] # Sklearn OK, ONNX not found
    mock_model_pool.return_value = MagicMock() # Mock sklearn pool

    with TestClient(app):
        from src.api.main import model_router
        assert model_router.is_available(ModelType.SKLEARN) # Sklearn should be fine
        assert not model_router.is_available(ModelType.ONNX)

@patch("src.api.main.ModelPool")
@patch("pathlib.Path")
def test_onnx_pool_import_error(mock_path, mock_model_pool, monkeypatch):
    """
    Tests that the ONNX pool is not initialized if onnxruntime is not installed.
    """
    monkeypatch.setattr("src.config.settings.ENABLE_ONNX", True)
    mock_path.return_value.exists.return_value = True
    mock_model_pool.return_value = MagicMock()

    with patch("src.api.main.ONNXModelLoader", side_effect=ImportError):
        with TestClient(app):
            from src.api.main import model_router
            assert not model_router.is_available(ModelType.ONNX)

@patch("src.api.main.ModelPool")
@patch("src.api.main.ONNXModelLoader")
@patch("pathlib.Path")
def test_onnx_initialization_error(mock_path, mock_onnx_loader, mock_model_pool, monkeypatch):
    """
    Tests that a generic error during ONNX pool initialization is handled.
    """
    monkeypatch.setattr("src.config.settings.ENABLE_ONNX", True)
    mock_path.return_value.exists.return_value = True

    mock_sklearn_pool = MagicMock()
    mock_onnx_pool = MagicMock()
    mock_onnx_pool.initialize.side_effect = Exception("ONNX Pool error")
    mock_model_pool.side_effect = [mock_sklearn_pool, mock_onnx_pool]

    with patch("src.api.main.ModelLoader") as mock_loader:
        mock_loader.return_value.load_model.return_value = MagicMock()
        mock_loader.return_value.is_loaded.return_value = True

        with TestClient(app):
            from src.api.main import model_router
            assert model_router.is_available(ModelType.SKLEARN)
            assert not model_router.is_available(ModelType.ONNX)
