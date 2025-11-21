"""
Interface Gradio pour le proxy API.

Ce module crée une interface Gradio complète qui expose tous les
endpoints de l'API FastAPI de manière interactive.
"""

import json
import logging
from typing import Tuple

import gradio as gr

from .client import APIProxyClient

logger = logging.getLogger(__name__)


def create_proxy_interface(
    api_url: str = None,
    share: bool = False
) -> gr.Blocks:
    """
    Crée l'interface Gradio pour le proxy API.

    Args:
        api_url: URL de l'API FastAPI (optionnel)
        share: Créer un lien public Gradio (défaut: False)

    Returns:
        gr.Blocks: Interface Gradio
    """
    client = APIProxyClient(api_url)

    # ==================== WRAPPERS ====================

    def format_response(response: Tuple) -> str:
        """Formate la réponse pour l'affichage."""
        response_json, status_code = response
        return json.dumps({
            "status_code": status_code,
            "response": response_json
        }, indent=2, ensure_ascii=False)

    def root_wrapper() -> str:
        """Wrapper pour GET /."""
        return format_response(client.get_root())

    def health_wrapper() -> str:
        """Wrapper pour GET /health."""
        return format_response(client.get_health())

    def predict_wrapper(
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
        chronic_disease: bool
    ) -> str:
        """Wrapper pour POST /predict."""
        patient_data = {
            "AGE": age,
            "GENDER": 1 if gender == "Homme" else 2,
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
            "CHRONIC DISEASE": int(chronic_disease)
        }
        return format_response(client.post_predict(patient_data))

    def predict_proba_wrapper(
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
        chronic_disease: bool
    ) -> str:
        """Wrapper pour POST /predict_proba."""
        patient_data = {
            "AGE": age,
            "GENDER": 1 if gender == "Homme" else 2,
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
            "CHRONIC DISEASE": int(chronic_disease)
        }
        return format_response(client.post_predict_proba(patient_data))

    def logs_wrapper(limit: int, offset: int) -> str:
        """Wrapper pour GET /logs."""
        return format_response(client.get_logs(limit, offset))

    def delete_logs_wrapper() -> str:
        """Wrapper pour DELETE /logs."""
        return format_response(client.delete_logs())

    def connection_check_wrapper() -> str:
        """Vérifie la connexion à l'API."""
        is_connected = client.check_connection()
        return json.dumps({
            "connected": is_connected,
            "api_url": client.api_url,
            "message": "✅ Connecté" if is_connected else "❌ Déconnecté"
        }, indent=2, ensure_ascii=False)

    # ==================== INTERFACE GRADIO ====================

    with gr.Blocks(
        title="API Proxy - Interface Complète",
        theme=gr.themes.Soft()
    ) as interface:
        gr.Markdown(
            """
            # 🔄 API Proxy - Interface Complète

            Interface Gradio permettant d'accéder à tous les endpoints
            de l'API FastAPI (port 8000) via le port Gradio (7860).
            """
        )

        # ==================== SECTION: CONNEXION ====================

        with gr.Accordion("🔌 Vérification de connexion", open=True):
            connection_btn = gr.Button("Vérifier la connexion")
            connection_output = gr.Textbox(
                label="État de la connexion",
                lines=5,
                interactive=False
            )
            connection_btn.click(
                fn=connection_check_wrapper,
                outputs=connection_output
            )

        # ==================== SECTION: INFORMATIONS API ====================

        with gr.Accordion("ℹ️ Informations de l'API", open=False):
            gr.Markdown("### GET /")
            root_btn = gr.Button("Récupérer les informations")
            root_output = gr.Textbox(
                label="Réponse",
                lines=10,
                interactive=False
            )
            root_btn.click(fn=root_wrapper, outputs=root_output)

        # ==================== SECTION: HEALTH CHECK ====================

        with gr.Accordion("💚 Health Check", open=False):
            gr.Markdown("### GET /health")
            health_btn = gr.Button("Vérifier la santé de l'API")
            health_output = gr.Textbox(
                label="Réponse",
                lines=10,
                interactive=False
            )
            health_btn.click(fn=health_wrapper, outputs=health_output)

        # ==================== SECTION: PRÉDICTION ====================

        with gr.Accordion("🔮 Prédiction ML", open=True):
            gr.Markdown("### POST /predict")
            gr.Markdown(
                "Effectue une prédiction de cancer du poumon "
                "basée sur les données du patient."
            )

            with gr.Row():
                with gr.Column():
                    age_input = gr.Slider(
                        minimum=18,
                        maximum=100,
                        value=50,
                        label="Âge du patient",
                        step=1
                    )
                    gender_input = gr.Dropdown(
                        choices=["Homme", "Femme"],
                        value="Homme",
                        label="Genre"
                    )

                with gr.Column():
                    smoking_input = gr.Checkbox(label="Fumeur")
                    alcohol_input = gr.Checkbox(label="Consommation d'alcool")
                    peer_pressure_input = gr.Checkbox(
                        label="Pression des pairs"
                    )
                    chronic_disease_input = gr.Checkbox(
                        label="Maladie chronique"
                    )

                with gr.Column():
                    yellow_fingers_input = gr.Checkbox(
                        label="Doigts jaunes"
                    )
                    anxiety_input = gr.Checkbox(label="Anxiété")
                    fatigue_input = gr.Checkbox(label="Fatigue")
                    allergy_input = gr.Checkbox(label="Allergie")

                with gr.Column():
                    wheezing_input = gr.Checkbox(label="Respiration sifflante")
                    coughing_input = gr.Checkbox(label="Toux")
                    shortness_of_breath_input = gr.Checkbox(
                        label="Essoufflement"
                    )
                    swallowing_difficulty_input = gr.Checkbox(
                        label="Difficulté à avaler"
                    )
                    chest_pain_input = gr.Checkbox(label="Douleur thoracique")

            predict_btn = gr.Button("🔮 Prédire", variant="primary")
            predict_output = gr.Textbox(
                label="Résultat de la prédiction",
                lines=10,
                interactive=False
            )

            predict_btn.click(
                fn=predict_wrapper,
                inputs=[
                    age_input, gender_input, smoking_input, alcohol_input,
                    peer_pressure_input, yellow_fingers_input,
                    anxiety_input, fatigue_input, allergy_input,
                    wheezing_input, coughing_input,
                    shortness_of_breath_input, swallowing_difficulty_input,
                    chest_pain_input, chronic_disease_input
                ],
                outputs=predict_output
            )

        # ==================== SECTION: PROBABILITÉS ====================

        with gr.Accordion("📊 Probabilités de prédiction", open=False):
            gr.Markdown("### POST /predict_proba")
            gr.Markdown(
                "Récupère les probabilités détaillées pour chaque classe."
            )

            with gr.Row():
                with gr.Column():
                    age_proba_input = gr.Slider(
                        minimum=18,
                        maximum=100,
                        value=50,
                        label="Âge du patient",
                        step=1
                    )
                    gender_proba_input = gr.Dropdown(
                        choices=["Homme", "Femme"],
                        value="Homme",
                        label="Genre"
                    )

                with gr.Column():
                    smoking_proba_input = gr.Checkbox(label="Fumeur")
                    alcohol_proba_input = gr.Checkbox(
                        label="Consommation d'alcool"
                    )
                    peer_pressure_proba_input = gr.Checkbox(
                        label="Pression des pairs"
                    )
                    chronic_disease_proba_input = gr.Checkbox(
                        label="Maladie chronique"
                    )

                with gr.Column():
                    yellow_fingers_proba_input = gr.Checkbox(
                        label="Doigts jaunes"
                    )
                    anxiety_proba_input = gr.Checkbox(label="Anxiété")
                    fatigue_proba_input = gr.Checkbox(label="Fatigue")
                    allergy_proba_input = gr.Checkbox(label="Allergie")

                with gr.Column():
                    wheezing_proba_input = gr.Checkbox(
                        label="Respiration sifflante"
                    )
                    coughing_proba_input = gr.Checkbox(label="Toux")
                    shortness_of_breath_proba_input = gr.Checkbox(
                        label="Essoufflement"
                    )
                    swallowing_difficulty_proba_input = gr.Checkbox(
                        label="Difficulté à avaler"
                    )
                    chest_pain_proba_input = gr.Checkbox(
                        label="Douleur thoracique"
                    )

            predict_proba_btn = gr.Button(
                "📊 Calculer les probabilités",
                variant="primary"
            )
            predict_proba_output = gr.Textbox(
                label="Probabilités",
                lines=10,
                interactive=False
            )

            predict_proba_btn.click(
                fn=predict_proba_wrapper,
                inputs=[
                    age_proba_input, gender_proba_input,
                    smoking_proba_input, alcohol_proba_input,
                    peer_pressure_proba_input, yellow_fingers_proba_input,
                    anxiety_proba_input, fatigue_proba_input,
                    allergy_proba_input, wheezing_proba_input,
                    coughing_proba_input, shortness_of_breath_proba_input,
                    swallowing_difficulty_proba_input,
                    chest_pain_proba_input, chronic_disease_proba_input
                ],
                outputs=predict_proba_output
            )

        # ==================== SECTION: LOGS ====================

        with gr.Accordion("📋 Gestion des logs", open=False):
            gr.Markdown("### GET /logs")

            with gr.Row():
                limit_input = gr.Slider(
                    minimum=1,
                    maximum=1000,
                    value=100,
                    label="Nombre de logs",
                    step=1
                )
                offset_input = gr.Slider(
                    minimum=0,
                    maximum=10000,
                    value=0,
                    label="Offset (pagination)",
                    step=10
                )

            logs_btn = gr.Button("📋 Récupérer les logs")
            logs_output = gr.Textbox(
                label="Logs",
                lines=15,
                interactive=False
            )

            logs_btn.click(
                fn=logs_wrapper,
                inputs=[limit_input, offset_input],
                outputs=logs_output
            )

            gr.Markdown("### DELETE /logs")
            gr.Markdown(
                "⚠️ **Attention** : Cette action vide complètement "
                "le cache Redis des logs."
            )

            delete_logs_btn = gr.Button(
                "🗑️ Vider les logs Redis",
                variant="stop"
            )
            delete_logs_output = gr.Textbox(
                label="Résultat",
                lines=5,
                interactive=False
            )

            delete_logs_btn.click(
                fn=delete_logs_wrapper,
                outputs=delete_logs_output
            )

        # ==================== FOOTER ====================

        gr.Markdown(
            """
            ---
            ### 📚 Documentation

            - **API FastAPI** : http://localhost:8000/docs
            - **ReDoc** : http://localhost:8000/redoc
            - **Proxy Gradio** : http://localhost:7860

            ### ℹ️ À propos

            Ce proxy permet d'accéder à tous les endpoints de l'API
            FastAPI via une interface Gradio conviviale.
            """
        )

    return interface


def launch_proxy(
    api_url: str = None,
    server_name: str = "0.0.0.0",
    server_port: int = 7860,
    share: bool = False
):
    """
    Lance l'interface proxy Gradio.

    Args:
        api_url: URL de l'API FastAPI
        server_name: Nom du serveur (défaut: 0.0.0.0)
        server_port: Port du serveur (défaut: 7860)
        share: Créer un lien public Gradio (défaut: False)
    """
    interface = create_proxy_interface(api_url, share)
    interface.launch(
        server_name=server_name,
        server_port=server_port,
        share=share
    )


if __name__ == "__main__":
    launch_proxy()
