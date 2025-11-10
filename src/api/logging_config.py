"""
Configuration du logging avec Redis.

Ce module configure le logger Python standard avec un handler personnalisé
pour stocker les logs dans Redis.
"""

import logging
from typing import Optional

import redis

from ..config import settings


class RedisHandler(logging.Handler):
    """
    Handler personnalisé pour stocker les logs dans Redis.
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        key: str,
        max_length: int = 1000
    ):
        """
        Initialise le handler Redis.

        Args:
            redis_client: Client Redis
            key: Clé Redis pour stocker les logs
            max_length: Nombre maximum de logs à conserver
        """
        super().__init__()
        self.redis_client = redis_client
        self.key = key
        self.max_length = max_length

    def emit(self, record: logging.LogRecord) -> None:
        """
        Émet un log vers Redis.

        Args:
            record: Enregistrement de log
        """
        try:
            log_entry = self.format(record)
            self.redis_client.lpush(self.key, log_entry)
            self.redis_client.ltrim(self.key, 0, self.max_length - 1)
        except Exception:
            self.handleError(record)


def setup_logging(
    log_level: Optional[str] = None,
    redis_client: Optional[redis.Redis] = None
) -> logging.Logger:
    """
    Configure le logger avec handler stdout ou redis.

    Args:
        log_level: Niveau de log (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                  Si None, utilise settings.LOG_LEVEL.
        redis_client: Client Redis existant. Si None, en crée un nouveau.

    Returns:
        logging.Logger: Logger configuré.
    """
    # Créer ou récupérer le logger
    logger = logging.getLogger("api")

    # Éviter d'ajouter plusieurs handlers
    if logger.handlers:
        return logger

    # Définir le niveau de log
    level = log_level or settings.LOG_LEVEL
    logger.setLevel(getattr(logging, level.upper()))

    # Format des logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Déterminer le handler à utiliser selon la configuration
    handler_type = settings.LOGGING_HANDLER.lower()

    if handler_type == "redis":
        # Mode Redis : console + redis
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, level.upper()))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Handler Redis
        try:
            if redis_client is None:
                redis_client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    decode_responses=True
                )
                # Tester la connexion
                redis_client.ping()

            # Créer le handler Redis personnalisé
            redis_handler = RedisHandler(
                redis_client=redis_client,
                key=settings.REDIS_LOGS_KEY,
                max_length=settings.REDIS_LOGS_MAX_SIZE
            )
            redis_handler.setLevel(getattr(logging, level.upper()))
            redis_handler.setFormatter(formatter)
            logger.addHandler(redis_handler)

            logger.info(
                f"Logging configuré: redis "
                f"({settings.REDIS_HOST}:{settings.REDIS_PORT})"
            )

        except redis.ConnectionError as e:
            logger.warning(
                f"Impossible de se connecter à Redis : {str(e)}. "
                f"Utilisation du mode stdout uniquement."
            )
        except Exception as e:
            logger.warning(
                f"Erreur lors de la configuration du handler Redis : "
                f"{str(e)}. Utilisation du mode stdout uniquement."
            )

    else:
        # Mode stdout : console uniquement
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, level.upper()))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        logger.info(f"Logging configuré: stdout (level={level})")

    return logger


def get_logger() -> logging.Logger:
    """
    Retourne le logger configuré.

    Returns:
        logging.Logger: Logger de l'API.
    """
    return logging.getLogger("api")


def get_redis_logs(
    limit: int = 100,
    redis_client: Optional[redis.Redis] = None
) -> list:
    """
    Récupère les logs depuis Redis.

    Args:
        limit: Nombre maximum de logs à récupérer.
        redis_client: Client Redis. Si None, en crée un nouveau.

    Returns:
        list: Liste des logs au format string.
    """
    if redis_client is None:
        try:
            redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True
            )
            redis_client.ping()
        except redis.ConnectionError:
            return []

    try:
        logs = redis_client.lrange(
            settings.REDIS_LOGS_KEY,
            0,
            limit - 1
        )
        return logs
    except Exception:
        return []


def clear_redis_logs(
    redis_client: Optional[redis.Redis] = None
) -> bool:
    """
    Supprime tous les logs de Redis.

    Args:
        redis_client: Client Redis. Si None, en crée un nouveau.

    Returns:
        bool: True si succès, False sinon.
    """
    if redis_client is None:
        try:
            redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True
            )
            redis_client.ping()
        except redis.ConnectionError:
            return False

    try:
        redis_client.delete(settings.REDIS_LOGS_KEY)
        return True
    except Exception:
        return False


def is_redis_connected(
    redis_client: Optional[redis.Redis] = None
) -> bool:
    """
    Vérifie si Redis est connecté.

    Args:
        redis_client: Client Redis. Si None, en crée un nouveau.

    Returns:
        bool: True si connecté, False sinon.
    """
    if redis_client is None:
        try:
            redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True
            )
        except Exception:
            return False

    try:
        redis_client.ping()
        return True
    except redis.ConnectionError:
        return False
