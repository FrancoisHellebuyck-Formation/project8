#!/usr/bin/env python3
"""
Script pour récupérer les logs via l'API Gradio sur HuggingFace Spaces.

Usage:
    python scripts/get_logs_gradio.py [--limit 50] [--hf-token TOKEN]
"""

import argparse
import json
import os
import sys

try:
    from gradio_client import Client
    GRADIO_CLIENT_AVAILABLE = True
except ImportError:
    GRADIO_CLIENT_AVAILABLE = False


def get_logs_via_gradio(gradio_url, limit=50, hf_token=None):
    """
    Récupère les logs via l'API Gradio.

    Args:
        gradio_url: URL de l'API Gradio
        limit: Nombre de logs à récupérer
        hf_token: Token HuggingFace pour accès aux Spaces privés

    Returns:
        dict: Résultat avec les logs
    """
    if not GRADIO_CLIENT_AVAILABLE:
        print("❌ gradio_client n'est pas installé.", file=sys.stderr)
        print("   Installez-le avec: pip install gradio-client", file=sys.stderr)
        sys.exit(1)

    try:
        # Créer le client Gradio
        client = Client(gradio_url, hf_token=hf_token)

        # Appeler l'endpoint /logs_api
        result = client.predict(
            limit=limit,
            api_name="/logs_api"
        )

        return result

    except Exception as e:
        print(f"❌ Erreur lors de la récupération des logs: {str(e)}", file=sys.stderr)
        sys.exit(1)


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description="Récupère les logs via l'API Gradio sur HuggingFace Spaces"
    )

    parser.add_argument(
        "--gradio-url",
        type=str,
        default="https://francoisformation-oc-project8.hf.space",
        help="URL de l'API Gradio (défaut: HF Space)"
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Nombre de logs à récupérer (défaut: 50)"
    )

    parser.add_argument(
        "--hf-token",
        type=str,
        default=None,
        help="Token HuggingFace pour accès aux Spaces privés"
    )

    args = parser.parse_args()

    # Charger le token depuis .env si disponible
    hf_token = args.hf_token
    if not hf_token:
        # Essayer de charger depuis .env
        env_file = os.path.join(os.path.dirname(__file__), "..", ".env")
        if os.path.exists(env_file):
            with open(env_file) as f:
                for line in f:
                    if line.startswith("HF_TOKEN="):
                        token_value = line.split("=", 1)[1].strip()
                        if token_value:
                            hf_token = token_value
                            break

    print(f"🔌 Connexion à Gradio: {args.gradio_url}")
    if hf_token:
        print("🔐 Token HuggingFace: Configuré")

    # Récupérer les logs
    result = get_logs_via_gradio(
        gradio_url=args.gradio_url,
        limit=args.limit,
        hf_token=hf_token
    )

    # Afficher le résultat formaté
    print("\n📋 Logs récupérés:")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
