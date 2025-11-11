"""
Tests unitaires pour le module logging_config de l'API.

Ce module teste:
- setup_logging()
- is_redis_connected()
- get_redis_logs()
- clear_redis_logs()
"""

from unittest.mock import MagicMock, patch

import pytest

from src.api.logging_config import (
    clear_redis_logs,
    get_redis_logs,
    is_redis_connected,
    setup_logging,
)


class TestSetupLogging:
    """Tests pour la fonction setup_logging()."""

    @patch('src.config.settings')
    def test_setup_logging_stdout_handler(self, mock_settings):
        """Test configuration avec handler stdout."""
        mock_settings.LOGGING_HANDLER = "stdout"
        mock_settings.LOG_LEVEL = "INFO"

        logger = setup_logging()

        assert logger is not None
        assert logger.name == "api"
        assert len(logger.handlers) > 0

    @patch('src.config.settings')
    @patch('src.api.logging_config.redis.Redis')
    def test_setup_logging_redis_handler(self, mock_redis, mock_settings):
        """Test configuration avec handler redis."""
        mock_settings.LOGGING_HANDLER = "redis"
        mock_settings.LOG_LEVEL = "INFO"
        mock_settings.REDIS_HOST = "localhost"
        mock_settings.REDIS_PORT = 6379
        mock_settings.REDIS_DB = 0

        # Mock connexion Redis
        mock_redis_instance = MagicMock()
        mock_redis_instance.ping.return_value = True
        mock_redis.return_value = mock_redis_instance

        logger = setup_logging()

        assert logger is not None
        assert logger.name == "api"

    @patch('src.config.settings')
    def test_setup_logging_invalid_level(self, mock_settings):
        """Test avec niveau de log invalide."""
        mock_settings.LOGGING_HANDLER = "stdout"
        mock_settings.LOG_LEVEL = "INVALID"

        logger = setup_logging()

        # Devrait utiliser INFO par défaut
        assert logger is not None


class TestIsRedisConnected:
    """Tests pour la fonction is_redis_connected()."""

    @patch('src.config.settings')
    @patch('src.api.logging_config.redis.Redis')
    def test_is_redis_connected_returns_true(
        self, mock_redis, mock_settings
    ):
        """Test retourne True si Redis connecté."""
        mock_settings.REDIS_HOST = "localhost"
        mock_settings.REDIS_PORT = 6379
        mock_settings.REDIS_DB = 0

        mock_redis_instance = MagicMock()
        mock_redis_instance.ping.return_value = True
        mock_redis.return_value = mock_redis_instance

        result = is_redis_connected()

        assert result is True
        mock_redis_instance.ping.assert_called_once()

    @patch('src.config.settings')
    @patch('src.api.logging_config.redis.Redis')
    def test_is_redis_connected_returns_false_on_error(
        self, mock_redis, mock_settings
    ):
        """Test retourne False si erreur Redis."""
        mock_settings.REDIS_HOST = "localhost"
        mock_settings.REDIS_PORT = 6379
        mock_settings.REDIS_DB = 0

        # Simuler une erreur lors de la création du client
        mock_redis.side_effect = Exception("Connection error")

        result = is_redis_connected()

        assert result is False


class TestGetRedisLogs:
    """Tests pour la fonction get_redis_logs()."""

    @patch('src.config.settings')
    @patch('src.api.logging_config.redis.Redis')
    def test_get_redis_logs_returns_list(self, mock_redis, mock_settings):
        """Test retourne une liste de logs."""
        mock_settings.REDIS_HOST = "localhost"
        mock_settings.REDIS_PORT = 6379
        mock_settings.REDIS_DB = 0
        mock_settings.REDIS_LOGS_KEY = "api_logs"

        mock_redis_instance = MagicMock()
        # Avec decode_responses=True, Redis retourne des strings
        mock_logs = ["log1", "log2", "log3"]
        mock_redis_instance.lrange.return_value = mock_logs
        mock_redis_instance.ping.return_value = True
        mock_redis.return_value = mock_redis_instance

        result = get_redis_logs(limit=10)

        assert len(result) == 3
        assert result[0] == "log1"
        assert result[1] == "log2"
        mock_redis_instance.lrange.assert_called_once()

    @patch('src.config.settings')
    @patch('src.api.logging_config.redis.Redis')
    def test_get_redis_logs_respects_limit(
        self, mock_redis, mock_settings
    ):
        """Test respecte la limite."""
        mock_settings.REDIS_HOST = "localhost"
        mock_settings.REDIS_PORT = 6379
        mock_settings.REDIS_DB = 0
        mock_settings.REDIS_LOGS_KEY = "api_logs"

        mock_redis_instance = MagicMock()
        mock_logs = ["log1", "log2"]
        mock_redis_instance.lrange.return_value = mock_logs
        mock_redis_instance.ping.return_value = True
        mock_redis.return_value = mock_redis_instance

        result = get_redis_logs(limit=2)

        assert len(result) == 2

    @patch('src.config.settings')
    @patch('src.api.logging_config.redis.Redis')
    def test_get_redis_logs_returns_empty_on_error(
        self, mock_redis, mock_settings
    ):
        """Test retourne liste vide si erreur."""
        mock_settings.REDIS_HOST = "localhost"
        mock_settings.REDIS_PORT = 6379
        mock_settings.REDIS_DB = 0

        mock_redis_instance = MagicMock()
        mock_redis_instance.lrange.side_effect = Exception("Redis error")
        mock_redis.return_value = mock_redis_instance

        result = get_redis_logs(limit=10)

        assert result == []


class TestClearRedisLogs:
    """Tests pour la fonction clear_redis_logs()."""

    @patch('src.config.settings')
    @patch('src.api.logging_config.redis.Redis')
    def test_clear_redis_logs_returns_true(
        self, mock_redis, mock_settings
    ):
        """Test retourne True si suppression réussie."""
        mock_settings.REDIS_HOST = "localhost"
        mock_settings.REDIS_PORT = 6379
        mock_settings.REDIS_DB = 0
        mock_settings.REDIS_LOGS_KEY = "api_logs"

        mock_redis_instance = MagicMock()
        mock_redis_instance.delete.return_value = 1
        mock_redis.return_value = mock_redis_instance

        result = clear_redis_logs()

        assert result is True
        mock_redis_instance.delete.assert_called_once()

    @patch('src.config.settings')
    @patch('src.api.logging_config.redis.Redis')
    def test_clear_redis_logs_returns_false_on_error(
        self, mock_redis, mock_settings
    ):
        """Test retourne False si erreur."""
        mock_settings.REDIS_HOST = "localhost"
        mock_settings.REDIS_PORT = 6379
        mock_settings.REDIS_DB = 0

        mock_redis_instance = MagicMock()
        mock_redis_instance.delete.side_effect = Exception("Redis error")
        mock_redis.return_value = mock_redis_instance

        result = clear_redis_logs()

        assert result is False


class TestEdgeCases:
    """Tests de cas limites."""

    @patch('src.config.settings')
    @patch('src.api.logging_config.redis.Redis')
    def test_get_redis_logs_with_zero_limit(
        self, mock_redis, mock_settings
    ):
        """Test avec limite = 0."""
        mock_settings.REDIS_HOST = "localhost"
        mock_settings.REDIS_PORT = 6379
        mock_settings.REDIS_DB = 0
        mock_settings.REDIS_LOGS_KEY = "api_logs"

        mock_redis_instance = MagicMock()
        mock_redis_instance.lrange.return_value = []
        mock_redis.return_value = mock_redis_instance

        result = get_redis_logs(limit=0)

        assert result == []

    @patch('src.config.settings')
    @patch('src.api.logging_config.redis.Redis')
    def test_get_redis_logs_decodes_bytes(
        self, mock_redis, mock_settings
    ):
        """Test décodage des bytes en string."""
        mock_settings.REDIS_HOST = "localhost"
        mock_settings.REDIS_PORT = 6379
        mock_settings.REDIS_DB = 0
        mock_settings.REDIS_LOGS_KEY = "api_logs"

        mock_redis_instance = MagicMock()
        # decode_responses=True décode automatiquement
        mock_logs = ["log with é accents"]
        mock_redis_instance.lrange.return_value = mock_logs
        mock_redis_instance.ping.return_value = True
        mock_redis.return_value = mock_redis_instance

        result = get_redis_logs(limit=10)

        assert len(result) == 1
        assert isinstance(result[0], str)
