"""
Module pour effectuer des prédictions avec le modèle ML.

Ce module utilise le ModelLoader pour obtenir le modèle
et effectuer des prédictions.
"""

from typing import Dict, List, Union

import numpy as np
import pandas as pd

from .feature_engineering import FeatureEngineer
from .model_loader import ModelLoader


class Predictor:
    """
    Classe pour effectuer des prédictions avec le modèle ML.

    Utilise le ModelLoader (Singleton) pour accéder au modèle.
    """

    def __init__(self):
        """Initialise le predictor avec le model loader."""
        self.model_loader = ModelLoader()
        self.feature_engineer = FeatureEngineer()

    def predict(
        self, data: Union[pd.DataFrame, Dict]
    ) -> Union[np.ndarray, List]:
        """
        Effectue une prédiction avec le modèle.

        Args:
            data: Les données d'entrée pour la prédiction.
                 Doit être un DataFrame pandas ou un dict avec
                 les features de base (sans les features dérivées).

        Returns:
            Union[np.ndarray, List]: Les prédictions du modèle.

        Raises:
            RuntimeError: Si le modèle n'est pas chargé.
            ValueError: Si les données d'entrée sont invalides.
        """
        if not self.model_loader.is_loaded():
            raise RuntimeError(
                "Le modèle n'est pas chargé. "
                "Assurez-vous que load_model() a été appelé."
            )

        try:
            # Appliquer le feature engineering
            processed_data = self.feature_engineer.engineer_features(
                data
            )

            # S'assurer que les colonnes sont dans le bon ordre
            # pour éviter les warnings sklearn
            model = self.model_loader.model
            if hasattr(model, 'feature_names_in_'):
                # Réordonner les colonnes selon l'ordre du modèle
                processed_data = processed_data[model.feature_names_in_]

            # Configurer le pipeline pour conserver les DataFrames
            # et éviter les warnings de feature names
            if hasattr(model, 'set_output'):
                model.set_output(transform="pandas")

            # Effectuer la prédiction
            predictions = model.predict(processed_data)

            return predictions

        except Exception as e:
            raise ValueError(
                f"Erreur lors de la prédiction : {str(e)}"
            ) from e

    def predict_proba(
        self, data: Union[pd.DataFrame, Dict]
    ) -> Union[np.ndarray, List]:
        """
        Effectue une prédiction de probabilités avec le modèle.

        Args:
            data: Les données d'entrée pour la prédiction.
                 Doit être un DataFrame pandas ou un dict avec
                 les features de base (sans les features dérivées).

        Returns:
            Union[np.ndarray, List]: Les probabilités prédites.

        Raises:
            RuntimeError: Si le modèle n'est pas chargé.
            ValueError: Si les données d'entrée sont invalides.
            AttributeError: Si le modèle ne supporte pas predict_proba.
        """
        if not self.model_loader.is_loaded():
            raise RuntimeError(
                "Le modèle n'est pas chargé. "
                "Assurez-vous que load_model() a été appelé."
            )

        model = self.model_loader.model

        if not hasattr(model, "predict_proba"):
            raise AttributeError(
                "Le modèle ne supporte pas predict_proba"
            )

        try:
            # Appliquer le feature engineering
            processed_data = self.feature_engineer.engineer_features(
                data
            )

            # S'assurer que les colonnes sont dans le bon ordre
            # pour éviter les warnings sklearn
            if hasattr(model, 'feature_names_in_'):
                # Réordonner les colonnes selon l'ordre du modèle
                processed_data = processed_data[model.feature_names_in_]

            # Configurer le pipeline pour conserver les DataFrames
            # et éviter les warnings de feature names
            if hasattr(model, 'set_output'):
                model.set_output(transform="pandas")

            # Effectuer la prédiction de probabilités
            probabilities = model.predict_proba(processed_data)

            return probabilities

        except Exception as e:
            raise ValueError(
                f"Erreur lors de la prédiction de probabilités : {str(e)}"
            ) from e

    def get_required_features(self) -> List[str]:
        """
        Retourne la liste des features requises en entrée.

        Returns:
            List[str]: Liste des noms de features requises.
        """
        return self.feature_engineer.get_required_input_columns()
