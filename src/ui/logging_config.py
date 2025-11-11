"""
Configuration du logging pour l'interface Gradio.

Ce module configure un logger spécifique pour l'UI.
"""

import logging
import sys


def setup_ui_logger(
    log_level: str = "INFO",
    logger_name: str = "ui"
) -> logging.Logger:
    """
    Configure le logger pour l'interface utilisateur.

    Args:
        log_level: Niveau de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        logger_name: Nom du logger

    Returns:
        logging.Logger: Logger configuré pour l'UI
    """
    logger = logging.getLogger(logger_name)

    # Éviter d'ajouter plusieurs handlers
    if logger.handlers:
        return logger

    # Définir le niveau de log
    logger.setLevel(getattr(logging, log_level.upper()))

    # Handler console (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))

    # Format des logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    return logger


def get_ui_logger() -> logging.Logger:
    """
    Retourne le logger UI configuré.

    Returns:
        logging.Logger: Logger de l'UI
    """
    return logging.getLogger("ui")
