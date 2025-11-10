"""
Schémas Pydantic pour l'API.

Ce module contient les modèles de données pour la validation
des requêtes et réponses de l'API.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class PatientData(BaseModel):
    """Modèle pour les données d'un patient."""

    AGE: int = Field(..., ge=0, le=120, description="Âge du patient")
    GENDER: int = Field(..., ge=0, le=1, description="Genre (0=F, 1=M)")
    SMOKING: int = Field(
        ..., ge=0, le=1, description="Fumeur (0=Non, 1=Oui)"
    )
    ALCOHOL_CONSUMING: int = Field(
        ...,
        ge=0,
        le=1,
        description="Consommation d'alcool (0=Non, 1=Oui)",
        alias="ALCOHOL CONSUMING"
    )
    PEER_PRESSURE: int = Field(
        ..., ge=0, le=1, description="Pression sociale (0=Non, 1=Oui)"
    )
    YELLOW_FINGERS: int = Field(
        ..., ge=0, le=1, description="Doigts jaunes (0=Non, 1=Oui)"
    )
    ANXIETY: int = Field(
        ..., ge=0, le=1, description="Anxiété (0=Non, 1=Oui)"
    )
    FATIGUE: int = Field(
        ..., ge=0, le=1, description="Fatigue (0=Non, 1=Oui)"
    )
    ALLERGY: int = Field(
        ..., ge=0, le=1, description="Allergie (0=Non, 1=Oui)"
    )
    WHEEZING: int = Field(
        ..., ge=0, le=1, description="Respiration sifflante (0=Non, 1=Oui)"
    )
    COUGHING: int = Field(
        ..., ge=0, le=1, description="Toux (0=Non, 1=Oui)"
    )
    SHORTNESS_OF_BREATH: int = Field(
        ...,
        ge=0,
        le=1,
        description="Essoufflement (0=Non, 1=Oui)",
        alias="SHORTNESS OF BREATH"
    )
    SWALLOWING_DIFFICULTY: int = Field(
        ...,
        ge=0,
        le=1,
        description="Difficulté à avaler (0=Non, 1=Oui)",
        alias="SWALLOWING DIFFICULTY"
    )
    CHEST_PAIN: int = Field(
        ...,
        ge=0,
        le=1,
        description="Douleur thoracique (0=Non, 1=Oui)",
        alias="CHEST PAIN"
    )

    class Config:
        """Configuration Pydantic."""

        populate_by_name = True
        json_schema_extra = {
            "example": {
                "AGE": 65,
                "GENDER": 1,
                "SMOKING": 1,
                "ALCOHOL CONSUMING": 1,
                "PEER_PRESSURE": 0,
                "YELLOW_FINGERS": 1,
                "ANXIETY": 0,
                "FATIGUE": 1,
                "ALLERGY": 0,
                "WHEEZING": 1,
                "COUGHING": 1,
                "SHORTNESS OF BREATH": 1,
                "SWALLOWING DIFFICULTY": 0,
                "CHEST PAIN": 1
            }
        }


class PredictionResponse(BaseModel):
    """Modèle pour la réponse de prédiction."""

    prediction: int = Field(
        ..., description="Prédiction (0=Négatif, 1=Positif)"
    )
    probability: Optional[float] = Field(
        None, description="Probabilité de la classe positive"
    )
    message: str = Field(..., description="Message de résultat")


class PredictionProbabilityResponse(BaseModel):
    """Modèle pour la réponse de prédiction avec probabilités."""

    prediction: int = Field(
        ..., description="Prédiction (0=Négatif, 1=Positif)"
    )
    probabilities: List[float] = Field(
        ..., description="Probabilités pour chaque classe"
    )
    message: str = Field(..., description="Message de résultat")


class HealthResponse(BaseModel):
    """Modèle pour la réponse de health check."""

    status: str = Field(..., description="Statut de l'API")
    model_loaded: bool = Field(..., description="Modèle chargé")
    redis_connected: bool = Field(..., description="Redis connecté")
    version: str = Field(..., description="Version de l'API")


class LogEntry(BaseModel):
    """Modèle pour une entrée de log."""

    timestamp: str = Field(..., description="Horodatage du log")
    level: str = Field(..., description="Niveau du log")
    message: str = Field(..., description="Message du log")
    data: Optional[dict] = Field(None, description="Données additionnelles")


class LogsResponse(BaseModel):
    """Modèle pour la réponse des logs."""

    total: int = Field(..., description="Nombre total de logs")
    logs: List[LogEntry] = Field(..., description="Liste des logs")


class LogsStatsResponse(BaseModel):
    """Modèle pour les statistiques des logs."""

    total: int = Field(..., description="Nombre total de logs")
    by_level: dict = Field(..., description="Nombre de logs par niveau")
