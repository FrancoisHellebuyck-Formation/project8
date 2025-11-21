#!/usr/bin/env python3
"""
Script de lancement pour l'interface proxy Gradio.

Ce script lance l'interface proxy qui expose tous les endpoints
de l'API FastAPI via Gradio.

Usage:
    python run_proxy.py
    python run_proxy.py --port 7860
    python run_proxy.py --api-url http://localhost:8000
"""

import argparse
import sys

try:
    from src.proxy import launch_proxy
except ImportError:
    print("❌ Erreur: Le package proxy n'est pas installé")
    print("   Installez-le avec: uv sync")
    sys.exit(1)


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description="Lance l'interface proxy Gradio"
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default=None,
        help="URL de l'API FastAPI (défaut: depuis config)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=7860,
        help="Port du serveur Gradio (défaut: 7860)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Hôte du serveur Gradio (défaut: 0.0.0.0)"
    )
    parser.add_argument(
        "--share",
        action="store_true",
        help="Créer un lien public Gradio"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("🔄 Lancement du proxy Gradio")
    print("=" * 60)
    print()
    print(f"📍 Hôte: {args.host}")
    print(f"📍 Port: {args.port}")
    if args.api_url:
        print(f"🔗 API URL: {args.api_url}")
    if args.share:
        print("🌐 Partage public: activé")
    print()
    print("Pour accéder à l'interface:")
    print(f"  - Local: http://localhost:{args.port}")
    print(f"  - Réseau: http://{args.host}:{args.port}")
    print()
    print("Appuyez sur Ctrl+C pour arrêter")
    print("=" * 60)

    try:
        launch_proxy(
            api_url=args.api_url,
            server_name=args.host,
            server_port=args.port,
            share=args.share
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Arrêt du serveur proxy")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Erreur: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
