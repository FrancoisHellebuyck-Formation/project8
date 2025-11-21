"""
Tests pour le package proxy.
"""

import pytest
from unittest.mock import Mock, patch

from src.proxy.client import APIProxyClient


class TestAPIProxyClient:
    """Tests pour la classe APIProxyClient."""

    @pytest.fixture
    def client(self):
        """Fixture pour créer un client proxy."""
        return APIProxyClient(api_url="http://localhost:8000")

    def test_init(self, client):
        """Test l'initialisation du client."""
        assert client.api_url == "http://localhost:8000"
        assert client.timeout == 30

    def test_init_default_url(self):
        """Test l'initialisation avec l'URL par défaut."""
        with patch('src.proxy.client.settings') as mock_settings:
            mock_settings.API_URL = "http://default:8000"
            client = APIProxyClient()
            assert client.api_url == "http://default:8000"

    @patch('src.proxy.client.requests.get')
    def test_get_root_success(self, mock_get, client):
        """Test GET / avec succès."""
        mock_response = Mock()
        mock_response.json.return_value = {"message": "API"}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result, status = client.get_root()

        assert result == {"message": "API"}
        assert status == 200
        mock_get.assert_called_once_with(
            "http://localhost:8000/",
            timeout=30
        )

    @patch('src.proxy.client.requests.get')
    def test_get_health_success(self, mock_get, client):
        """Test GET /health avec succès."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "healthy",
            "model_loaded": True
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result, status = client.get_health()

        assert result["status"] == "healthy"
        assert result["model_loaded"] is True
        assert status == 200

    @patch('src.proxy.client.requests.post')
    def test_post_predict_success(self, mock_post, client):
        """Test POST /predict avec succès."""
        patient_data = {
            "AGE": 50,
            "GENDER": 1,
            "SMOKING": 1
        }
        mock_response = Mock()
        mock_response.json.return_value = {
            "prediction": 1,
            "probability": 0.85
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result, status = client.post_predict(patient_data)

        assert result["prediction"] == 1
        assert result["probability"] == 0.85
        assert status == 200
        mock_post.assert_called_once_with(
            "http://localhost:8000/predict",
            json=patient_data,
            timeout=30
        )

    @patch('src.proxy.client.requests.post')
    def test_post_predict_proba_success(self, mock_post, client):
        """Test POST /predict_proba avec succès."""
        patient_data = {"AGE": 50, "GENDER": 1}
        mock_response = Mock()
        mock_response.json.return_value = {
            "probabilities": [0.15, 0.85]
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result, status = client.post_predict_proba(patient_data)

        assert "probabilities" in result
        assert status == 200

    @patch('src.proxy.client.requests.get')
    def test_get_logs_success(self, mock_get, client):
        """Test GET /logs avec succès."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "total": 10,
            "logs": []
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result, status = client.get_logs(limit=50, offset=10)

        assert result["total"] == 10
        assert status == 200
        mock_get.assert_called_once_with(
            "http://localhost:8000/logs",
            params={"limit": 50, "offset": 10},
            timeout=30
        )

    @patch('src.proxy.client.requests.delete')
    def test_delete_logs_success(self, mock_delete, client):
        """Test DELETE /logs avec succès."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "message": "Logs supprimés avec succès"
        }
        mock_response.status_code = 200
        mock_delete.return_value = mock_response

        result, status = client.delete_logs()

        assert "message" in result
        assert status == 200

    @patch('src.proxy.client.requests.get')
    def test_handle_timeout(self, mock_get, client):
        """Test la gestion du timeout."""
        from requests.exceptions import Timeout
        mock_get.side_effect = Timeout("Connection timeout")

        result, status = client.get_health()

        assert "error" in result
        assert "Timeout" in result["error"]
        assert status == 504

    @patch('src.proxy.client.requests.get')
    def test_handle_connection_error(self, mock_get, client):
        """Test la gestion des erreurs de connexion."""
        from requests.exceptions import ConnectionError
        mock_get.side_effect = ConnectionError("Connection failed")

        result, status = client.get_health()

        assert "error" in result
        assert status == 503

    @patch('src.proxy.client.requests.get')
    def test_handle_invalid_json(self, mock_get, client):
        """Test la gestion des réponses JSON invalides."""
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result, status = client.get_health()

        assert "error" in result
        assert "Réponse invalide" in result["error"]
        assert status == 200

    @patch('src.proxy.client.requests.get')
    def test_check_connection_success(self, mock_get, client):
        """Test la vérification de connexion avec succès."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        is_connected = client.check_connection()

        assert is_connected is True

    @patch('src.proxy.client.requests.get')
    def test_check_connection_failure(self, mock_get, client):
        """Test la vérification de connexion en échec."""
        from requests.exceptions import ConnectionError
        mock_get.side_effect = ConnectionError("Connection failed")

        is_connected = client.check_connection()

        assert is_connected is False

    def test_batch_predict(self, client):
        """Test les prédictions en batch."""
        patients_data = [
            {"AGE": 50, "GENDER": 1},
            {"AGE": 60, "GENDER": 2}
        ]

        with patch.object(client, 'post_predict') as mock_predict:
            mock_predict.return_value = ({"prediction": 1}, 200)

            results = client.batch_predict(patients_data)

            assert len(results) == 2
            assert mock_predict.call_count == 2

    @patch('src.proxy.client.requests.get')
    def test_get_api_info(self, mock_get, client):
        """Test la récupération des infos de l'API."""
        mock_response = Mock()
        mock_response.json.return_value = {"version": "1.0.0"}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result, status = client.get_api_info()

        assert result["version"] == "1.0.0"
        assert status == 200
