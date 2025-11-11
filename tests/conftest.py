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


@pytest.fixture
def api_client(monkeypatch, mock_model_loader, mock_model):
    """
    Fixture fournissant un client de test pour l'API FastAPI.

    Args:
        monkeypatch: Fixture pytest pour monkey patching.
        mock_model_loader: Mock du ModelLoader.
        mock_model: Mock du modèle ML.

    Returns:
        TestClient: Client de test FastAPI.
    """
    import logging

    # Mock du ModelLoader pour éviter de charger le vrai modèle
    from src.model import ModelLoader, Predictor

    def mock_loader_init(self):
        self.model = mock_model
        self._loaded = True

    monkeypatch.setattr(ModelLoader, "__init__", mock_loader_init)
    monkeypatch.setattr(ModelLoader, "load_model", lambda self: None)
    monkeypatch.setattr(ModelLoader, "is_loaded", lambda self: True)

    # Mock du Predictor
    import numpy as np

    mock_predictor = MagicMock(spec=Predictor)
    mock_predictor.model_loader = mock_model_loader
    mock_predictor.predict.return_value = np.array([1])
    mock_predictor.predict_proba.return_value = np.array([[0.2, 0.8]])

    # Mock du logger pour éviter l'erreur NoneType
    mock_logger = MagicMock(spec=logging.Logger)

    # Importer et patcher l'app
    from src.api import main
    monkeypatch.setattr(main, "logger", mock_logger)
    monkeypatch.setattr(main, "predictor", mock_predictor)

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
