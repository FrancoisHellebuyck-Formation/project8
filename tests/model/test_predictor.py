"""
Tests unitaires pour le module Predictor.

Ce module teste:
- Predictor.__init__()
- Predictor.predict()
- Predictor.predict_proba()
- Predictor.get_required_features()
"""

import numpy as np
import pandas as pd
import pytest

from src.model.feature_engineering import FeatureEngineer
from src.model.model_loader import ModelLoader
from src.model.predictor import Predictor


@pytest.fixture(autouse=True)
def reset_singleton(mock_model):
    """Reset ModelLoader singleton avant chaque test."""
    ModelLoader._instance = None
    ModelLoader._model = mock_model
    yield
    ModelLoader._instance = None
    ModelLoader._model = None


class TestPredictorInitialization:
    """Tests d'initialisation du Predictor."""

    def test_predictor_initialization(self):
        """Test que le Predictor s'initialise correctement."""
        predictor = Predictor()

        assert predictor.model_loader is not None
        assert predictor.feature_engineer is not None
        assert isinstance(predictor.feature_engineer, FeatureEngineer)


class TestPredictMethod:
    """Tests pour la méthode predict()."""

    def test_predict_with_dict(self, sample_patient_data):
        """Test predict avec un dictionnaire."""
        predictor = Predictor()
        result = predictor.predict(sample_patient_data)

        assert result is not None
        assert len(result) == 1
        assert result[0] in [0, 1]

    def test_predict_with_dataframe(self, sample_patient_df):
        """Test predict avec un DataFrame."""
        predictor = Predictor()
        result = predictor.predict(sample_patient_df)

        assert result is not None
        assert len(result) == 1

    def test_predict_calls_feature_engineering(
        self, sample_patient_data, monkeypatch
    ):
        """Test que predict appelle le feature engineering."""
        predictor = Predictor()

        # Mock de engineer_features pour vérifier l'appel
        original_engineer = FeatureEngineer.engineer_features
        called = []

        def mock_engineer(data):
            called.append(True)
            return original_engineer(data)

        monkeypatch.setattr(
            FeatureEngineer,
            "engineer_features",
            staticmethod(mock_engineer)
        )

        predictor.predict(sample_patient_data)
        assert len(called) == 1

    def test_predict_with_model_not_loaded(self, sample_patient_data):
        """Test predict quand le modèle n'est pas chargé."""
        # Forcer _model à None APRÈS création du predictor
        predictor = Predictor()
        ModelLoader._model = None

        with pytest.raises(RuntimeError, match="modèle n'est pas chargé"):
            predictor.predict(sample_patient_data)

    def test_predict_with_invalid_data(self):
        """Test predict avec données invalides."""
        predictor = Predictor()
        invalid_data = {"AGE": 50}  # Données incomplètes

        with pytest.raises(ValueError, match="Erreur lors de la prédiction"):
            predictor.predict(invalid_data)


class TestPredictProbaMethod:
    """Tests pour la méthode predict_proba()."""

    def test_predict_proba_with_dict(self, sample_patient_data):
        """Test predict_proba avec un dictionnaire."""
        predictor = Predictor()
        result = predictor.predict_proba(sample_patient_data)

        assert result is not None
        assert len(result) == 1
        assert len(result[0]) == 2  # Deux classes

    def test_predict_proba_with_dataframe(self, sample_patient_df):
        """Test predict_proba avec un DataFrame."""
        predictor = Predictor()
        result = predictor.predict_proba(sample_patient_df)

        assert result is not None
        assert len(result) == 1
        assert len(result[0]) == 2

    def test_predict_proba_probabilities_sum_to_one(
        self, sample_patient_data
    ):
        """Test que les probabilités somment à 1."""
        predictor = Predictor()
        result = predictor.predict_proba(sample_patient_data)

        # Somme proche de 1.0 (tolérance pour float)
        assert abs(sum(result[0]) - 1.0) < 0.01

    def test_predict_proba_all_probabilities_positive(
        self, sample_patient_data
    ):
        """Test que toutes les probabilités sont positives."""
        predictor = Predictor()
        result = predictor.predict_proba(sample_patient_data)

        for prob in result[0]:
            assert 0.0 <= prob <= 1.0

    def test_predict_proba_with_model_not_loaded(self, sample_patient_data):
        """Test predict_proba quand le modèle n'est pas chargé."""
        # Forcer _model à None APRÈS création du predictor
        predictor = Predictor()
        ModelLoader._model = None

        with pytest.raises(RuntimeError, match="modèle n'est pas chargé"):
            predictor.predict_proba(sample_patient_data)

    def test_predict_proba_without_method(self, sample_patient_data):
        """Test predict_proba si le modèle ne supporte pas predict_proba."""
        # Mock sans méthode predict_proba
        model_without_proba = type('Model', (), {
            'predict': lambda self, x: [1]
        })()

        ModelLoader._model = model_without_proba
        predictor = Predictor()

        with pytest.raises(
            AttributeError,
            match="ne supporte pas predict_proba"
        ):
            predictor.predict_proba(sample_patient_data)

    def test_predict_proba_with_invalid_data(self):
        """Test predict_proba avec données invalides."""
        predictor = Predictor()
        invalid_data = {"AGE": 50}  # Données incomplètes

        with pytest.raises(
            ValueError,
            match="Erreur lors de la prédiction de probabilités"
        ):
            predictor.predict_proba(invalid_data)


class TestGetRequiredFeatures:
    """Tests pour la méthode get_required_features()."""

    def test_get_required_features(self):
        """Test que get_required_features retourne les bonnes features."""
        predictor = Predictor()
        features = predictor.get_required_features()

        assert len(features) == 15
        assert "AGE" in features
        assert "GENDER" in features
        assert "SMOKING" in features

    def test_get_required_features_matches_feature_engineer(self):
        """Test que les features correspondent à FeatureEngineer."""
        predictor = Predictor()
        features = predictor.get_required_features()

        expected = FeatureEngineer.get_required_input_columns()
        assert features == expected


class TestPredictorIntegration:
    """Tests d'intégration du Predictor."""

    def test_predict_and_predict_proba_consistency(
        self, sample_patient_data
    ):
        """Test que predict et predict_proba sont cohérents."""
        predictor = Predictor()

        prediction = predictor.predict(sample_patient_data)
        probabilities = predictor.predict_proba(sample_patient_data)

        # La prédiction devrait correspondre à la classe avec la plus
        # haute probabilité
        predicted_class = int(prediction[0])
        max_prob_class = np.argmax(probabilities[0])

        assert predicted_class == max_prob_class

    def test_multiple_predictions(self):
        """Test plusieurs prédictions consécutives."""
        predictor = Predictor()

        data1 = {
            "AGE": 50,
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

        data2 = {
            "AGE": 70,
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

        result1 = predictor.predict(data1)
        result2 = predictor.predict(data2)

        assert result1 is not None
        assert result2 is not None

    def test_batch_prediction(self, mock_model):
        """Test prédiction batch avec plusieurs lignes."""
        # Mock qui gère plusieurs lignes
        mock_model.predict.return_value = np.array([1, 1])
        mock_model.predict_proba.return_value = np.array([[0.2, 0.8], [0.3, 0.7]])

        ModelLoader._model = mock_model
        predictor = Predictor()

        data = pd.DataFrame([
            {
                "AGE": 50,
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
            },
            {
                "AGE": 70,
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
        ])

        result = predictor.predict(data)
        assert len(result) == 2


class TestPredictorEdgeCases:
    """Tests de cas limites."""

    def test_predict_with_extreme_values(self):
        """Test prédiction avec valeurs extrêmes."""
        predictor = Predictor()

        # Patient très jeune
        data_young = {
            "AGE": 0,
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

        result = predictor.predict(data_young)
        assert result is not None

        # Patient très âgé
        data_old = data_young.copy()
        data_old["AGE"] = 120

        result = predictor.predict(data_old)
        assert result is not None

    def test_predict_no_feature_names_warning(self, sample_patient_data):
        """Vérifie qu'aucun warning de feature names n'est émis."""
        import warnings

        predictor = Predictor()

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # Faire une prédiction
            predictor.predict(sample_patient_data)

            # Vérifier qu'aucun warning de feature names n'a été émis
            feature_warnings = [
                warning for warning in w
                if 'feature names' in str(warning.message).lower()
            ]

            assert len(feature_warnings) == 0, (
                f"Warning de feature names détecté: {feature_warnings}"
            )
