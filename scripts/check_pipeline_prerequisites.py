#!/usr/bin/env python3
"""
Script pour vérifier les pré-requis du pipeline de logs.

Usage:
    python scripts/check_pipeline_prerequisites.py
"""

import logging
import sys
from pathlib import Path

# Ajouter le répertoire racine au PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

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
    from src.logs_pipeline import LogsPipeline

    logger.info("=" * 60)
    logger.info("Vérification des pré-requis du pipeline de logs")
    logger.info("=" * 60)

    pipeline = LogsPipeline()
    result = pipeline.check_prerequisites()

    logger.info("=" * 60)
    if result:
        logger.info("✓ SUCCÈS: Tous les pré-requis sont satisfaits")
        logger.info("  Vous pouvez lancer le pipeline avec:")
        logger.info("  - make pipeline-once")
        logger.info("  - make pipeline-continuous")
    else:
        logger.error("✗ ÉCHEC: Certains pré-requis ne sont pas satisfaits")
        logger.error("  Consultez les messages ci-dessus pour plus de détails")

    logger.info("=" * 60)

    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
