#!/usr/bin/env python3
"""
Point d'entrée CLI pour le pipeline de logs.

Usage:
    python -m src.logs_pipeline [--once] [--limit 100]
    python -m src.logs_pipeline --continuous [--interval 10]
"""

import argparse
import logging
import sys

from .pipeline import LogsPipeline

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description="Pipeline d'intégration des logs dans Elasticsearch"
    )

    parser.add_argument(
        "--once",
        action="store_true",
        help="Exécuter le pipeline une seule fois (défaut: continu)"
    )

    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Exécuter le pipeline en continu"
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Nombre maximum de logs à récupérer (défaut: tous, max 1000)"
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=10,
        help="Intervalle entre chaque exécution en secondes (défaut: 10)"
    )

    parser.add_argument(
        "--gradio-url",
        type=str,
        default=None,
        help="URL de l'API Gradio (défaut: depuis .env)"
    )

    parser.add_argument(
        "--hf-token",
        type=str,
        default=None,
        help="Token HuggingFace (défaut: depuis .env)"
    )

    args = parser.parse_args()

    # Créer le pipeline
    logger.info("Initialisation du pipeline...")
    pipeline = LogsPipeline(
        gradio_url=args.gradio_url,
        hf_token=args.hf_token
    )

    # Exécuter selon le mode
    if args.once:
        logger.info("Mode: Exécution unique")
        stats = pipeline.run_once(limit=args.limit)
        logger.info(f"Résultat: {stats}")
    else:
        logger.info("Mode: Exécution continue")
        pipeline.run_continuous(
            limit=args.limit,
            poll_interval=args.interval
        )


if __name__ == "__main__":
    main()
