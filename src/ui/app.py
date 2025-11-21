"""
Application Gradio - Interface utilisateur pour les prédictions ML.

Ce module fournit une interface Gradio intuitive permettant aux utilisateurs
de saisir les données d'un patient et d'obtenir une prédiction de cancer
du poumon via l'API FastAPI.
"""

import json
import os

import gradio as gr
import requests

from ..config import settings
from .logging_config import setup_ui_logger

# Configurer le logger UI
logger = setup_ui_logger(log_level=settings.UI_LOG_LEVEL)

# Détecter si on est sur HuggingFace Spaces
IS_HUGGINGFACE_SPACE = os.getenv("SPACE_ID") is not None

# Import conditionnel du package proxy pour HuggingFace
if IS_HUGGINGFACE_SPACE:
    try:
        from ..proxy import APIProxyClient
        proxy_client = APIProxyClient()
        logger.info("✅ Package proxy chargé pour HuggingFace Spaces")
    except ImportError:
        logger.warning("⚠️  Package proxy non disponible, utilisation des"
                       " fonctions proxy locales")
        IS_HUGGINGFACE_SPACE = False
        proxy_client = None
else:
    proxy_client = None
    logger.info("ℹ️  Environnement local détecté, utilisation des fonctions"
                " proxy simples")


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
    if IS_HUGGINGFACE_SPACE and proxy_client:
        # Utiliser le package proxy sur HuggingFace
        return proxy_client.get_health()
    else:
        # Utiliser la fonction proxy simple en local
        try:
            response = requests.get(f"{settings.API_URL}/health", timeout=5)
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 503


def api_predict_proxy(payload: dict):
    """Proxy vers l'endpoint /predict de FastAPI."""
    if IS_HUGGINGFACE_SPACE and proxy_client:
        # Utiliser le package proxy sur HuggingFace
        return proxy_client.post_predict(payload)
    else:
        # Utiliser la fonction proxy simple en local
        try:
            response = requests.post(
                f"{settings.API_URL}/predict", json=payload, timeout=10
            )
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 503


def api_predict_proba_proxy(payload: dict):
    """Proxy vers l'endpoint /predict_proba de FastAPI."""
    if IS_HUGGINGFACE_SPACE and proxy_client:
        # Utiliser le package proxy sur HuggingFace
        return proxy_client.post_predict_proba(payload)
    else:
        # Utiliser la fonction proxy simple en local
        try:
            response = requests.post(
                f"{settings.API_URL}/predict_proba", json=payload, timeout=10
            )
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 503


def api_logs_proxy(limit: int = 100, offset: int = 0):
    """Proxy vers l'endpoint /logs de FastAPI avec pagination."""
    if IS_HUGGINGFACE_SPACE and proxy_client:
        # Utiliser le package proxy sur HuggingFace
        return proxy_client.get_logs(limit=limit, offset=offset)
    else:
        # Utiliser la fonction proxy simple en local
        try:
            response = requests.get(
                f"{settings.API_URL}/logs?limit={limit}&offset={offset}",
                timeout=10
            )
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 503


def api_clear_logs_proxy():
    """Proxy vers l'endpoint DELETE /logs de FastAPI."""
    if IS_HUGGINGFACE_SPACE and proxy_client:
        # Utiliser le package proxy sur HuggingFace
        return proxy_client.delete_logs()
    else:
        # Utiliser la fonction proxy simple en local
        try:
            response = requests.delete(
                f"{settings.API_URL}/logs",
                timeout=10
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

        # === API Endpoints via Gradio (compatibles HF Spaces) ===
        gr.Markdown(
            """
            ---
            ### 🔌 API Endpoints

            Testez les endpoints de l'API directement depuis cette interface.
            Ces endpoints sont également accessibles via l'API Gradio
            (voir documentation ci-dessous).
            """
        )

        with gr.Accordion("🩺 Health Check", open=False):
            gr.Markdown(
                """
                Vérifie l'état de santé de l'API, du modèle et de Redis.

                **API Gradio:** `/api/health`
                """
            )
            with gr.Row():
                health_btn = gr.Button("🔍 Vérifier l'état", variant="secondary")
                health_output = gr.JSON(label="Statut de l'API")

            def health_check_wrapper():
                """Wrapper pour le health check."""
                result, _ = api_health_proxy()
                return result

            health_btn.click(
                fn=health_check_wrapper,
                inputs=None,
                outputs=health_output,
                api_name="health"
            )

        with gr.Accordion("🎯 Prédiction (JSON)", open=False):
            gr.Markdown(
                """
                Effectue une prédiction binaire (0 ou 1) à partir d'un JSON.

                **API Gradio:** `/api/predict_api`

                **Format du JSON:**
                ```json
                {
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
                  "CHEST PAIN": 1,
                  "CHRONIC DISEASE": 0
                }
                ```
                """
            )
            with gr.Row():
                with gr.Column():
                    predict_json_input = gr.JSON(
                        label="Données patient (JSON)",
                        value={
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
                            "CHEST PAIN": 1,
                            "CHRONIC DISEASE": 0
                        }
                    )
                    predict_btn_api = gr.Button(
                        "🔮 Prédire", variant="primary"
                    )
                with gr.Column():
                    predict_json_output = gr.JSON(label="Résultat")

            def predict_api_wrapper(data):
                """Wrapper pour l'API de prédiction."""
                result, _ = api_predict_proxy(data)
                return result

            predict_btn_api.click(
                fn=predict_api_wrapper,
                inputs=predict_json_input,
                outputs=predict_json_output,
                api_name="predict_api"
            )

        with gr.Accordion("📊 Prédiction avec probabilités (JSON)", open=False):
            gr.Markdown(
                """
                Effectue une prédiction avec probabilité détaillée.

                **API Gradio:** `/api/predict_proba_api`
                """
            )
            with gr.Row():
                with gr.Column():
                    predict_proba_input = gr.JSON(
                        label="Données patient (JSON)",
                        value={
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
                            "CHEST PAIN": 1,
                            "CHRONIC DISEASE": 0
                        }
                    )
                    predict_proba_btn = gr.Button(
                        "🔮 Prédire avec probabilités", variant="primary"
                    )
                with gr.Column():
                    predict_proba_output = gr.JSON(label="Résultat")

            def predict_proba_api_wrapper(data):
                """Wrapper pour l'API predict_proba."""
                result, _ = api_predict_proba_proxy(data)
                return result

            predict_proba_btn.click(
                fn=predict_proba_api_wrapper,
                inputs=predict_proba_input,
                outputs=predict_proba_output,
                api_name="predict_proba_api"
            )

        with gr.Accordion("📝 Logs de l'API", open=False):
            gr.Markdown(
                """
                Récupère les derniers logs de l'API.

                **API Gradio:** `/api/logs_api`
                """
            )
            with gr.Row():
                with gr.Column(scale=1):
                    logs_limit_input = gr.Slider(
                        minimum=1,
                        maximum=100,
                        value=10,
                        step=1,
                        label="Nombre de logs à récupérer"
                    )
                    logs_offset_input = gr.Number(
                        value=0,
                        minimum=0,
                        step=1,
                        label="Offset (pagination)",
                        precision=0
                    )
                    logs_btn = gr.Button("📋 Récupérer les logs", variant="secondary")
                with gr.Column(scale=2):
                    logs_output = gr.JSON(label="Logs")

            def logs_api_wrapper(limit, offset):
                """Wrapper pour l'API des logs."""
                result, _ = api_logs_proxy(int(limit), int(offset))
                return result

            logs_btn.click(
                fn=logs_api_wrapper,
                inputs=[logs_limit_input, logs_offset_input],
                outputs=logs_output,
                api_name="logs_api"
            )

            # Endpoint pour vider les logs Redis (via API proxy)
            # Exposé uniquement via l'API, pas dans l'interface visible
            def clear_logs_api_wrapper():
                """Wrapper pour vider les logs Redis."""
                result, _ = api_clear_logs_proxy()
                return result

            # Créer un bouton invisible juste pour exposer l'API
            clear_logs_output = gr.JSON(visible=False)
            clear_logs_btn = gr.Button(
                "🗑️ Vider les logs Redis",
                visible=False
            )
            clear_logs_btn.click(
                fn=clear_logs_api_wrapper,
                outputs=clear_logs_output,
                api_name="api_clear_logs_proxy"
            )

    return interface


def launch_ui(
    server_name: str = None, server_port: int = None, share: bool = False
) -> None:
    """
    Lance l'interface Gradio avec API REST montée.

    Args:
        server_name: Nom du serveur (par défaut: settings.GRADIO_HOST)
        server_port: Port du serveur (par défaut: settings.GRADIO_PORT)
        share: Créer un lien public partageable (défaut: False)
    """
    interface = create_interface()

    # Monter les routes FastAPI AVANT le lancement
    # Gradio expose son app FastAPI via interface.app
    try:
        from .api_routes import api_router
        # Gradio crée automatiquement une instance FastAPI
        # On peut y inclure nos routes
        interface.app.include_router(api_router)
        logger.info("✅ Routes FastAPI montées pour accès HTTP/curl direct")
    except Exception as e:
        logger.warning(
            f"⚠️  Impossible de monter les routes API: {e}"
        )

    host = server_name or settings.GRADIO_HOST
    port = server_port or settings.GRADIO_PORT

    print(f"🚀 Lancement de l'interface Gradio sur {host}:{port}")
    print(f"📡 API Backend: {settings.API_URL}")
    print("\n📍 Fonctionnalités disponibles:")
    print("   ✅ Interface de prédiction interactive")
    print("   ✅ Section API Endpoints (testez l'API directement)")
    print("   ✅ Health check, prédictions JSON, logs")
    print("\n📍 API REST (accès HTTP/curl direct):")
    print("   - GET  /api/health")
    print("   - POST /api/predict")
    print("   - POST /api/predict_proba")
    print("   - GET  /api/logs?limit=100&offset=0")
    print("   - DELETE /api/logs")
    print("\n📍 API Gradio (intégration programmatique):")
    print("   - /api/health")
    print("   - /api/predict_api")
    print("   - /api/predict_proba_api")
    print("   - /api/logs_api")
    print(f"\n💡 Interface web: http://{host}:{port}")
    print("💡 Documentation: Voir section 'API Endpoints' dans l'interface")
    print("\n🔧 Test curl:")
    print(f"   curl http://{host}:{port}/api/health")

    interface.launch(server_name=host, server_port=port, share=share)


if __name__ == "__main__":
    launch_ui()
