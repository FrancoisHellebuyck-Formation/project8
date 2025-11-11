"""
Tests unitaires pour les schémas Pydantic de l'API.

Ce module teste la validation des modèles de données:
- PatientData
- PredictionResponse
- PredictionProbabilityResponse
- HealthResponse
- LogsResponse
"""

import pytest
from pydantic import ValidationError

from src.api.schemas import (
    HealthResponse,
    LogEntry,
    LogsResponse,
    PatientData,
    PredictionProbabilityResponse,
    PredictionResponse,
)


class TestPatientDataSchema:
    """Tests pour le schéma PatientData."""

    def test_valid_patient_data(self, sample_patient_data):
        """Test création avec données valides."""
        patient = PatientData(**sample_patient_data)

        assert patient.AGE == 65
        assert patient.GENDER == 1
        assert patient.SMOKING == 1

    def test_patient_data_with_alias(self):
        """Test que les alias fonctionnent correctement."""
        data = {
            "AGE": 50,
            "GENDER": 1,
            "SMOKING": 1,
            "ALCOHOL CONSUMING": 1,  # Avec espace (alias)
            "PEER_PRESSURE": 0,
            "YELLOW_FINGERS": 1,
            "ANXIETY": 0,
            "FATIGUE": 1,
            "ALLERGY": 0,
            "WHEEZING": 1,
            "COUGHING": 1,
            "SHORTNESS OF BREATH": 1,  # Avec espace (alias)
            "SWALLOWING DIFFICULTY": 0,  # Avec espace (alias)
            "CHEST PAIN": 1,  # Avec espace (alias)
            "CHRONIC DISEASE": 0  # Avec espace (alias)
        }

        patient = PatientData(**data)
        assert patient.ALCOHOL_CONSUMING == 1
        assert patient.SHORTNESS_OF_BREATH == 1
        assert patient.SWALLOWING_DIFFICULTY == 0
        assert patient.CHEST_PAIN == 1
        assert patient.CHRONIC_DISEASE == 0

    def test_patient_data_age_validation(self):
        """Test validation de l'âge."""
        # Âge négatif
        with pytest.raises(ValidationError):
            PatientData(
                AGE=-1,
                GENDER=1,
                SMOKING=1,
                ALCOHOL_CONSUMING=1,
                PEER_PRESSURE=0,
                YELLOW_FINGERS=1,
                ANXIETY=0,
                FATIGUE=1,
                ALLERGY=0,
                WHEEZING=1,
                COUGHING=1,
                SHORTNESS_OF_BREATH=1,
                SWALLOWING_DIFFICULTY=0,
                CHEST_PAIN=1,
                CHRONIC_DISEASE=0
            )

        # Âge trop élevé
        with pytest.raises(ValidationError):
            PatientData(
                AGE=150,
                GENDER=1,
                SMOKING=1,
                ALCOHOL_CONSUMING=1,
                PEER_PRESSURE=0,
                YELLOW_FINGERS=1,
                ANXIETY=0,
                FATIGUE=1,
                ALLERGY=0,
                WHEEZING=1,
                COUGHING=1,
                SHORTNESS_OF_BREATH=1,
                SWALLOWING_DIFFICULTY=0,
                CHEST_PAIN=1,
                CHRONIC_DISEASE=0
            )

    def test_patient_data_gender_validation(self, sample_patient_data):
        """Test validation du genre."""
        # Genre invalide (> 1)
        invalid_data = sample_patient_data.copy()
        invalid_data["GENDER"] = 2

        with pytest.raises(ValidationError):
            PatientData(**invalid_data)

        # Genre invalide (< 0)
        invalid_data["GENDER"] = -1
        with pytest.raises(ValidationError):
            PatientData(**invalid_data)

    def test_patient_data_binary_fields_validation(
        self, sample_patient_data
    ):
        """Test validation des champs binaires."""
        # SMOKING invalide
        invalid_data = sample_patient_data.copy()
        invalid_data["SMOKING"] = 2

        with pytest.raises(ValidationError):
            PatientData(**invalid_data)

    def test_patient_data_missing_field(self, sample_patient_data):
        """Test qu'un champ manquant lève une erreur."""
        incomplete_data = sample_patient_data.copy()
        del incomplete_data["AGE"]

        with pytest.raises(ValidationError):
            PatientData(**incomplete_data)

    def test_patient_data_extra_field(self, sample_patient_data):
        """Test qu'un champ supplémentaire est ignoré par Pydantic v2."""
        data_with_extra = sample_patient_data.copy()
        data_with_extra["EXTRA_FIELD"] = 999

        # Pydantic v2 ignore les champs extra par défaut avec populate_by_name
        patient = PatientData(**data_with_extra)
        assert patient.AGE == sample_patient_data["AGE"]
        # Vérifier que EXTRA_FIELD n'est pas dans le modèle
        assert not hasattr(patient, "EXTRA_FIELD")

    def test_patient_data_model_dump(self, sample_patient_data):
        """Test la méthode model_dump avec alias."""
        patient = PatientData(**sample_patient_data)
        dumped = patient.model_dump(by_alias=True)

        # Vérifier que les alias sont utilisés
        assert "ALCOHOL CONSUMING" in dumped
        assert "SHORTNESS OF BREATH" in dumped
        assert "SWALLOWING DIFFICULTY" in dumped
        assert "CHEST PAIN" in dumped
        assert "CHRONIC DISEASE" in dumped


class TestPredictionResponseSchema:
    """Tests pour le schéma PredictionResponse."""

    def test_prediction_response_with_probability(self):
        """Test création avec probabilité."""
        response = PredictionResponse(
            prediction=1,
            probability=0.85,
            message="Prédiction positive"
        )

        assert response.prediction == 1
        assert response.probability == 0.85
        assert response.message == "Prédiction positive"

    def test_prediction_response_without_probability(self):
        """Test création sans probabilité."""
        response = PredictionResponse(
            prediction=0,
            probability=None,
            message="Prédiction négative"
        )

        assert response.prediction == 0
        assert response.probability is None
        assert response.message == "Prédiction négative"

    def test_prediction_response_validation(self):
        """Test validation des champs."""
        # Champ manquant
        with pytest.raises(ValidationError):
            PredictionResponse(prediction=1, probability=0.5)


class TestPredictionProbabilityResponseSchema:
    """Tests pour le schéma PredictionProbabilityResponse."""

    def test_prediction_probability_response(self):
        """Test création avec liste de probabilités."""
        response = PredictionProbabilityResponse(
            prediction=1,
            probabilities=[0.2, 0.8],
            message="Prédiction positive"
        )

        assert response.prediction == 1
        assert len(response.probabilities) == 2
        assert response.probabilities[0] == 0.2
        assert response.probabilities[1] == 0.8

    def test_prediction_probability_response_validation(self):
        """Test validation des champs."""
        # Probabilités manquantes
        with pytest.raises(ValidationError):
            PredictionProbabilityResponse(
                prediction=1,
                message="Test"
            )


class TestHealthResponseSchema:
    """Tests pour le schéma HealthResponse."""

    def test_health_response_healthy(self):
        """Test création avec statut healthy."""
        response = HealthResponse(
            status="healthy",
            model_loaded=True,
            redis_connected=True,
            version="1.0.0"
        )

        assert response.status == "healthy"
        assert response.model_loaded is True
        assert response.redis_connected is True
        assert response.version == "1.0.0"

    def test_health_response_unhealthy(self):
        """Test création avec statut unhealthy."""
        response = HealthResponse(
            status="unhealthy",
            model_loaded=False,
            redis_connected=False,
            version="1.0.0"
        )

        assert response.status == "unhealthy"
        assert response.model_loaded is False
        assert response.redis_connected is False

    def test_health_response_validation(self):
        """Test validation des champs requis."""
        with pytest.raises(ValidationError):
            HealthResponse(
                status="healthy",
                model_loaded=True
                # Champs manquants
            )


class TestLogEntrySchema:
    """Tests pour le schéma LogEntry."""

    def test_log_entry_with_data(self):
        """Test création avec données additionnelles."""
        log = LogEntry(
            timestamp="2025-01-01 12:00:00",
            level="INFO",
            message="Test message",
            data={"key": "value"}
        )

        assert log.timestamp == "2025-01-01 12:00:00"
        assert log.level == "INFO"
        assert log.message == "Test message"
        assert log.data == {"key": "value"}

    def test_log_entry_without_data(self):
        """Test création sans données additionnelles."""
        log = LogEntry(
            timestamp="2025-01-01 12:00:00",
            level="ERROR",
            message="Error message",
            data=None
        )

        assert log.data is None

    def test_log_entry_validation(self):
        """Test validation des champs requis."""
        with pytest.raises(ValidationError):
            LogEntry(
                timestamp="2025-01-01 12:00:00",
                level="INFO"
                # Message manquant
            )


class TestLogsResponseSchema:
    """Tests pour le schéma LogsResponse."""

    def test_logs_response(self):
        """Test création avec liste de logs."""
        logs = [
            LogEntry(
                timestamp="2025-01-01 12:00:00",
                level="INFO",
                message="Message 1",
                data=None
            ),
            LogEntry(
                timestamp="2025-01-01 12:01:00",
                level="ERROR",
                message="Message 2",
                data={"error": "details"}
            )
        ]

        response = LogsResponse(total=2, logs=logs)

        assert response.total == 2
        assert len(response.logs) == 2
        assert response.logs[0].message == "Message 1"
        assert response.logs[1].level == "ERROR"

    def test_logs_response_empty(self):
        """Test création avec liste vide."""
        response = LogsResponse(total=0, logs=[])

        assert response.total == 0
        assert len(response.logs) == 0

    def test_logs_response_validation(self):
        """Test validation des champs requis."""
        with pytest.raises(ValidationError):
            LogsResponse(logs=[])  # total manquant


class TestSchemaEdgeCases:
    """Tests de cas limites pour les schémas."""

    def test_patient_data_boundary_values(self):
        """Test valeurs aux limites."""
        # Âge minimum
        patient = PatientData(
            AGE=0,
            GENDER=0,
            SMOKING=0,
            ALCOHOL_CONSUMING=0,
            PEER_PRESSURE=0,
            YELLOW_FINGERS=0,
            ANXIETY=0,
            FATIGUE=0,
            ALLERGY=0,
            WHEEZING=0,
            COUGHING=0,
            SHORTNESS_OF_BREATH=0,
            SWALLOWING_DIFFICULTY=0,
            CHEST_PAIN=0,
            CHRONIC_DISEASE=0
        )
        assert patient.AGE == 0

        # Âge maximum
        patient = PatientData(
            AGE=120,
            GENDER=1,
            SMOKING=1,
            ALCOHOL_CONSUMING=1,
            PEER_PRESSURE=1,
            YELLOW_FINGERS=1,
            ANXIETY=1,
            FATIGUE=1,
            ALLERGY=1,
            WHEEZING=1,
            COUGHING=1,
            SHORTNESS_OF_BREATH=1,
            SWALLOWING_DIFFICULTY=1,
            CHEST_PAIN=1,
            CHRONIC_DISEASE=1
        )
        assert patient.AGE == 120

    def test_prediction_response_edge_probabilities(self):
        """Test probabilités aux limites."""
        # Probabilité 0
        response = PredictionResponse(
            prediction=0,
            probability=0.0,
            message="Test"
        )
        assert response.probability == 0.0

        # Probabilité 1
        response = PredictionResponse(
            prediction=1,
            probability=1.0,
            message="Test"
        )
        assert response.probability == 1.0
