#!/usr/bin/env python3
"""
Script de démonstration : logs de performance dans Redis.

Ce script montre que les logs de métriques de performance sont bien
envoyés vers Redis lorsque le monitoring est activé et que Redis
est configuré comme handler de logs.

Usage:
    # Assurez-vous que Redis tourne (docker-compose up redis)
    LOGGING_HANDLER=redis ENABLE_PERFORMANCE_MONITORING=true \
        python scripts/demo_redis_performance_logs.py
"""

import json
import logging
import os
import sys
from pathlib import Path

# Ajouter le répertoire racine au PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Configuration
os.environ['LOGGING_HANDLER'] = 'redis'
os.environ['ENABLE_PERFORMANCE_MONITORING'] = 'true'

# Configuration du logging console
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


def main():
    """Point d'entrée principal."""
    import redis
    from src.config import settings
    from src.model import ModelLoader, Predictor
    from src.api.performance_monitor import performance_monitor
    from src.api.logging_config import setup_logging

    logger.info("=" * 70)
    logger.info(
        "DÉMONSTRATION : LOGS DE PERFORMANCE DANS REDIS"
    )
    logger.info("=" * 70)
    logger.info("")

    # Vérifier la connexion Redis
    logger.info("1. Vérification de la connexion Redis...")
    try:
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        redis_client.ping()
        logger.info(
            f"   ✓ Redis connecté sur "
            f"{settings.REDIS_HOST}:{settings.REDIS_PORT}"
        )
    except redis.ConnectionError:
        logger.error(
            "   ✗ Impossible de se connecter à Redis. "
            "Assurez-vous que Redis tourne."
        )
        logger.error(
            "     Commande : docker-compose up -d redis"
        )
        sys.exit(1)
    logger.info("")

    # Configurer le logging avec Redis
    logger.info("2. Configuration du logging avec Redis...")
    setup_logging(redis_client=redis_client)
    logger.info("   ✓ Logging configuré (handler Redis)")
    logger.info("")

    # Vider les logs existants
    logger.info("3. Vidage des logs Redis existants...")
    redis_client.delete(settings.REDIS_LOGS_KEY)
    logger.info(f"   ✓ Clé '{settings.REDIS_LOGS_KEY}' vidée")
    logger.info("")

    # Charger le modèle
    logger.info("4. Chargement du modèle ML...")
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

    # Faire une prédiction avec monitoring
    logger.info(
        "5. Exécution d'une prédiction avec monitoring activé..."
    )
    logger.info("")

    with performance_monitor.profile():
        prediction = predictor.predict(patient_data)

    metrics = performance_monitor.get_metrics()
    if metrics:
        performance_monitor.log_metrics(metrics)
        logger.info(f"   ✓ Prédiction : {prediction[0]}")
        logger.info(
            f"   ✓ Métriques loggées "
            f"(inference: {metrics.inference_time_ms:.2f}ms)"
        )
    logger.info("")

    # Récupérer les logs de Redis
    logger.info("6. Récupération des logs depuis Redis...")
    logs = redis_client.lrange(settings.REDIS_LOGS_KEY, 0, -1)
    logger.info(f"   ✓ {len(logs)} logs trouvés dans Redis")
    logger.info("")

    # Chercher le log de performance
    logger.info("7. Recherche du log de métriques de performance...")
    performance_log_found = False

    for i, log in enumerate(logs, 1):
        if "performance_metrics" in log:
            performance_log_found = True
            logger.info(f"   ✓ Log de performance trouvé (log #{i})")
            logger.info("")

            # Parser et afficher le JSON
            try:
                # Format: timestamp - name - level - message
                log_parts = log.split(" - ", 3)
                if len(log_parts) >= 4:
                    json_data = json.loads(log_parts[3])
                    logger.info("   📊 Contenu du log (JSON formaté) :")
                    logger.info("")
                    print(json.dumps(json_data, indent=2, ensure_ascii=False))
                    logger.info("")

                    # Résumé
                    perf = json_data.get("performance_metrics", {})
                    logger.info("   📈 Résumé des métriques :")
                    logger.info(
                        f"      • Temps d'inférence : "
                        f"{perf.get('inference_time_ms', 0):.2f} ms"
                    )
                    logger.info(
                        f"      • Temps CPU        : "
                        f"{perf.get('cpu_time_ms', 0):.2f} ms"
                    )
                    logger.info(
                        f"      • Latence          : "
                        f"{perf.get('latency_ms', 0):.2f} ms"
                    )
                    logger.info(
                        f"      • Mémoire          : "
                        f"{perf.get('memory_mb', 0):.2f} MB"
                    )
                    logger.info(
                        f"      • Delta mémoire    : "
                        f"{perf.get('memory_delta_mb', 0):+.2f} MB"
                    )
                    logger.info(
                        f"      • Appels fonction  : "
                        f"{perf.get('function_calls', 0):,}"
                    )
            except json.JSONDecodeError:
                logger.warning("   ⚠ Impossible de parser le JSON")

            break

    logger.info("")

    if not performance_log_found:
        logger.warning(
            "   ⚠ Aucun log de performance trouvé dans Redis !"
        )
        logger.warning(
            "     Vérifiez que ENABLE_PERFORMANCE_MONITORING=true"
        )
        logger.info("")
        logger.info("   Logs présents dans Redis :")
        for i, log in enumerate(logs[:5], 1):
            logger.info(f"     {i}. {log[:80]}...")

    logger.info("=" * 70)
    logger.info("CONCLUSION:")
    logger.info("")
    if performance_log_found:
        logger.info(
            "✅ Les logs de métriques de performance sont bien envoyés "
            "vers Redis !"
        )
        logger.info(
            "   Ils utilisent le même système de logging que "
            "les autres logs de l'API."
        )
    else:
        logger.info("❌ Problème de configuration détecté.")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
