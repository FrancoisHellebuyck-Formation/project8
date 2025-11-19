#!/usr/bin/env python3
"""
Script de démonstration du format JSON des métriques de performance.

Ce script montre comment les métriques sont formatées en JSON
lorsque le monitoring est activé.

Usage:
    ENABLE_PERFORMANCE_MONITORING=true python scripts/demo_performance_json.py
"""

import json
import logging
import os
import sys
from pathlib import Path

# Ajouter le répertoire racine au PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Activer le monitoring
os.environ['ENABLE_PERFORMANCE_MONITORING'] = 'true'

# Configuration du logging pour afficher en format lisible
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


def main():
    """Point d'entrée principal."""
    from src.model import ModelLoader, Predictor
    from src.api.performance_monitor import performance_monitor

    logger.info("=" * 70)
    logger.info("DÉMONSTRATION DU FORMAT JSON DES MÉTRIQUES DE PERFORMANCE")
    logger.info("=" * 70)
    logger.info("")

    # Charger le modèle
    logger.info("1. Chargement du modèle...")
    model_loader = ModelLoader()
    model_loader.load_model()
    predictor = Predictor()
    logger.info("   ✓ Modèle chargé")
    logger.info("")

    # Données de test
    patient_data = {
        'GENDER': 1,
        'AGE': 65,
        'SMOKING': 1,
        'YELLOW_FINGERS': 1,
        'ANXIETY': 0,
        'PEER_PRESSURE': 0,
        'CHRONIC DISEASE': 1,
        'FATIGUE': 1,
        'ALLERGY': 0,
        'WHEEZING': 1,
        'ALCOHOL CONSUMING': 0,
        'COUGHING': 1,
        'SHORTNESS OF BREATH': 1,
        'SWALLOWING DIFFICULTY': 0,
        'CHEST PAIN': 1
    }

    logger.info("2. Exécution d'une prédiction avec monitoring activé...")
    logger.info("")

    # Profiler la prédiction
    with performance_monitor.profile():
        prediction = predictor.predict(patient_data)

    # Récupérer les métriques
    metrics = performance_monitor.get_metrics()

    if metrics:
        logger.info("3. Format JSON des métriques de performance :")
        logger.info("-" * 70)

        # Créer le dictionnaire complet comme dans log_metrics
        metrics_dict = {
            'performance_metrics': {
                'inference_time_ms': round(metrics.inference_time_ms, 2),
                'cpu_time_ms': round(metrics.cpu_time_ms, 2),
                'memory_mb': round(metrics.memory_mb, 2),
                'memory_delta_mb': round(metrics.memory_delta_mb, 2),
                'function_calls': metrics.function_calls,
                'latency_ms': round(metrics.inference_time_ms, 2),
                'top_functions': [
                    {
                        'function': f['function'],
                        'file': f['file'],
                        'line': f['line'],
                        'cumulative_time_ms': round(
                            f['cumulative_time_ms'], 2
                        ),
                        'total_time_ms': round(f['total_time_ms'], 2),
                        'calls': f['calls']
                    }
                    for f in metrics.top_functions
                ]
            }
        }

        # Afficher en JSON formaté
        print(json.dumps(metrics_dict, indent=2, ensure_ascii=False))
        logger.info("-" * 70)
        logger.info("")

        # Résumé des métriques principales
        logger.info("4. Résumé des métriques principales :")
        logger.info("")
        logger.info(f"   • Prédiction : {prediction[0]}")
        logger.info(
            f"   • Temps d'inférence : "
            f"{metrics.inference_time_ms:.2f} ms"
        )
        logger.info(f"   • Temps CPU : {metrics.cpu_time_ms:.2f} ms")
        logger.info(f"   • Latence : {metrics.inference_time_ms:.2f} ms")
        logger.info(f"   • Mémoire utilisée : {metrics.memory_mb:.2f} MB")
        logger.info(
            f"   • Variation mémoire : {metrics.memory_delta_mb:+.2f} MB"
        )
        logger.info(f"   • Appels de fonction : {metrics.function_calls:,}")
        logger.info("")

        # Top 3 fonctions
        logger.info("5. Top 3 des fonctions les plus coûteuses :")
        logger.info("")
        for i, func in enumerate(metrics.top_functions[:3], 1):
            logger.info(
                f"   {i}. {func['function']} "
                f"({func['file']}:{func['line']})"
            )
            logger.info(
                f"      Temps cumulatif : "
                f"{func['cumulative_time_ms']:.2f} ms"
            )
            logger.info(
                f"      Temps propre : {func['total_time_ms']:.2f} ms"
            )
            logger.info(f"      Appels : {func['calls']}")
            logger.info("")

    logger.info("=" * 70)
    logger.info(
        "Ce format JSON est automatiquement envoyé au système de logs "
        "configuré"
    )
    logger.info("(Redis, Elasticsearch, ou stdout)")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
