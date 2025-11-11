"""
Module pour le calcul des features dérivées du modèle ML.

Ce module contient les fonctions pour calculer automatiquement
les variables qui ne sont pas saisies par l'utilisateur.
"""

from typing import Union

import pandas as pd


class FeatureEngineer:
    """
    Classe pour calculer les features dérivées.

    Ces features sont calculées automatiquement à partir des données
    d'entrée et ne doivent pas être saisies par l'utilisateur.
    """

    @staticmethod
    def engineer_features(
        data: Union[pd.DataFrame, dict]
    ) -> pd.DataFrame:
        """
        Calcule toutes les features dérivées.

        Args:
            data: DataFrame ou dictionnaire contenant les features
                  de base saisies par l'utilisateur.

        Returns:
            pd.DataFrame: DataFrame avec toutes les features
                         (de base + dérivées).

        Raises:
            ValueError: Si des colonnes requises sont manquantes.
        """
        # Convertir en DataFrame si nécessaire
        if isinstance(data, dict):
            df = pd.DataFrame([data])
        else:
            df = data.copy()

        # Vérifier les colonnes requises
        required_columns = [
            'AGE', 'GENDER', 'SMOKING', 'ALCOHOL CONSUMING',
            'PEER_PRESSURE', 'YELLOW_FINGERS', 'ANXIETY',
            'FATIGUE', 'ALLERGY', 'WHEEZING', 'COUGHING',
            'SHORTNESS OF BREATH', 'SWALLOWING DIFFICULTY',
            'CHEST PAIN', 'CHRONIC DISEASE'
        ]

        missing_columns = [
            col for col in required_columns if col not in df.columns
        ]
        if missing_columns:
            raise ValueError(
                f"Colonnes manquantes : {', '.join(missing_columns)}"
            )

        # Calculer les features dérivées
        df = FeatureEngineer._add_derived_features(df)

        return df

    @staticmethod
    def _add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
        """
        Ajoute toutes les features dérivées au DataFrame.

        Args:
            df: DataFrame avec les features de base.

        Returns:
            pd.DataFrame: DataFrame avec les features dérivées ajoutées.
        """
        # Age
        df['SMOKING_x_AGE'] = df['SMOKING'] * df['AGE']

        # Combinaison tabac + alcool
        df['SMOKING_x_ALCOHOL'] = (
            df['SMOKING'] * df["ALCOHOL CONSUMING"]
        ).astype(bool)

        # Symptômes respiratoires combinés
        df['RESPIRATORY_SYMPTOMS'] = (
            df['WHEEZING'] + df['COUGHING'] + df['SHORTNESS OF BREATH']
        ).clip(0, 3)

        # Score de symptômes totaux
        df['TOTAL_SYMPTOMS'] = (
            df['YELLOW_FINGERS'] + df['ANXIETY'] +
            df['FATIGUE'] + df['ALLERGY'] + df['WHEEZING'] +
            df['COUGHING'] + df['SHORTNESS OF BREATH'] +
            df['SWALLOWING DIFFICULTY'] + df['CHEST PAIN']
        )

        # Score de facteurs de risque comportementaux
        df['BEHAVIORAL_RISK_SCORE'] = (
            df['SMOKING'] + df['ALCOHOL CONSUMING'] + df['PEER_PRESSURE']
        )

        # Score de symptômes graves
        df['SEVERE_SYMPTOMS'] = (
            df['CHEST PAIN'] + df['SWALLOWING DIFFICULTY'] +
            df['SHORTNESS OF BREATH']
        )

        # Catégories d'âge
        df['AGE_GROUP'] = pd.cut(
            df['AGE'],
            bins=[0, 50, 60, 70, 100],
            labels=['<50', '50-60', '60-70', '70+']
        )

        # Risque élevé : homme + fumeur + âge > 60
        df['HIGH_RISK_PROFILE'] = (
            (df['GENDER'] == 1) &
            (df['SMOKING'] == 1) &
            (df['AGE'] > 60)
        ).astype(bool)

        # Âge au carré (relation non-linéaire)
        df['AGE_SQUARED'] = df['AGE'] ** 2

        # Triade classique du cancer du poumon
        df['CANCER_TRIAD'] = (
            (df['COUGHING'] == 1) &
            (df['CHEST PAIN'] == 1) &
            (df['SHORTNESS OF BREATH'] == 1)
        ).astype(bool)

        # Fumeur avec symptômes respiratoires
        df['SMOKER_WITH_RESP_SYMPTOMS'] = (
            df['SMOKING'] * df['RESPIRATORY_SYMPTOMS']
        ).astype(bool)

        # Symptômes avancés (dysphagie + douleur thoracique)
        df['ADVANCED_SYMPTOMS'] = (
            df['SWALLOWING DIFFICULTY'] * df['CHEST PAIN']
        ).astype(bool)

        # Ratio symptômes / âge (normalisation)
        df['SYMPTOMS_PER_AGE'] = df['TOTAL_SYMPTOMS'] / (df['AGE'] + 1)

        # Proportion de symptômes respiratoires
        df['RESP_SYMPTOM_RATIO'] = (
            df['RESPIRATORY_SYMPTOMS'] / (df['TOTAL_SYMPTOMS'] + 1)
        )

        return df

    @staticmethod
    def get_required_input_columns() -> list:
        """
        Retourne la liste des colonnes requises en entrée.

        Returns:
            list: Liste des noms de colonnes requises.
        """
        return [
            'AGE', 'GENDER', 'SMOKING', 'ALCOHOL CONSUMING',
            'PEER_PRESSURE', 'YELLOW_FINGERS', 'ANXIETY',
            'FATIGUE', 'ALLERGY', 'WHEEZING', 'COUGHING',
            'SHORTNESS OF BREATH', 'SWALLOWING DIFFICULTY',
            'CHEST PAIN', 'CHRONIC DISEASE'
        ]

    @staticmethod
    def get_derived_columns() -> list:
        """
        Retourne la liste des colonnes dérivées calculées.

        Returns:
            list: Liste des noms de colonnes dérivées.
        """
        return [
            'SMOKING_x_AGE', 'SMOKING_x_ALCOHOL',
            'RESPIRATORY_SYMPTOMS', 'TOTAL_SYMPTOMS',
            'BEHAVIORAL_RISK_SCORE', 'SEVERE_SYMPTOMS',
            'AGE_GROUP', 'HIGH_RISK_PROFILE', 'AGE_SQUARED',
            'CANCER_TRIAD', 'SMOKER_WITH_RESP_SYMPTOMS',
            'ADVANCED_SYMPTOMS', 'SYMPTOMS_PER_AGE',
            'RESP_SYMPTOM_RATIO'
        ]
