"""
API FastAPI pour le modèle de prédiction.

Ce module contient l'application FastAPI avec les endpoints
pour les prédictions, le health check et la consultation des logs.
"""

import json
import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request
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


# Middleware pour logger les requêtes
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware qui log toutes les requêtes avec:
    - ID de transaction (pour les POST)
    - Endpoint appelé
    - Méthode HTTP
    - Inputs (body)
    - Outputs (response)
    - Temps d'exécution
    """
    # Ne pas logger les requêtes health check et logs pour éviter le bruit
    if request.url.path in ["/health", "/logs"]:
        return await call_next(request)

    start_time = time.time()

    # Générer un ID de transaction pour les POST
    transaction_id = None
    if request.method == "POST":
        transaction_id = str(uuid.uuid4())
        request.state.transaction_id = transaction_id

    # Lire le body de la requête
    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            body_bytes = await request.body()
            if body_bytes:
                body = json.loads(body_bytes.decode())

                # Réinjecter le body pour que l'endpoint puisse le lire
                async def receive():
                    return {"type": "http.request", "body": body_bytes}

                request._receive = receive
        except Exception:
            body = "<unable to parse>"

    # Appeler l'endpoint
    response = await call_next(request)

    # Calculer le temps d'exécution
    execution_time = time.time() - start_time

    # Logger la requête si le logger est disponible
    if logger:
        log_data = {
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "execution_time_ms": round(execution_time * 1000, 2)
        }

        # Ajouter l'ID de transaction pour les POST
        if transaction_id:
            log_data["transaction_id"] = transaction_id

        # Logger toutes les données d'entrée pour /predict et /predict_proba
        if body and request.url.path in ["/predict", "/predict_proba"]:
            log_data["input_data"] = body

        # Capturer le résultat de la prédiction si disponible
        if request.url.path in ["/predict", "/predict_proba"]:
            try:
                # Lire le corps de la réponse
                response_body = b""
                async for chunk in response.body_iterator:
                    response_body += chunk

                # Parser le résultat
                result = json.loads(response_body.decode())
                log_data["result"] = result

                # Recréer la réponse avec le body
                from starlette.responses import Response
                response = Response(
                    content=response_body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type
                )
            except Exception:
                log_data["result"] = "<unable to parse>"

        # Formatter le message de log
        log_message = (
            f"API Call - {request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Time: {log_data['execution_time_ms']}ms"
        )

        if transaction_id:
            log_message = f"[{transaction_id}] {log_message}"

        if "input_data" in log_data:
            log_message += f" - Input: {json.dumps(log_data['input_data'])}"

        if "result" in log_data:
            log_message += f" - Result: {json.dumps(log_data['result'])}"

        logger.info(log_message)

    return response


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
    limit: int = Query(100, ge=1, le=1000, description="Nombre de logs"),
    offset: int = Query(0, ge=0, description="Offset pour la pagination")
):
    """
    Récupère les logs de l'API depuis Redis avec pagination.

    Args:
        limit: Nombre maximum de logs à récupérer.
        offset: Nombre de logs à sauter (pour la pagination).

    Returns:
        LogsResponse: Liste des logs avec métadonnées de pagination.
    """
    try:
        result = get_redis_logs(limit=limit, offset=offset)
        logs = result["logs"]
        total = result["total"]

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
            total=total,
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
