"""
Package API pour l'application FastAPI.

Ce package contient l'API REST pour effectuer des prédictions
avec le modèle ML et consulter les logs.
"""

from .logging_config import setup_logging
from .main import app
from .schemas import (
    HealthResponse,
    LogsResponse,
    PatientData,
    PredictionProbabilityResponse,
    PredictionResponse,
)

__all__ = [
    "app",
    "setup_logging",
    "PatientData",
    "PredictionResponse",
    "PredictionProbabilityResponse",
    "HealthResponse",
    "LogsResponse",
]
