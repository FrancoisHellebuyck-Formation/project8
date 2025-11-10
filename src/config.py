"""
Module de configuration pour charger les variables d'environnement.

Ce module utilise python-dotenv pour charger les variables depuis .env
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Settings:
    """Classe pour gérer les paramètres de configuration."""

    # Configuration du modèle ML
    MODEL_PATH: str = os.getenv("MODEL_PATH", "./model/model.pkl")

    # Configuration de l'API FastAPI
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))

    # Configuration Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_LOGS_KEY: str = os.getenv("REDIS_LOGS_KEY", "api_logs")
    REDIS_LOGS_MAX_SIZE: int = int(
        os.getenv("REDIS_LOGS_MAX_SIZE", "1000")
    )

    # Configuration Gradio
    GRADIO_HOST: str = os.getenv("GRADIO_HOST", "0.0.0.0")
    GRADIO_PORT: int = int(os.getenv("GRADIO_PORT", "7860"))
    API_URL: str = os.getenv("API_URL", "http://localhost:8000")

    # Environnement
    ENV: str = os.getenv("ENV", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOGGING_HANDLER: str = os.getenv("LOGGING_HANDLER", "stdout")
    UI_LOG_LEVEL: str = os.getenv("UI_LOG_LEVEL", "INFO")


# Instance globale des settings
settings = Settings()
