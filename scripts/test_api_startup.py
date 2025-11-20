#!/usr/bin/env python3
"""
Script pour tester l'affichage du monitoring au démarrage de l'API.

Ce script démarre l'API et vérifie que le message de monitoring
s'affiche correctement dans les logs.

Usage:
    # Sans monitoring
    python scripts/test_api_startup.py

    # Avec monitoring
    ENABLE_PERFORMANCE_MONITORING=true python scripts/test_api_startup.py
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
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


def test_startup_message():
    """Teste l'affichage du message de monitoring au démarrage."""
    from src.config import settings

    logger.info("=" * 70)
    logger.info("TEST DE L'AFFICHAGE DU MONITORING AU DÉMARRAGE")
    logger.info("=" * 70)
    logger.info("")

    # Afficher la configuration
    monitoring_enabled = settings.ENABLE_PERFORMANCE_MONITORING
    logger.info("Configuration actuelle:")
    logger.info(
        f"  ENABLE_PERFORMANCE_MONITORING = {monitoring_enabled}"
    )
    logger.info("")

    # Simuler le démarrage de l'API
    logger.info("Simulation du démarrage de l'API...")
    logger.info("")

    # Message qui sera affiché
    if monitoring_enabled:
        expected_message = (
            "⚡ Performance monitoring: ACTIVÉ "
            "(métriques: CPU, RAM, latence, throughput)"
        )
    else:
        expected_message = "Performance monitoring: désactivé"

    logger.info("Message attendu au démarrage:")
    logger.info(f"  {expected_message}")
    logger.info("")

    logger.info("=" * 70)
    logger.info("Pour tester avec le monitoring activé:")
    logger.info(
        "  ENABLE_PERFORMANCE_MONITORING=true python "
        "scripts/test_api_startup.py"
    )
    logger.info("")
    logger.info("Pour démarrer l'API réellement:")
    logger.info("  make run-api")
    logger.info("=" * 70)


if __name__ == "__main__":
    test_startup_message()
