"""
Configuration pytest et fixtures partagées pour tous les tests.

Ce module contient les fixtures utilisées par les tests unitaires
et d'intégration.
"""

import os
from unittest.mock import MagicMock, Mock

import pandas as pd
import pytest
from fastapi.testclient import TestClient

# Forcer l'utilisation de stdout pour les tests
os.environ["LOGGING_HANDLER"] = "stdout"


@pytest.fixture
def sample_patient_data():
    """
    Fixture fournissant des données patient valides pour les tests.

    Returns:
        dict: Données patient avec toutes les features requises.
    """
    return {
        "AGE": 65,
        "GENDER": 1,
        "SMOKING": 1,
        "ALCOHOL CONSUMING": 1,
        "PEER_PRESSURE": 0,
        "YELLOW_FINGERS": 1,
        "ANXIETY": 0,
        "FATIGUE": 1,
        "ALLERGY": 0,
        "WHEEZING": 1,
        "COUGHING": 1,
        "SHORTNESS OF BREATH": 1,
        "SWALLOWING DIFFICULTY": 0,
        "CHEST PAIN": 1,
        "CHRONIC DISEASE": 0
    }


@pytest.fixture
def sample_patient_df(sample_patient_data):
    """
    Fixture fournissant un DataFrame patient valide.

    Args:
        sample_patient_data: Données patient de la fixture.

    Returns:
        pd.DataFrame: DataFrame avec données patient.
    """
    return pd.DataFrame([sample_patient_data])


@pytest.fixture
def mock_model():
    """
    Fixture fournissant un mock de modèle ML.

    Returns:
        MagicMock: Mock du modèle avec méthodes predict et predict_proba.
    """
    model = MagicMock()
    model.predict.return_value = [1]
    model.predict_proba.return_value = [[0.2, 0.8]]
    return model


@pytest.fixture
def mock_model_loader(mock_model):
    """
    Fixture fournissant un mock de ModelLoader.

    Args:
        mock_model: Mock du modèle.

    Returns:
        Mock: Mock du ModelLoader avec modèle chargé.
    """
    loader = Mock()
    loader.model = mock_model
    loader.is_loaded.return_value = True
    loader.load_model.return_value = None
    return loader


from contextlib import asynccontextmanager

from contextlib import asynccontextmanager
from unittest.mock import MagicMock
import numpy as np
import pytest

@pytest.fixture
def api_client(monkeypatch):
    """
    Fixture fournissant un client de test pour l'API FastAPI.

    Cette fixture configure les mocks nécessaires pour que le lifespan
    de l'application s'exécute, mais utilise des dépendances mockées
    pour le chargement des modèles et autres services externes.
    """
    from src.api import main
    from src.model import ModelType

    # Mock ModelLoader
    mock_loader_class = MagicMock()
    mock_loader_class.return_value.is_loaded.return_value = True
    mock_loader_class.return_value.load_model.return_value = None
    monkeypatch.setattr("src.api.main.ModelLoader", mock_loader_class)
    monkeypatch.setattr("src.model.predictor.ModelLoader", mock_loader_class)

    # Mock ONNXModelLoader
    mock_onnx_loader = MagicMock()
    monkeypatch.setattr("src.api.main.ONNXModelLoader", mock_onnx_loader)

    # Mock Path.exists to prevent FileNotFoundError
    mock_path_class = MagicMock()
    mock_path_class.return_value.exists.return_value = True
    monkeypatch.setattr("pathlib.Path", mock_path_class)

    # Mock ModelPool
    mock_sklearn_pool_instance = MagicMock()
    mock_sklearn_pool_instance.initialize.return_value = None
    mock_onnx_pool_instance = MagicMock()
    mock_onnx_pool_instance.initialize.return_value = None
    mock_model_pool_class = MagicMock()
    mock_model_pool_class.side_effect = [mock_sklearn_pool_instance, mock_onnx_pool_instance]
    monkeypatch.setattr("src.api.main.ModelPool", mock_model_pool_class)

    # Mock the router and its model instance
    mock_router = MagicMock()
    mock_model_instance = MagicMock()
    mock_model_instance.predict.return_value = np.array([1])
    mock_model_instance.predict_proba.return_value = np.array([[0.2, 0.8]])

    @asynccontextmanager
    async def mock_acquire_model(*args, **kwargs):
        yield mock_model_instance

    mock_router.acquire_model.return_value = mock_acquire_model()
    mock_router.is_available.side_effect = lambda x: x == ModelType.SKLEARN
    mock_router.get_available_types.return_value = [ModelType.SKLEARN]
    mock_router._default_type = ModelType.SKLEARN # Set default type for testing

    # Patch global variables in main that are not covered by lifespan
    monkeypatch.setattr(main, "model_router", mock_router)
    monkeypatch.setattr(main, "predictor", MagicMock())
    monkeypatch.setattr(main, "feature_engineer", MagicMock())
    monkeypatch.setattr(main, "logger", MagicMock()) # Mock the logger as well

    from fastapi.testclient import TestClient
    return TestClient(main.app)


@pytest.fixture
def invalid_patient_data():
    """
    Fixture fournissant des données patient invalides pour les tests.

    Returns:
        dict: Données patient avec valeurs hors limites.
    """
    return {
        "AGE": 150,  # Invalide: > 120
        "GENDER": 2,  # Invalide: > 1
        "SMOKING": -1,  # Invalide: < 0
        "ALCOHOL CONSUMING": 1,
        "PEER_PRESSURE": 0,
        "YELLOW_FINGERS": 1,
        "ANXIETY": 0,
        "FATIGUE": 1,
        "ALLERGY": 0,
        "WHEEZING": 1,
        "COUGHING": 1,
        "SHORTNESS OF BREATH": 1,
        "SWALLOWING DIFFICULTY": 0,
        "CHEST PAIN": 1,
        "CHRONIC DISEASE": 0
    }


@pytest.fixture
def minimal_symptoms_patient():
    """
    Fixture fournissant un patient avec symptômes minimaux.

    Returns:
        dict: Patient jeune sans facteurs de risque.
    """
    return {
        "AGE": 25,
        "GENDER": 0,
        "SMOKING": 0,
        "ALCOHOL CONSUMING": 0,
        "PEER_PRESSURE": 0,
        "YELLOW_FINGERS": 0,
        "ANXIETY": 0,
        "FATIGUE": 0,
        "ALLERGY": 0,
        "WHEEZING": 0,
        "COUGHING": 0,
        "SHORTNESS OF BREATH": 0,
        "SWALLOWING DIFFICULTY": 0,
        "CHEST PAIN": 0,
        "CHRONIC DISEASE": 0
    }


@pytest.fixture
def high_risk_patient():
    """
    Fixture fournissant un patient à haut risque.

    Returns:
        dict: Patient avec tous les facteurs de risque.
    """
    return {
        "AGE": 75,
        "GENDER": 1,
        "SMOKING": 1,
        "ALCOHOL CONSUMING": 1,
        "PEER_PRESSURE": 1,
        "YELLOW_FINGERS": 1,
        "ANXIETY": 1,
        "FATIGUE": 1,
        "ALLERGY": 1,
        "WHEEZING": 1,
        "COUGHING": 1,
        "SHORTNESS OF BREATH": 1,
        "SWALLOWING DIFFICULTY": 1,
        "CHEST PAIN": 1,
        "CHRONIC DISEASE": 1
    }
