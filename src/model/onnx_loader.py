"""Chargeur de modèle ONNX.

Ce module fournit une classe pour charger et exécuter des modèles ONNX.
Compatible avec l'interface scikit-learn pour permettre l'utilisation
dans le ModelPool existant.
"""

import logging
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


class ONNXModelLoader:
    """Chargeur et wrapper pour modèle ONNX.

    Fournit une interface compatible avec scikit-learn pour les modèles ONNX,
    permettant une utilisation transparente dans le ModelPool.
    """

    def __init__(self, model_path: Optional[str] = None):
        """Initialise le loader ONNX.

        Args:
            model_path: Chemin optionnel vers le modèle ONNX
        """
        self._session = None
        self._model_path = model_path
        self.n_features_in_ = 28  # Features attendues par le modèle
        self.classes_ = np.array([0, 1])  # Classes de classification binaire

        if model_path:
            self.load_model(model_path)

    def load_model(self, model_path: str) -> None:
        """Charge le modèle ONNX.

        Args:
            model_path: Chemin vers le fichier .onnx

        Raises:
            FileNotFoundError: Si le fichier n'existe pas
            RuntimeError: Si le chargement échoue
        """
        try:
            import onnxruntime as rt
        except ImportError as e:
            raise ImportError(
                "onnxruntime non installé. "
                "Installez avec: uv add onnxruntime"
            ) from e

        model_file = Path(model_path)
        if not model_file.exists():
            raise FileNotFoundError(f"Modèle ONNX non trouvé: {model_path}")

        try:
            # Options de session pour optimisation
            session_options = rt.SessionOptions()
            session_options.graph_optimization_level = (
                rt.GraphOptimizationLevel.ORT_ENABLE_ALL
            )

            self._session = rt.InferenceSession(
                str(model_file),
                session_options
            )
            self._model_path = model_path

            logger.info(f"Modèle ONNX chargé depuis {model_path}")

            # Récupérer les infos du modèle
            input_shape = self._session.get_inputs()[0].shape
            if len(input_shape) > 1 and input_shape[1] is not None:
                self.n_features_in_ = input_shape[1]

        except Exception as e:
            raise RuntimeError(
                f"Erreur lors du chargement du modèle ONNX: {e}"
            ) from e

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Prédiction avec le modèle ONNX.

        Args:
            X: Array de features (n_samples, n_features)

        Returns:
            Array de prédictions (n_samples,)

        Raises:
            RuntimeError: Si le modèle n'est pas chargé
        """
        if self._session is None:
            raise RuntimeError("Modèle non chargé. Appelez load_model() d'abord")

        # Convertir en float32 si nécessaire
        if X.dtype != np.float32:
            X = X.astype(np.float32)

        # Assurer la forme 2D
        if X.ndim == 1:
            X = X.reshape(1, -1)

        input_name = self._session.get_inputs()[0].name
        output_name = self._session.get_outputs()[0].name

        result = self._session.run([output_name], {input_name: X})
        predictions = result[0]

        # Flatten si nécessaire
        if predictions.ndim > 1:
            predictions = predictions.flatten()

        return predictions

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Prédiction des probabilités.

        Args:
            X: Array de features (n_samples, n_features)

        Returns:
            Array de probabilités (n_samples, n_classes)

        Raises:
            RuntimeError: Si le modèle n'est pas chargé
        """
        if self._session is None:
            raise RuntimeError("Modèle non chargé. Appelez load_model() d'abord")

        # Convertir en float32 si nécessaire
        if X.dtype != np.float32:
            X = X.astype(np.float32)

        # Assurer la forme 2D
        if X.ndim == 1:
            X = X.reshape(1, -1)

        input_name = self._session.get_inputs()[0].name

        # Le deuxième output contient les probabilités pour les modèles
        # scikit-learn convertis en ONNX
        outputs = self._session.get_outputs()
        if len(outputs) > 1:
            proba_output_name = outputs[1].name
            result = self._session.run([proba_output_name], {input_name: X})
            return result[0]
        else:
            # Fallback: utiliser predict et retourner des probas binaires
            predictions = self.predict(X)
            probas = np.zeros((len(predictions), 2))
            for i, pred in enumerate(predictions):
                if pred == 1:
                    probas[i] = [0.0, 1.0]
                else:
                    probas[i] = [1.0, 0.0]
            return probas

    def is_loaded(self) -> bool:
        """Vérifie si le modèle est chargé.

        Returns:
            True si le modèle est chargé, False sinon
        """
        return self._session is not None

    def get_model_info(self) -> dict:
        """Récupère les informations du modèle.

        Returns:
            Dictionnaire avec les informations du modèle
        """
        if not self.is_loaded():
            return {
                "loaded": False,
                "model_path": self._model_path
            }

        return {
            "loaded": True,
            "model_path": self._model_path,
            "n_features": self.n_features_in_,
            "classes": self.classes_.tolist(),
            "type": "ONNX",
            "input_name": self._session.get_inputs()[0].name,
            "output_names": [
                out.name for out in self._session.get_outputs()
            ]
        }
