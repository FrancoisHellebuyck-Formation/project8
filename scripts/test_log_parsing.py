#!/usr/bin/env python3
"""
Script pour tester le parsing des logs.

Usage:
    python scripts/test_log_parsing.py
"""

import json
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
    from src.logs_pipeline.collector import LogCollector

    logger.info("=" * 60)
    logger.info("Test de parsing des logs")
    logger.info("=" * 60)

    # Log brut exemple fourni par l'utilisateur
    log_example = {
        "timestamp": "2025-11-18 16:55:02",
        "level": "INFO",
        "message": '[9dfbccba-d03c-4afc-99f1-6f465296d5ce] API Call - POST /predict - Status: 200 - Time: 15.98ms - Input: {"AGE": 74, "GENDER": 1, "SMOKING": 1, "ALCOHOL CONSUMING": 0, "PEER_PRESSURE": 0, "YELLOW_FINGERS": 0, "ANXIETY": 0, "FATIGUE": 1, "ALLERGY": 0, "WHEEZING": 0, "COUGHING": 1, "SHORTNESS OF BREATH": 1, "SWALLOWING DIFFICULTY": 1, "CHEST PAIN": 0, "CHRONIC DISEASE": 1} - Result: {"prediction": 1, "probability": 0.8120028604459375, "message": "Prédiction positive"}',  # noqa: E501
        "data": None
    }

    logger.info("\nLog brut:")
    logger.info(json.dumps(log_example, indent=2, ensure_ascii=False))

    # Créer un collecteur (juste pour utiliser la méthode de parsing)
    collector = LogCollector()

    # Simuler le traitement du log
    document = {
        '@timestamp': '2025-11-18T16:55:02Z',
        'level': log_example['level'],
        'message': log_example['message'],
    }

    # Parser le message
    collector._extract_additional_fields(document, log_example['message'])

    logger.info("\n" + "=" * 60)
    logger.info("Document parsé:")
    logger.info("=" * 60)
    logger.info(json.dumps(document, indent=2, ensure_ascii=False))

    # Vérifications
    logger.info("\n" + "=" * 60)
    logger.info("Vérifications:")
    logger.info("=" * 60)

    checks = {
        "transaction_id": document.get('transaction_id') == '9dfbccba-d03c-4afc-99f1-6f465296d5ce',  # noqa: E501
        "http_method": document.get('http_method') == 'POST',
        "http_path": document.get('http_path') == '/predict',
        "status_code": document.get('status_code') == 200,
        "execution_time_ms": document.get('execution_time_ms') == 15.98,
        "input_data présent": document.get('input_data') is not None,
        "result présent": document.get('result') is not None,
    }

    all_ok = True
    for check, result in checks.items():
        status = "✓" if result else "✗"
        logger.info(f"{status} {check}: {result}")
        if not result:
            all_ok = False

    # Vérifier les champs de input_data
    if document.get('input_data'):
        logger.info("\n  Champs input_data:")
        input_data = document['input_data']
        expected_fields = [
            'AGE', 'GENDER', 'SMOKING', 'ALCOHOL', 'PEER_PRESSURE',
            'YELLOW_FINGERS', 'ANXIETY', 'FATIGUE', 'ALLERGY',
            'WHEEZING', 'COUGHING', 'SHORTNESS_OF_BREATH',
            'SWALLOWING_DIFFICULTY', 'CHEST_PAIN', 'CHRONIC_DISEASE'
        ]
        for field in expected_fields:
            if field in input_data:
                logger.info(f"  ✓ {field}: {input_data[field]}")
            else:
                logger.info(f"  ✗ {field}: MANQUANT")
                all_ok = False

    # Vérifier les champs de result
    if document.get('result'):
        logger.info("\n  Champs result:")
        result = document['result']
        if 'prediction' in result:
            logger.info(f"  ✓ prediction: {result['prediction']}")
        else:
            logger.info("  ✗ prediction: MANQUANT")
            all_ok = False
        if 'probability' in result:
            logger.info(f"  ✓ probability: {result['probability']}")
        else:
            logger.info("  ✗ probability: MANQUANT")
            all_ok = False
        if 'message' in result:
            logger.info(f"  ✓ message: {result['message']}")
        else:
            logger.info("  ✗ message: MANQUANT")
            all_ok = False

    logger.info("\n" + "=" * 60)
    if all_ok:
        logger.info("✓ SUCCÈS: Le parsing fonctionne correctement")
    else:
        logger.error("✗ ÉCHEC: Certains champs n'ont pas été parsés")
    logger.info("=" * 60)

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
