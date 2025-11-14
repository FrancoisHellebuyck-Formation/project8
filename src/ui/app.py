"""
Application Gradio - Interface utilisateur pour les prédictions ML.

Ce module fournit une interface Gradio intuitive permettant aux utilisateurs
de saisir les données d'un patient et d'obtenir une prédiction de cancer
du poumon via l'API FastAPI.
"""

import json

import gradio as gr
import requests
from fastapi import Request
from fastapi.responses import JSONResponse

from ..config import settings
from .logging_config import setup_ui_logger

# Configurer le logger UI
logger = setup_ui_logger(log_level=settings.UI_LOG_LEVEL)


def predict(
    age: int,
    gender: str,
    smoking: bool,
    alcohol: bool,
    peer_pressure: bool,
    yellow_fingers: bool,
    anxiety: bool,
    fatigue: bool,
    allergy: bool,
    wheezing: bool,
    coughing: bool,
    shortness_of_breath: bool,
    swallowing_difficulty: bool,
    chest_pain: bool,
    chronic_disease: bool,
):
    """
    Envoie les données du patient à l'API et retourne la visualisation.

    Args:
        age: Âge du patient (20-80)
        gender: Genre ("Masculin" ou "Féminin")
        smoking: Fumeur
        alcohol: Consommation d'alcool
        peer_pressure: Pression des pairs
        yellow_fingers: Doigts jaunes
        anxiety: Anxiété
        fatigue: Fatigue
        allergy: Allergies
        wheezing: Respiration sifflante
        coughing: Toux
        shortness_of_breath: Essoufflement
        swallowing_difficulty: Difficulté à avaler
        chest_pain: Douleur thoracique
        chronic_disease: Maladie chronique

    Returns:
        str: HTML avec barre de progression colorée
    """
    # Compter le nombre de symptômes cochés
    symptoms = [
        smoking,
        alcohol,
        peer_pressure,
        yellow_fingers,
        anxiety,
        fatigue,
        allergy,
        wheezing,
        coughing,
        shortness_of_breath,
        swallowing_difficulty,
        chest_pain,
        chronic_disease,
    ]
    num_symptoms = sum(symptoms)

    # Vérifier qu'au moins 3 symptômes sont cochés
    if num_symptoms < 3:
        logger.warning(
            f"Prédiction refusée: seulement {num_symptoms} symptôme(s) "
            f"coché(s), minimum 3 requis"
        )
        return f"""
        <div style="padding: 20px; font-family: sans-serif; text-align: center;">
            <h3 style="color: #f59e0b; margin: 0 0 10px 0;">
                ⚠️ Pas assez d'informations pour effectuer une prédiction
            </h3>
            <p style="color: #6b7280; margin: 0;">
                Veuillez cocher au minimum 3 symptômes ou facteurs de risque
                pour obtenir une prédiction fiable.
            </p>
            <p style="color: #6b7280; margin: 10px 0 0 0; font-size: 14px;">
                Actuellement: {num_symptoms} symptôme(s) coché(s)
            </p>
        </div>
        """

    # Construire le payload pour l'API
    payload = {
        "AGE": age,
        "GENDER": 1 if gender == "Masculin" else 0,
        "SMOKING": int(smoking),
        "ALCOHOL CONSUMING": int(alcohol),
        "PEER_PRESSURE": int(peer_pressure),
        "YELLOW_FINGERS": int(yellow_fingers),
        "ANXIETY": int(anxiety),
        "FATIGUE": int(fatigue),
        "ALLERGY": int(allergy),
        "WHEEZING": int(wheezing),
        "COUGHING": int(coughing),
        "SHORTNESS OF BREATH": int(shortness_of_breath),
        "SWALLOWING DIFFICULTY": int(swallowing_difficulty),
        "CHEST PAIN": int(chest_pain),
        "CHRONIC DISEASE": int(chronic_disease),
    }

    # Debug: afficher le payload
    logger.info("=" * 60)
    logger.info("Payload envoyé à l'API:")
    logger.info("-" * 60)
    logger.info(json.dumps(payload, indent=2))
    logger.info("=" * 60)

    try:
        # Appel à l'API
        response = requests.post(
            f"{settings.API_URL}/predict", json=payload, timeout=10
        )
        response.raise_for_status()

        data = response.json()
        probability = data.get("probability", 0.0)

        # Créer la barre de progression HTML avec gradient
        return create_probability_bar(probability)

    except requests.exceptions.ConnectionError:
        logger.error(f"Impossible de se connecter à l'API ({settings.API_URL})")
        return create_probability_bar(0.0, error=True)

    except requests.exceptions.Timeout:
        logger.error("L'API n'a pas répondu dans le délai imparti")
        return create_probability_bar(0.0, error=True)

    except requests.exceptions.HTTPError as e:
        logger.error(f"Erreur HTTP {response.status_code}: {str(e)}")
        return create_probability_bar(0.0, error=True)

    except Exception as e:
        logger.error(f"Erreur inattendue: {str(e)}")
        return create_probability_bar(0.0, error=True)


def create_probability_bar(probability: float, error: bool = False) -> str:
    """
    Crée une barre de progression HTML avec gradient de couleurs.

    Args:
        probability: Probabilité entre 0.0 et 1.0
        error: Indique si c'est une erreur

    Returns:
        str: Code HTML de la barre
    """
    if error:
        return """
        <div style="text-align: center; padding: 20px;">
            <p style="color: #ef4444; font-size: 18px; font-weight: bold;">
                ❌ Erreur de connexion à l'API
            </p>
        </div>
        """

    percentage = probability * 100

    # Déterminer la couleur en fonction du pourcentage
    if percentage < 33:
        color = "#22c55e"  # Vert
        risk_text = "FAIBLE"
        emoji = "🟢"
    elif percentage < 66:
        color = "#f59e0b"  # Orange
        risk_text = "MODÉRÉ"
        emoji = "🟠"
    else:
        color = "#ef4444"  # Rouge
        risk_text = "ÉLEVÉ"
        emoji = "🔴"

    html = f"""
    <div style="padding: 20px; font-family: sans-serif;">
        <div style="margin-bottom: 15px;">
            <h3 style="margin: 0 0 10px 0; color: #1f2937;">
                {emoji} Risque de cancer du poumon: {risk_text}
            </h3>
            <p style="margin: 0; font-size: 24px; font-weight: bold; color: {color};">
                {percentage:.1f}%
            </p>
        </div>

        <div style="position: relative; height: 40px; background: linear-gradient(to right, #22c55e 0%, #84cc16 25%, #f59e0b 50%, #fb923c 75%, #ef4444 100%); border-radius: 20px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="position: absolute; left: {percentage}%; top: 50%; transform: translate(-50%, -50%); width: 4px; height: 50px; background: white; border: 2px solid #1f2937; border-radius: 2px; box-shadow: 0 2px 6px rgba(0,0,0,0.3);"></div>
        </div>

        <div style="display: flex; justify-content: space-between; margin-top: 8px; font-size: 12px; color: #6b7280;">
            <span>0% (Faible)</span>
            <span>50% (Modéré)</span>
            <span>100% (Élevé)</span>
        </div>
    </div>
    """
    return html


def api_health_proxy():
    """Proxy vers l'endpoint /health de FastAPI."""
    try:
        response = requests.get(f"{settings.API_URL}/health", timeout=5)
        return response.json(), response.status_code
    except Exception as e:
        return {"error": str(e)}, 503


def api_predict_proxy(payload: dict):
    """Proxy vers l'endpoint /predict de FastAPI."""
    try:
        response = requests.post(
            f"{settings.API_URL}/predict", json=payload, timeout=10
        )
        return response.json(), response.status_code
    except Exception as e:
        return {"error": str(e)}, 503


def api_predict_proba_proxy(payload: dict):
    """Proxy vers l'endpoint /predict_proba de FastAPI."""
    try:
        response = requests.post(
            f"{settings.API_URL}/predict_proba", json=payload, timeout=10
        )
        return response.json(), response.status_code
    except Exception as e:
        return {"error": str(e)}, 503


def api_logs_proxy(limit: int = 100):
    """Proxy vers l'endpoint /logs de FastAPI."""
    try:
        response = requests.get(
            f"{settings.API_URL}/logs?limit={limit}", timeout=10
        )
        return response.json(), response.status_code
    except Exception as e:
        return {"error": str(e)}, 503


def create_interface() -> gr.Blocks:
    """
    Crée l'interface Gradio.

    Returns:
        gr.Blocks: Interface Gradio configurée
    """
    with gr.Blocks(
        title="Prédiction Cancer du Poumon", theme=gr.themes.Soft()
    ) as interface:
        gr.Markdown(
            """
            # 🫁 Prédiction de Cancer du Poumon

            Cette application utilise un modèle de machine learning pour
            évaluer le risque de cancer du poumon basé sur les données
            d'un patient.

            **Note**: Cette application est à but éducatif uniquement et
            ne remplace pas un diagnostic médical professionnel.
            """
        )

        with gr.Row():
            with gr.Column():
                gr.Markdown("### 📋 Informations générales")
                age_input = gr.Slider(
                    minimum=20,
                    maximum=80,
                    value=50,
                    step=1,
                    label="Âge",
                    info="Âge du patient en années (20-80 ans)",
                )
                gender_input = gr.Radio(
                    choices=["Féminin", "Masculin"],
                    value="Féminin",
                    label="Genre",
                    info="Sélectionner le genre du patient",
                )

                gr.Markdown("### 🍾 Facteurs de risque comportementaux")
                smoking_input = gr.Checkbox(label="Fumeur", value=False)
                alcohol_input = gr.Checkbox(label="Consommation d'alcool", value=False)
                peer_pressure_input = gr.Checkbox(
                    label="Pression des pairs", value=False
                )

                gr.Markdown("### 👫 Signes physiques")
                yellow_fingers_input = gr.Checkbox(label="Doigts jaunes", value=False)
                anxiety_input = gr.Checkbox(label="Anxiété", value=False)
                fatigue_input = gr.Checkbox(label="Fatigue chronique", value=False)
                allergy_input = gr.Checkbox(label="Allergies", value=False)

            with gr.Column():
                gr.Markdown("### 🫁 Symptômes respiratoires")
                wheezing_input = gr.Checkbox(label="Respiration sifflante", value=False)
                coughing_input = gr.Checkbox(label="Toux persistante", value=False)
                shortness_input = gr.Checkbox(label="Essoufflement", value=False)

                gr.Markdown("### 💢 Autres symptômes")
                swallowing_input = gr.Checkbox(label="Difficulté à avaler", value=False)
                chest_pain_input = gr.Checkbox(label="Douleur thoracique", value=False)
                chronic_disease_input = gr.Checkbox(
                    label="Maladie chronique", value=False
                )

                gr.Markdown("### 🎯 Résultat")
                predict_btn = gr.Button(
                    "Obtenir la prédiction", variant="primary", size="lg"
                )

                result_html = gr.HTML(
                    label="Probabilité de cancer du poumon",
                    value=create_probability_bar(0.0),
                )

        # Connecter le bouton à la fonction de prédiction
        predict_btn.click(
            fn=predict,
            inputs=[
                age_input,
                gender_input,
                smoking_input,
                alcohol_input,
                peer_pressure_input,
                yellow_fingers_input,
                anxiety_input,
                fatigue_input,
                allergy_input,
                wheezing_input,
                coughing_input,
                shortness_input,
                swallowing_input,
                chest_pain_input,
                chronic_disease_input,
            ],
            outputs=result_html,
        )

        gr.Markdown(
            """
            ---
            ### ℹ️ À propos

            Cette interface utilise:
            - **FastAPI** pour l'API REST
            - **LightGBM** pour le modèle ML
            - **Gradio** pour l'interface utilisateur

            Les prédictions sont basées sur 15 features d'entrée et 14
            features calculées automatiquement (29 features au total).

            La barre de probabilité indique le risque prédit de cancer
            du poumon de 0% (risque très faible) à 100% (risque très élevé).
            """
        )

    return interface


def launch_ui(
    server_name: str = None, server_port: int = None, share: bool = False
) -> None:
    """
    Lance l'interface Gradio.

    Args:
        server_name: Nom du serveur (par défaut: settings.GRADIO_HOST)
        server_port: Port du serveur (par défaut: settings.GRADIO_PORT)
        share: Créer un lien public partageable (défaut: False)
    """
    interface = create_interface()

    # Ajouter les routes API proxy vers FastAPI
    @interface.app.get("/api/health")
    async def health_endpoint():
        """Endpoint proxy vers /health de FastAPI."""
        result, status_code = api_health_proxy()
        return JSONResponse(content=result, status_code=status_code)

    @interface.app.post("/api/predict")
    async def predict_endpoint(request: Request):
        """Endpoint proxy vers /predict de FastAPI."""
        payload = await request.json()
        result, status_code = api_predict_proxy(payload)
        return JSONResponse(content=result, status_code=status_code)

    @interface.app.post("/api/predict_proba")
    async def predict_proba_endpoint(request: Request):
        """Endpoint proxy vers /predict_proba de FastAPI."""
        payload = await request.json()
        result, status_code = api_predict_proba_proxy(payload)
        return JSONResponse(content=result, status_code=status_code)

    @interface.app.get("/api/logs")
    async def logs_endpoint(limit: int = 100):
        """Endpoint proxy vers /logs de FastAPI."""
        result, status_code = api_logs_proxy(limit)
        return JSONResponse(content=result, status_code=status_code)

    host = server_name or settings.GRADIO_HOST
    port = server_port or settings.GRADIO_PORT

    print(f"🚀 Lancement de l'interface Gradio sur {host}:{port}")
    print(f"📡 API URL: {settings.API_URL}")
    print("\n📍 Endpoints API proxy disponibles sur Gradio:")
    print(f"   - GET  http://{host}:{port}/api/health")
    print(f"   - POST http://{host}:{port}/api/predict")
    print(f"   - POST http://{host}:{port}/api/predict_proba")
    print(f"   - GET  http://{host}:{port}/api/logs?limit=100")

    interface.launch(server_name=host, server_port=port, share=share)


if __name__ == "__main__":
    launch_ui()
