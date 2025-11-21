"""
Client proxy pour l'API FastAPI.

Ce module fournit une classe client qui encapsule tous les appels
à l'API FastAPI et gère les erreurs de manière uniforme.
"""

import logging
from typing import Dict, List, Optional, Tuple

import requests
from requests.exceptions import RequestException, Timeout

from src.config import settings

logger = logging.getLogger(__name__)


class APIProxyClient:
    """Client proxy pour communiquer avec l'API FastAPI."""

    def __init__(self, api_url: Optional[str] = None):
        """
        Initialise le client proxy.

        Args:
            api_url: URL de l'API FastAPI (défaut: settings.API_URL)
        """
        self.api_url = api_url or settings.API_URL
        self.timeout = 30  # Timeout par défaut de 30 secondes

    def _handle_response(
        self,
        response: requests.Response
    ) -> Tuple[Dict, int]:
        """
        Gère la réponse HTTP de manière uniforme.

        Args:
            response: Objet Response de requests

        Returns:
            Tuple (response_json, status_code)
        """
        try:
            return response.json(), response.status_code
        except ValueError:
            return {
                "error": "Réponse invalide du serveur",
                "status_code": response.status_code
            }, response.status_code

    def _handle_error(self, error: Exception) -> Tuple[Dict, int]:
        """
        Gère les erreurs de requête de manière uniforme.

        Args:
            error: Exception levée

        Returns:
            Tuple (error_dict, status_code)
        """
        if isinstance(error, Timeout):
            logger.error(f"Timeout lors de la requête: {error}")
            return {"error": "Timeout: L'API ne répond pas"}, 504
        elif isinstance(error, RequestException):
            logger.error(f"Erreur de connexion: {error}")
            return {"error": f"Erreur de connexion: {str(error)}"}, 503
        else:
            logger.error(f"Erreur inattendue: {error}")
            return {"error": f"Erreur inattendue: {str(error)}"}, 500

    # ==================== ROOT ====================

    def get_root(self) -> Tuple[Dict, int]:
        """
        Appelle l'endpoint racine GET /.

        Returns:
            Tuple (response_json, status_code)
        """
        try:
            response = requests.get(
                f"{self.api_url}/",
                timeout=self.timeout
            )
            return self._handle_response(response)
        except Exception as e:
            return self._handle_error(e)

    # ==================== HEALTH ====================

    def get_health(self) -> Tuple[Dict, int]:
        """
        Appelle l'endpoint GET /health.

        Returns:
            Tuple (response_json, status_code)
        """
        try:
            response = requests.get(
                f"{self.api_url}/health",
                timeout=self.timeout
            )
            return self._handle_response(response)
        except Exception as e:
            return self._handle_error(e)

    # ==================== PREDICT ====================

    def post_predict(self, patient_data: Dict) -> Tuple[Dict, int]:
        """
        Appelle l'endpoint POST /predict.

        Args:
            patient_data: Dictionnaire avec les 14 features du patient

        Returns:
            Tuple (response_json, status_code)
        """
        try:
            response = requests.post(
                f"{self.api_url}/predict",
                json=patient_data,
                timeout=self.timeout
            )
            return self._handle_response(response)
        except Exception as e:
            return self._handle_error(e)

    def post_predict_proba(self, patient_data: Dict) -> Tuple[Dict, int]:
        """
        Appelle l'endpoint POST /predict_proba.

        Args:
            patient_data: Dictionnaire avec les 14 features du patient

        Returns:
            Tuple (response_json, status_code)
        """
        try:
            response = requests.post(
                f"{self.api_url}/predict_proba",
                json=patient_data,
                timeout=self.timeout
            )
            return self._handle_response(response)
        except Exception as e:
            return self._handle_error(e)

    # ==================== LOGS ====================

    def get_logs(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[Dict, int]:
        """
        Appelle l'endpoint GET /logs.

        Args:
            limit: Nombre de logs à récupérer (max: 1000)
            offset: Nombre de logs à sauter (pagination)

        Returns:
            Tuple (response_json, status_code)
        """
        try:
            response = requests.get(
                f"{self.api_url}/logs",
                params={"limit": limit, "offset": offset},
                timeout=self.timeout
            )
            return self._handle_response(response)
        except Exception as e:
            return self._handle_error(e)

    def delete_logs(self) -> Tuple[Dict, int]:
        """
        Appelle l'endpoint DELETE /logs.

        Returns:
            Tuple (response_json, status_code)
        """
        try:
            response = requests.delete(
                f"{self.api_url}/logs",
                timeout=self.timeout
            )
            return self._handle_response(response)
        except Exception as e:
            return self._handle_error(e)

    # ==================== BATCH OPERATIONS ====================

    def batch_predict(
        self,
        patients_data: List[Dict]
    ) -> List[Tuple[Dict, int]]:
        """
        Effectue des prédictions en batch.

        Args:
            patients_data: Liste de dictionnaires de patients

        Returns:
            Liste de tuples (response_json, status_code)
        """
        results = []
        for patient_data in patients_data:
            result = self.post_predict(patient_data)
            results.append(result)
        return results

    # ==================== UTILITY ====================

    def check_connection(self) -> bool:
        """
        Vérifie la connexion à l'API.

        Returns:
            bool: True si l'API est accessible, False sinon
        """
        try:
            response = requests.get(
                f"{self.api_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False

    def get_api_info(self) -> Tuple[Dict, int]:
        """
        Récupère les informations de l'API.

        Returns:
            Tuple (response_json, status_code)
        """
        return self.get_root()
