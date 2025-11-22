"""
Tests unitaires pour le module logging_config de l'API.

Ce module teste:
- setup_logging()
- is_redis_connected()
- get_redis_logs()
- clear_redis_logs()
"""

import logging
from unittest.mock import MagicMock, patch

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
        mock_redis_instance.llen.return_value = 3
        mock_redis_instance.ping.return_value = True
        mock_redis.return_value = mock_redis_instance

        result = get_redis_logs(limit=10)

        assert isinstance(result, dict)
        assert len(result['logs']) == 3
        assert result['logs'][0] == "log1"
        assert result['logs'][1] == "log2"
        assert result['total'] == 3
        assert result['offset'] == 0
        assert result['limit'] == 10
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
        mock_redis_instance.llen.return_value = 2
        mock_redis_instance.ping.return_value = True
        mock_redis.return_value = mock_redis_instance

        result = get_redis_logs(limit=2)

        assert isinstance(result, dict)
        assert len(result['logs']) == 2
        assert result['limit'] == 2

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

        assert result == {"logs": [], "total": 0, "offset": 0, "limit": 10}


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
        mock_redis_instance.llen.return_value = 0
        mock_redis.return_value = mock_redis_instance

        result = get_redis_logs(limit=0)

        assert result == {"logs": [], "total": 0, "offset": 0, "limit": 0}

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
        mock_redis_instance.llen.return_value = 1
        mock_redis_instance.ping.return_value = True
        mock_redis.return_value = mock_redis_instance

        result = get_redis_logs(limit=10)

        assert isinstance(result, dict)
        assert len(result['logs']) == 1
        assert isinstance(result['logs'][0], str)


class TestRedisHandler:
    """Tests pour le RedisHandler."""

    def test_redis_handler_init(self):
        """Test initialisation du RedisHandler."""
        from src.api.logging_config import RedisHandler

        mock_redis = MagicMock()
        handler = RedisHandler(
            redis_client=mock_redis,
            key="test_logs",
            max_length=100
        )

        assert handler.redis_client is mock_redis
        assert handler.key == "test_logs"
        assert handler.max_length == 100

    def test_redis_handler_emit(self):
        """Test émission d'un log."""
        from src.api.logging_config import RedisHandler
        import logging

        mock_redis = MagicMock()
        handler = RedisHandler(
            redis_client=mock_redis,
            key="test_logs",
            max_length=100
        )

        # Créer un formatter
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)

        # Créer un record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )

        # Émettre le log
        handler.emit(record)

        # Vérifier les appels Redis
        mock_redis.lpush.assert_called_once()
        mock_redis.ltrim.assert_called_once_with("test_logs", 0, 99)

    def test_redis_handler_emit_error(self):
        """Test gestion d'erreur lors de l'émission."""
        from src.api.logging_config import RedisHandler
        import logging

        mock_redis = MagicMock()
        mock_redis.lpush.side_effect = Exception("Redis error")

        handler = RedisHandler(
            redis_client=mock_redis,
            key="test_logs",
            max_length=100
        )

        # Mock handleError pour éviter les sorties stderr
        handler.handleError = MagicMock()

        # Créer un record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )

        # Émettre le log (ne devrait pas lever d'exception)
        handler.emit(record)

        # Vérifier que handleError a été appelé
        handler.handleError.assert_called_once_with(record)


class TestSetupLoggingExtended:
    """Tests étendus pour setup_logging."""

    @patch('src.config.settings')
    def test_setup_logging_with_custom_level(self, mock_settings):
        """Test avec niveau de log personnalisé."""
        mock_settings.LOG_LEVEL = "DEBUG"
        mock_settings.LOGGING_HANDLER = "stdout"

        # Réinitialiser le logger pour ce test
        logger = logging.getLogger("api")
        logger.handlers = []

        logger = setup_logging(log_level="WARNING")

        assert logger.level == logging.WARNING

    @patch('src.config.settings')
    def test_setup_logging_prevents_duplicate_handlers(self, mock_settings):
        """Test que setup_logging n'ajoute pas de handlers en double."""
        mock_settings.LOG_LEVEL = "INFO"
        mock_settings.LOGGING_HANDLER = "stdout"

        # Premier appel
        logger1 = setup_logging()
        handlers_count1 = len(logger1.handlers)

        # Deuxième appel
        logger2 = setup_logging()
        handlers_count2 = len(logger2.handlers)

        # Devrait retourner le même logger sans ajouter de handlers
        assert logger1 is logger2
        assert handlers_count1 == handlers_count2

    @patch('src.config.settings')
    @patch('src.api.logging_config.redis.Redis')
    def test_setup_logging_redis_with_custom_client(
        self,
        mock_redis,
        mock_settings
    ):
        """Test avec client Redis personnalisé."""
        mock_settings.LOG_LEVEL = "INFO"
        mock_settings.LOGGING_HANDLER = "redis"
        mock_settings.REDIS_LOGS_KEY = "custom_logs"
        mock_settings.REDIS_LOGS_MAX_SIZE = 500

        custom_redis = MagicMock()
        custom_redis.ping.return_value = True

        # Réinitialiser le logger pour ce test
        import logging
        logger = logging.getLogger("api")
        logger.handlers = []

        logger = setup_logging(redis_client=custom_redis)

        assert logger is not None


class TestGetRedisLogsExtended:
    """Tests étendus pour get_redis_logs."""

    @patch('src.config.settings')
    @patch('src.api.logging_config.redis.Redis')
    def test_get_redis_logs_with_offset(self, mock_redis, mock_settings):
        """Test récupération avec offset."""
        mock_settings.REDIS_HOST = "localhost"
        mock_settings.REDIS_PORT = 6379
        mock_settings.REDIS_DB = 0
        mock_settings.REDIS_LOGS_KEY = "api_logs"

        mock_redis_instance = MagicMock()
        mock_logs = ["log3", "log4"]
        mock_redis_instance.lrange.return_value = mock_logs
        mock_redis_instance.llen.return_value = 10
        mock_redis_instance.ping.return_value = True
        mock_redis.return_value = mock_redis_instance

        result = get_redis_logs(limit=2, offset=2)

        assert len(result['logs']) == 2
        assert result['offset'] == 2
        assert result['total'] == 10
        # Vérifier que lrange a été appelé avec les bons paramètres
        mock_redis_instance.lrange.assert_called_once_with(
            "api_logs",
            2,
            3  # offset + limit - 1
        )
