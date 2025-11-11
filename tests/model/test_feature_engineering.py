"""
Tests unitaires pour le module de feature engineering.

Ce module teste:
- FeatureEngineer.engineer_features()
- FeatureEngineer._add_derived_features()
- FeatureEngineer._reorder_columns()
- FeatureEngineer.get_required_input_columns()
- FeatureEngineer.get_derived_columns()
"""

import numpy as np
import pandas as pd
import pytest

from src.model.feature_engineering import FeatureEngineer


class TestFeatureEngineerBasics:
    """Tests de base pour FeatureEngineer."""

    def test_engineer_features_with_dict(self, sample_patient_data):
        """Test engineer_features avec un dictionnaire."""
        result = FeatureEngineer.engineer_features(sample_patient_data)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert len(result.columns) == 29  # 15 input + 14 derived

    def test_engineer_features_with_dataframe(self, sample_patient_df):
        """Test engineer_features avec un DataFrame."""
        result = FeatureEngineer.engineer_features(sample_patient_df)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert len(result.columns) == 29

    def test_engineer_features_preserves_original_features(
        self, sample_patient_data
    ):
        """Test que les features originales sont préservées."""
        result = FeatureEngineer.engineer_features(sample_patient_data)

        # Vérifier les features originales
        assert result["AGE"].iloc[0] == sample_patient_data["AGE"]
        assert result["GENDER"].iloc[0] == sample_patient_data["GENDER"]
        assert result["SMOKING"].iloc[0] == sample_patient_data["SMOKING"]


class TestDerivedFeatures:
    """Tests pour les features dérivées."""

    def test_smoking_x_age(self, sample_patient_data):
        """Test calcul de SMOKING_x_AGE."""
        result = FeatureEngineer.engineer_features(sample_patient_data)

        expected = (
            sample_patient_data["SMOKING"] * sample_patient_data["AGE"]
        )
        assert result["SMOKING_x_AGE"].iloc[0] == expected

    def test_smoking_x_alcohol(self, sample_patient_data):
        """Test calcul de SMOKING_x_ALCOHOL."""
        result = FeatureEngineer.engineer_features(sample_patient_data)

        expected = bool(
            sample_patient_data["SMOKING"]
            * sample_patient_data["ALCOHOL CONSUMING"]
        )
        assert result["SMOKING_x_ALCOHOL"].iloc[0] == expected

    def test_respiratory_symptoms(self, sample_patient_data):
        """Test calcul de RESPIRATORY_SYMPTOMS."""
        result = FeatureEngineer.engineer_features(sample_patient_data)

        expected = min(
            sample_patient_data["WHEEZING"]
            + sample_patient_data["COUGHING"]
            + sample_patient_data["SHORTNESS OF BREATH"],
            3
        )
        assert result["RESPIRATORY_SYMPTOMS"].iloc[0] == expected

    def test_total_symptoms(self, sample_patient_data):
        """Test calcul de TOTAL_SYMPTOMS."""
        result = FeatureEngineer.engineer_features(sample_patient_data)

        expected = sum([
            sample_patient_data["YELLOW_FINGERS"],
            sample_patient_data["ANXIETY"],
            sample_patient_data["FATIGUE"],
            sample_patient_data["ALLERGY"],
            sample_patient_data["WHEEZING"],
            sample_patient_data["COUGHING"],
            sample_patient_data["SHORTNESS OF BREATH"],
            sample_patient_data["SWALLOWING DIFFICULTY"],
            sample_patient_data["CHEST PAIN"]
        ])
        assert result["TOTAL_SYMPTOMS"].iloc[0] == expected

    def test_behavioral_risk_score(self, sample_patient_data):
        """Test calcul de BEHAVIORAL_RISK_SCORE."""
        result = FeatureEngineer.engineer_features(sample_patient_data)

        expected = sum([
            sample_patient_data["SMOKING"],
            sample_patient_data["ALCOHOL CONSUMING"],
            sample_patient_data["PEER_PRESSURE"]
        ])
        assert result["BEHAVIORAL_RISK_SCORE"].iloc[0] == expected

    def test_severe_symptoms(self, sample_patient_data):
        """Test calcul de SEVERE_SYMPTOMS."""
        result = FeatureEngineer.engineer_features(sample_patient_data)

        expected = sum([
            sample_patient_data["CHEST PAIN"],
            sample_patient_data["SWALLOWING DIFFICULTY"],
            sample_patient_data["SHORTNESS OF BREATH"]
        ])
        assert result["SEVERE_SYMPTOMS"].iloc[0] == expected

    def test_age_group(self):
        """Test calcul de AGE_GROUP."""
        # Tester différentes tranches d'âge
        test_cases = [
            (25, 0),   # 0-50
            (50, 0),   # 0-50
            (55, 1),   # 50-60
            (60, 1),   # 50-60
            (65, 2),   # 60-70
            (70, 2),   # 60-70
            (75, 3),   # 70-100
        ]

        for age, expected_group in test_cases:
            data = {
                "AGE": age,
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

            result = FeatureEngineer.engineer_features(data)
            assert result["AGE_GROUP"].iloc[0] == expected_group

    def test_high_risk_profile(self):
        """Test calcul de HIGH_RISK_PROFILE."""
        # Cas high risk: homme + fumeur + âge > 60
        data_high_risk = {
            "AGE": 65,
            "GENDER": 1,  # Homme
            "SMOKING": 1,  # Fumeur
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

        result = FeatureEngineer.engineer_features(data_high_risk)
        assert bool(result["HIGH_RISK_PROFILE"].iloc[0]) is True

        # Cas low risk: femme
        data_low_risk = data_high_risk.copy()
        data_low_risk["GENDER"] = 0
        result = FeatureEngineer.engineer_features(data_low_risk)
        assert bool(result["HIGH_RISK_PROFILE"].iloc[0]) is False

    def test_age_squared(self, sample_patient_data):
        """Test calcul de AGE_SQUARED."""
        result = FeatureEngineer.engineer_features(sample_patient_data)

        expected = sample_patient_data["AGE"] ** 2
        assert result["AGE_SQUARED"].iloc[0] == expected

    def test_cancer_triad(self):
        """Test calcul de CANCER_TRIAD."""
        # Avec triade complète
        data_with_triad = {
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
            "COUGHING": 1,
            "SHORTNESS OF BREATH": 1,
            "SWALLOWING DIFFICULTY": 0,
            "CHEST PAIN": 1,
            "CHRONIC DISEASE": 0
        }

        result = FeatureEngineer.engineer_features(data_with_triad)
        assert bool(result["CANCER_TRIAD"].iloc[0]) is True

        # Sans triade complète
        data_without_triad = data_with_triad.copy()
        data_without_triad["COUGHING"] = 0
        result = FeatureEngineer.engineer_features(data_without_triad)
        assert bool(result["CANCER_TRIAD"].iloc[0]) is False

    def test_smoker_with_resp_symptoms(self):
        """Test calcul de SMOKER_WITH_RESP_SYMPTOMS."""
        data = {
            "AGE": 50,
            "GENDER": 0,
            "SMOKING": 1,
            "ALCOHOL CONSUMING": 0,
            "PEER_PRESSURE": 0,
            "YELLOW_FINGERS": 0,
            "ANXIETY": 0,
            "FATIGUE": 0,
            "ALLERGY": 0,
            "WHEEZING": 1,
            "COUGHING": 1,
            "SHORTNESS OF BREATH": 0,
            "SWALLOWING DIFFICULTY": 0,
            "CHEST PAIN": 0,
            "CHRONIC DISEASE": 0
        }

        result = FeatureEngineer.engineer_features(data)
        # RESPIRATORY_SYMPTOMS = 2, SMOKING = 1, donc True
        assert bool(result["SMOKER_WITH_RESP_SYMPTOMS"].iloc[0]) is True

    def test_advanced_symptoms(self):
        """Test calcul de ADVANCED_SYMPTOMS."""
        # Avec symptômes avancés
        data_with = {
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
            "SWALLOWING DIFFICULTY": 1,
            "CHEST PAIN": 1,
            "CHRONIC DISEASE": 0
        }

        result = FeatureEngineer.engineer_features(data_with)
        assert bool(result["ADVANCED_SYMPTOMS"].iloc[0]) is True

        # Sans symptômes avancés
        data_without = data_with.copy()
        data_without["SWALLOWING DIFFICULTY"] = 0
        result = FeatureEngineer.engineer_features(data_without)
        assert bool(result["ADVANCED_SYMPTOMS"].iloc[0]) is False

    def test_symptoms_per_age(self, sample_patient_data):
        """Test calcul de SYMPTOMS_PER_AGE."""
        result = FeatureEngineer.engineer_features(sample_patient_data)

        total_symptoms = result["TOTAL_SYMPTOMS"].iloc[0]
        age = sample_patient_data["AGE"]
        expected = total_symptoms / (age + 1)

        assert result["SYMPTOMS_PER_AGE"].iloc[0] == pytest.approx(expected)

    def test_resp_symptom_ratio(self, sample_patient_data):
        """Test calcul de RESP_SYMPTOM_RATIO."""
        result = FeatureEngineer.engineer_features(sample_patient_data)

        resp_symptoms = result["RESPIRATORY_SYMPTOMS"].iloc[0]
        total_symptoms = result["TOTAL_SYMPTOMS"].iloc[0]
        expected = resp_symptoms / (total_symptoms + 1)

        assert result["RESP_SYMPTOM_RATIO"].iloc[0] == pytest.approx(
            expected
        )


class TestColumnOrdering:
    """Tests pour l'ordre des colonnes."""

    def test_column_order_matches_mlmodel(self, sample_patient_data):
        """Test que l'ordre des colonnes correspond au schéma MLflow."""
        result = FeatureEngineer.engineer_features(sample_patient_data)

        expected_order = [
            # Features de base (15)
            'GENDER', 'AGE', 'SMOKING', 'YELLOW_FINGERS',
            'ANXIETY', 'PEER_PRESSURE', 'CHRONIC DISEASE',
            'FATIGUE', 'ALLERGY', 'WHEEZING',
            'ALCOHOL CONSUMING', 'COUGHING',
            'SHORTNESS OF BREATH', 'SWALLOWING DIFFICULTY',
            'CHEST PAIN',
            # Features dérivées (14)
            'SMOKING_x_AGE', 'SMOKING_x_ALCOHOL',
            'RESPIRATORY_SYMPTOMS', 'TOTAL_SYMPTOMS',
            'BEHAVIORAL_RISK_SCORE', 'SEVERE_SYMPTOMS',
            'AGE_GROUP', 'HIGH_RISK_PROFILE', 'AGE_SQUARED',
            'CANCER_TRIAD', 'SMOKER_WITH_RESP_SYMPTOMS',
            'ADVANCED_SYMPTOMS', 'SYMPTOMS_PER_AGE',
            'RESP_SYMPTOM_RATIO'
        ]

        assert list(result.columns) == expected_order

    def test_all_required_columns_present(self, sample_patient_data):
        """Test que toutes les colonnes requises sont présentes."""
        result = FeatureEngineer.engineer_features(sample_patient_data)

        # Features de base
        for col in FeatureEngineer.get_required_input_columns():
            assert col in result.columns

        # Features dérivées
        for col in FeatureEngineer.get_derived_columns():
            assert col in result.columns


class TestValidation:
    """Tests de validation des entrées."""

    def test_missing_required_column(self):
        """Test qu'une colonne manquante lève une erreur."""
        incomplete_data = {
            "AGE": 50,
            "GENDER": 1,
            # SMOKING manquant
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

        with pytest.raises(ValueError, match="Colonnes manquantes"):
            FeatureEngineer.engineer_features(incomplete_data)

    def test_multiple_missing_columns(self):
        """Test plusieurs colonnes manquantes."""
        incomplete_data = {
            "AGE": 50,
            "GENDER": 1,
            # Plusieurs colonnes manquantes
        }

        with pytest.raises(ValueError, match="Colonnes manquantes"):
            FeatureEngineer.engineer_features(incomplete_data)


class TestGetMethods:
    """Tests pour les méthodes get_*."""

    def test_get_required_input_columns(self):
        """Test get_required_input_columns retourne 15 colonnes."""
        columns = FeatureEngineer.get_required_input_columns()

        assert len(columns) == 15
        assert "AGE" in columns
        assert "GENDER" in columns
        assert "SMOKING" in columns
        assert "ALCOHOL CONSUMING" in columns

    def test_get_derived_columns(self):
        """Test get_derived_columns retourne 14 colonnes."""
        columns = FeatureEngineer.get_derived_columns()

        assert len(columns) == 14
        assert "SMOKING_x_AGE" in columns
        assert "RESPIRATORY_SYMPTOMS" in columns
        assert "AGE_GROUP" in columns
        assert "HIGH_RISK_PROFILE" in columns


class TestEdgeCases:
    """Tests de cas limites."""

    def test_all_zeros(self):
        """Test avec toutes les features à 0."""
        data = {col: 0 for col in FeatureEngineer.get_required_input_columns()}  # noqa: E501
        result = FeatureEngineer.engineer_features(data)

        assert result["TOTAL_SYMPTOMS"].iloc[0] == 0
        assert result["BEHAVIORAL_RISK_SCORE"].iloc[0] == 0
        assert result["AGE_SQUARED"].iloc[0] == 0

    def test_all_ones(self):
        """Test avec toutes les features binaires à 1."""
        data = {
            "AGE": 50,
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

        result = FeatureEngineer.engineer_features(data)

        assert result["TOTAL_SYMPTOMS"].iloc[0] == 9
        assert result["BEHAVIORAL_RISK_SCORE"].iloc[0] == 3
        assert result["RESPIRATORY_SYMPTOMS"].iloc[0] == 3  # Clippé à 3

    def test_multiple_rows(self):
        """Test avec plusieurs lignes."""
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

        result = FeatureEngineer.engineer_features(data)

        assert len(result) == 2
        assert result["AGE"].iloc[0] == 50
        assert result["AGE"].iloc[1] == 70

    def test_age_group_data_type(self, sample_patient_data):
        """Test que AGE_GROUP est de type numeric (pas categorical)."""
        result = FeatureEngineer.engineer_features(sample_patient_data)

        # Vérifier que AGE_GROUP est numeric
        assert np.issubdtype(result["AGE_GROUP"].dtype, np.number)
        # Pas categorical
        assert not pd.api.types.is_categorical_dtype(result["AGE_GROUP"])
