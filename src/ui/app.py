"""
Application Gradio - Interface utilisateur pour les prédictions ML.

Ce module fournit une interface Gradio intuitive permettant aux utilisateurs
de saisir les données d'un patient et d'obtenir une prédiction de cancer
du poumon via l'API FastAPI.
"""

import json

import gradio as gr
import requests
from typing import Tuple

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
    chronic_disease: bool
) -> Tuple[str, str]:
    """
    Envoie les données du patient à l'API et retourne la prédiction.

    Args:
        age: Âge du patient (0-120)
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
        Tuple[str, str]: Message de prédiction et niveau de risque
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
        "CHRONIC DISEASE": int(chronic_disease)
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
            f"{settings.API_URL}/predict",
            json=payload,
            timeout=10
        )
        response.raise_for_status()

        data = response.json()
        prediction = data.get("prediction", 0)
        probability = data.get("probability", 0.0)
        message = data.get("message", "")

        # Formater la réponse
        if prediction == 1:
            result = f"⚠️ **RISQUE ÉLEVÉ DE CANCER DU POUMON**\n\n{message}"
            if probability:
                result += f"\n\nProbabilité: {probability:.1%}"
            risk_level = "🔴 ÉLEVÉ"
        else:
            result = f"✅ **RISQUE FAIBLE DE CANCER DU POUMON**\n\n{message}"
            if probability:
                result += f"\n\nProbabilité: {probability:.1%}"
            risk_level = "🟢 FAIBLE"

        return result, risk_level

    except requests.exceptions.ConnectionError:
        error_msg = (
            "❌ **Erreur de connexion**\n\n"
            f"Impossible de se connecter à l'API ({settings.API_URL}).\n"
            "Vérifiez que l'API est en cours d'exécution."
        )
        return error_msg, "⚫ ERREUR"

    except requests.exceptions.Timeout:
        error_msg = (
            "❌ **Délai d'attente dépassé**\n\n"
            "L'API n'a pas répondu dans le délai imparti."
        )
        return error_msg, "⚫ ERREUR"

    except requests.exceptions.HTTPError as e:
        error_msg = (
            f"❌ **Erreur HTTP {response.status_code}**\n\n"
            f"{str(e)}"
        )
        return error_msg, "⚫ ERREUR"

    except Exception as e:
        error_msg = f"❌ **Erreur inattendue**\n\n{str(e)}"
        return error_msg, "⚫ ERREUR"


def create_interface() -> gr.Blocks:
    """
    Crée l'interface Gradio.

    Returns:
        gr.Blocks: Interface Gradio configurée
    """
    with gr.Blocks(
        title="Prédiction Cancer du Poumon",
        theme=gr.themes.Soft()
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
                    minimum=0,
                    maximum=120,
                    value=50,
                    step=1,
                    label="Âge",
                    info="Âge du patient en années"
                )
                gender_input = gr.Dropdown(
                    choices=["Féminin", "Masculin"],
                    value="Féminin",
                    label="Genre",
                    info="Sélectionner le genre du patient"
                )

                gr.Markdown("### 🚬 Facteurs de risque comportementaux")
                smoking_input = gr.Checkbox(
                    label="Fumeur",
                    value=False
                )
                alcohol_input = gr.Checkbox(
                    label="Consommation d'alcool",
                    value=False
                )
                peer_pressure_input = gr.Checkbox(
                    label="Pression des pairs",
                    value=False
                )

                gr.Markdown("### 🔍 Signes physiques")
                yellow_fingers_input = gr.Checkbox(
                    label="Doigts jaunes",
                    value=False
                )
                anxiety_input = gr.Checkbox(
                    label="Anxiété",
                    value=False
                )
                fatigue_input = gr.Checkbox(
                    label="Fatigue chronique",
                    value=False
                )
                allergy_input = gr.Checkbox(
                    label="Allergies",
                    value=False
                )

            with gr.Column():
                gr.Markdown("### 🫁 Symptômes respiratoires")
                wheezing_input = gr.Checkbox(
                    label="Respiration sifflante",
                    value=False
                )
                coughing_input = gr.Checkbox(
                    label="Toux persistante",
                    value=False
                )
                shortness_input = gr.Checkbox(
                    label="Essoufflement",
                    value=False
                )

                gr.Markdown("### 💢 Autres symptômes")
                swallowing_input = gr.Checkbox(
                    label="Difficulté à avaler",
                    value=False
                )
                chest_pain_input = gr.Checkbox(
                    label="Douleur thoracique",
                    value=False
                )
                chronic_disease_input = gr.Checkbox(
                    label="Maladie chronique",
                    value=False
                )

                gr.Markdown("### 🎯 Résultat")
                predict_btn = gr.Button(
                    "Obtenir la prédiction",
                    variant="primary",
                    size="lg"
                )

                risk_output = gr.Textbox(
                    label="Niveau de risque",
                    interactive=False
                )
                result_output = gr.Markdown()

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
                chronic_disease_input
            ],
            outputs=[result_output, risk_output]
        )

        gr.Markdown(
            """
            ---
            ### ℹ️ À propos

            Cette interface utilise:
            - **FastAPI** pour l'API REST
            - **scikit-learn** pour le modèle ML
            - **Gradio** pour l'interface utilisateur

            Les prédictions sont basées sur 14 features d'entrée et 14
            features calculées automatiquement (28 features au total).
            """
        )

    return interface


def launch_ui(
    server_name: str = None,
    server_port: int = None,
    share: bool = False
) -> None:
    """
    Lance l'interface Gradio.

    Args:
        server_name: Nom du serveur (par défaut: settings.GRADIO_HOST)
        server_port: Port du serveur (par défaut: settings.GRADIO_PORT)
        share: Créer un lien public partageable (défaut: False)
    """
    interface = create_interface()

    host = server_name or settings.GRADIO_HOST
    port = server_port or settings.GRADIO_PORT

    print(f"🚀 Lancement de l'interface Gradio sur {host}:{port}")
    print(f"📡 API URL: {settings.API_URL}")

    interface.launch(
        server_name=host,
        server_port=port,
        share=share
    )


if __name__ == "__main__":
    launch_ui()
