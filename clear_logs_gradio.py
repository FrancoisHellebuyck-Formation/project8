#!/usr/bin/env python3
"""
Script pour vider les logs Redis via l'interface Gradio.

Ce script utilise le client Gradio pour appeler l'endpoint DELETE /logs
via le proxy api_clear_logs_proxy de l'interface Gradio.

Usage:
    # Local
    GRADIO_URL=http://localhost:7860 python clear_logs_gradio.py

    # HuggingFace Spaces (public)
    GRADIO_URL=https://francoisformation-oc-project8.hf.space \
        python clear_logs_gradio.py

    # HuggingFace Spaces (privé, avec token)
    HF_TOKEN=hf_xxxxx \
    GRADIO_URL=https://francoisformation-oc-project8.hf.space \
        python clear_logs_gradio.py
"""

import json
import os
import sys

try:
    from gradio_client import Client
except ImportError:
    print("❌ Erreur: gradio_client n'est pas installé")
    print("   Installez-le avec: pip install gradio-client")
    sys.exit(1)


def clear_logs_via_gradio(gradio_url: str, hf_token: str = None):
    """
    Vide les logs Redis via l'interface Gradio.

    Args:
        gradio_url: URL de l'interface Gradio
        hf_token: Token HuggingFace (optionnel, pour Spaces privés)

    Returns:
        dict: Réponse de l'API
    """
    print(f"🔗 Connexion à Gradio: {gradio_url}")

    if hf_token:
        print(f"🔐 Token HuggingFace: {hf_token[:10]}...")
        client = Client(gradio_url, hf_token=hf_token)
    else:
        print("🔓 Pas de token HuggingFace (Space public)")
        client = Client(gradio_url)

    print("🗑️  Suppression des logs Redis...")

    try:
        # Appeler le proxy api_clear_logs_proxy
        result = client.predict(api_name="/api_clear_logs_proxy")

        # result est un tuple (response_json, status_code)
        if isinstance(result, tuple) and len(result) == 2:
            response_json, status_code = result

            print(f"📊 Status HTTP: {status_code}")

            if status_code == 200:
                print("✅ Logs supprimés avec succès")
                print(f"📄 Réponse: {json.dumps(response_json, indent=2)}")
                return response_json
            else:
                print(f"❌ Erreur HTTP {status_code}")
                print(f"📄 Réponse: {json.dumps(response_json, indent=2)}")
                return response_json
        else:
            print(f"⚠️  Format de réponse inattendu: {result}")
            return result

    except Exception as e:
        print(f"❌ Erreur lors de la suppression: {str(e)}")
        return {"error": str(e)}


def main():
    """Point d'entrée principal."""
    # Récupérer l'URL Gradio depuis l'environnement
    gradio_url = os.getenv(
        "GRADIO_URL",
        "http://localhost:7860"
    )

    # Récupérer le token HF depuis l'environnement (optionnel)
    hf_token = os.getenv("HF_TOKEN")

    print("=" * 60)
    print("🗑️  Suppression des logs Redis via Gradio")
    print("=" * 60)
    print()

    result = clear_logs_via_gradio(gradio_url, hf_token)

    print()
    print("=" * 60)

    # Code de sortie basé sur le résultat
    if isinstance(result, dict):
        if "error" in result:
            sys.exit(1)
        elif result.get("message") == "Logs supprimés avec succès":
            sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
