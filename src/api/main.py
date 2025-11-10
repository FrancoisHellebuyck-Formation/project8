"""
API FastAPI pour le modèle de prédiction.

Ce module contient l'application FastAPI avec les endpoints
pour les prédictions, le health check et la consultation des logs.
"""

import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from ..config import settings
from ..model import ModelLoader, Predictor
from .logging_config import (
    clear_redis_logs,
    get_redis_logs,
    is_redis_connected,
    setup_logging,
)
from .schemas import (
    HealthResponse,
    LogsResponse,
    PatientData,
    PredictionProbabilityResponse,
    PredictionResponse,
)

# Variables globales
predictor: Optional[Predictor] = None
logger: Optional[logging.Logger] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gère le cycle de vie de l'application (startup/shutdown)."""
    # Startup
    global predictor, logger

    # Configurer le logging
    logger = setup_logging()
    logger.info("Démarrage de l'API...")

    # Charger le modèle au démarrage
    try:
        model_loader = ModelLoader()
        model_loader.load_model()
        predictor = Predictor()
        logger.info("Modèle chargé avec succès")
    except Exception as e:
        error_msg = f"Erreur lors du chargement du modèle : {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

    yield

    # Shutdown
    logger.info("Arrêt de l'API...")


# Créer l'application FastAPI
app = FastAPI(
    title="API de Prédiction ML",
    description=(
        "API pour effectuer des prédictions avec le modèle ML. "
        "Les logs sont stockés dans Redis."
    ),
    version="1.0.0",
    lifespan=lifespan
)

# Ajouter CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root():
    """Endpoint racine."""
    return {
        "message": "API de Prédiction ML",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "predict": "/predict",
            "predict_proba": "/predict_proba",
            "logs": "/logs"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Vérifie l'état de santé de l'API.

    Retourne le statut de l'API, si le modèle est chargé
    et si Redis est connecté.
    """
    model_loaded = predictor is not None and predictor.model_loader.is_loaded()  # noqa: E501
    redis_connected = is_redis_connected()

    status = "healthy" if model_loaded else "unhealthy"

    logger.info(
        f"Health check effectué - Model: {model_loaded}, "
        f"Redis: {redis_connected}"
    )

    return HealthResponse(
        status=status,
        model_loaded=model_loaded,
        redis_connected=redis_connected,
        version="1.0.0"
    )


@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
async def predict(patient: PatientData):
    """
    Effectue une prédiction pour un patient.

    Args:
        patient: Données du patient (14 features de base).

    Returns:
        PredictionResponse: Résultat de la prédiction.
    """
    if predictor is None:
        logger.error("Predictor non initialisé")
        raise HTTPException(
            status_code=500,
            detail="Le modèle n'est pas chargé"
        )

    try:
        # Convertir les données Pydantic en dict
        patient_dict = patient.model_dump(by_alias=True)

        # Effectuer la prédiction
        prediction = predictor.predict(patient_dict)
        pred_value = int(prediction[0])

        # Obtenir la probabilité si disponible
        probability = None
        try:
            proba = predictor.predict_proba(patient_dict)
            probability = float(proba[0][1])  # Probabilité classe positive
        except Exception:
            pass

        # Message de résultat
        message = (
            "Prédiction positive"
            if pred_value == 1
            else "Prédiction négative"
        )

        logger.info(
            f"Prédiction effectuée: {pred_value} "
            f"(prob={probability:.2f}, age={patient.AGE})"
            if probability
            else f"Prédiction effectuée: {pred_value} (age={patient.AGE})"
        )

        return PredictionResponse(
            prediction=pred_value,
            probability=probability,
            message=message
        )

    except Exception as e:
        error_msg = f"Erreur lors de la prédiction : {str(e)}"
        logger.error(f"{error_msg} (patient age={patient.AGE})")
        raise HTTPException(status_code=500, detail=error_msg) from e


@app.post(
    "/predict_proba",
    response_model=PredictionProbabilityResponse,
    tags=["Prediction"]
)
async def predict_proba(patient: PatientData):
    """
    Effectue une prédiction avec probabilités pour un patient.

    Args:
        patient: Données du patient (14 features de base).

    Returns:
        PredictionProbabilityResponse: Résultat avec probabilités.
    """
    if predictor is None:
        logger.error("Predictor non initialisé")
        raise HTTPException(
            status_code=500,
            detail="Le modèle n'est pas chargé"
        )

    try:
        # Convertir les données Pydantic en dict
        patient_dict = patient.model_dump(by_alias=True)

        # Effectuer la prédiction avec probabilités
        probabilities = predictor.predict_proba(patient_dict)
        proba_list = probabilities[0].tolist()

        # Obtenir la prédiction
        prediction = predictor.predict(patient_dict)
        pred_value = int(prediction[0])

        message = (
            "Prédiction positive"
            if pred_value == 1
            else "Prédiction négative"
        )

        logger.info(
            f"Prédiction avec probabilités: {pred_value} "
            f"(proba={proba_list}, age={patient.AGE})"
        )

        return PredictionProbabilityResponse(
            prediction=pred_value,
            probabilities=proba_list,
            message=message
        )

    except Exception as e:
        error_msg = f"Erreur lors de la prédiction : {str(e)}"
        logger.error(f"{error_msg} (patient age={patient.AGE})")
        raise HTTPException(status_code=500, detail=error_msg) from e


@app.get("/logs", response_model=LogsResponse, tags=["Logs"])
async def get_logs(
    limit: int = Query(100, ge=1, le=1000, description="Nombre de logs")
):
    """
    Récupère les logs de l'API depuis Redis.

    Args:
        limit: Nombre maximum de logs à récupérer.

    Returns:
        LogsResponse: Liste des logs.
    """
    try:
        logs = get_redis_logs(limit=limit)

        # Parser les logs pour extraire les informations
        log_entries = []
        for log_str in logs:
            # Le format est: "timestamp - name - level - message"
            parts = log_str.split(" - ", 3)
            if len(parts) >= 4:
                log_entries.append({
                    "timestamp": parts[0],
                    "level": parts[2],
                    "message": parts[3],
                    "data": None
                })

        return LogsResponse(
            total=len(log_entries),
            logs=log_entries
        )

    except Exception as e:
        error_msg = f"Erreur lors de la récupération des logs : {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg) from e


@app.delete("/logs", tags=["Logs"])
async def clear_logs():
    """
    Supprime tous les logs.

    Returns:
        dict: Message de confirmation.
    """
    try:
        success = clear_redis_logs()

        if success:
            logger.info("Logs supprimés")
            return {"message": "Logs supprimés avec succès"}
        else:
            raise HTTPException(
                status_code=500,
                detail="Échec de la suppression des logs"
            )

    except Exception as e:
        error_msg = f"Erreur lors de la suppression des logs : {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg) from e


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
