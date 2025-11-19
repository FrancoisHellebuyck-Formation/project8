#!/usr/bin/env python3
"""
Script pour tester le monitoring de performance.

Ce script teste le module de performance monitoring en mode activé
et désactivé pour vérifier son bon fonctionnement.

Usage:
    python scripts/test_performance_monitoring.py
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


def test_monitoring_disabled():
    """Test avec monitoring désactivé."""
    logger.info("\n" + "=" * 60)
    logger.info("Test 1: Monitoring DÉSACTIVÉ")
    logger.info("=" * 60)

    # Forcer la désactivation
    import os
    os.environ['ENABLE_PERFORMANCE_MONITORING'] = 'false'

    # Recharger la config et le monitor
    from importlib import reload
    from src import config
    reload(config)
    from src.api import performance_monitor
    reload(performance_monitor)

    monitor = performance_monitor.PerformanceMonitor()

    logger.info(f"  Monitoring activé: {monitor.enabled}")

    # Simuler une opération
    with monitor.profile():
        # Opération factice
        result = sum(range(1000000))
        logger.info(f"  Résultat calculé: {result}")

    # Récupérer les métriques
    metrics = monitor.get_metrics()

    if metrics is None:
        logger.info("  ✓ Aucune métrique collectée (attendu)")
    else:
        logger.error("  ✗ Des métriques ont été collectées (inattendu)")
        return False

    logger.info("  ✓ Test réussi: monitoring désactivé fonctionne")
    return True


def test_monitoring_enabled():
    """Test avec monitoring activé."""
    logger.info("\n" + "=" * 60)
    logger.info("Test 2: Monitoring ACTIVÉ")
    logger.info("=" * 60)

    # Forcer l'activation
    import os
    os.environ['ENABLE_PERFORMANCE_MONITORING'] = 'true'

    # Recharger la config et le monitor
    from importlib import reload
    from src import config
    reload(config)
    from src.api import performance_monitor
    reload(performance_monitor)

    monitor = performance_monitor.PerformanceMonitor()

    logger.info(f"  Monitoring activé: {monitor.enabled}")

    # Simuler une opération
    with monitor.profile():
        # Opération factice plus complexe
        result = 0
        for i in range(1000):
            result += sum(range(1000))
        logger.info(f"  Résultat calculé: {result}")

    # Récupérer les métriques
    metrics = monitor.get_metrics()

    if metrics is None:
        logger.error("  ✗ Aucune métrique collectée (inattendu)")
        return False

    logger.info("  ✓ Métriques collectées:")
    logger.info(f"    - Temps d'inférence: {metrics.inference_time_ms:.2f}ms")
    logger.info(f"    - CPU time: {metrics.cpu_time_ms:.2f}ms")
    logger.info(f"    - Mémoire: {metrics.memory_mb:.2f}MB")
    logger.info(
        f"    - Delta mémoire: {metrics.memory_delta_mb:+.2f}MB"
    )
    logger.info(f"    - Appels de fonction: {metrics.function_calls}")

    # Vérifier que les métriques ont des valeurs raisonnables
    checks = {
        "inference_time_ms > 0": metrics.inference_time_ms > 0,
        "cpu_time_ms > 0": metrics.cpu_time_ms > 0,
        "memory_mb > 0": metrics.memory_mb > 0,
        "function_calls > 0": metrics.function_calls > 0,
    }

    all_ok = True
    for check, result in checks.items():
        status = "✓" if result else "✗"
        logger.info(f"    {status} {check}")
        if not result:
            all_ok = False

    # Logger les métriques
    monitor.log_metrics(metrics)

    # Formater en dict
    perf_dict = monitor.format_metrics_dict(metrics)
    logger.info(f"\n  Métriques formatées: {perf_dict}")

    if all_ok:
        logger.info("  ✓ Test réussi: monitoring activé fonctionne")
    else:
        logger.error("  ✗ Test échoué: certaines métriques invalides")

    return all_ok


def test_with_model_prediction():
    """Test avec une vraie prédiction de modèle."""
    logger.info("\n" + "=" * 60)
    logger.info("Test 3: Monitoring avec prédiction réelle")
    logger.info("=" * 60)

    # Forcer l'activation
    import os
    os.environ['ENABLE_PERFORMANCE_MONITORING'] = 'true'

    # Recharger la config et le monitor
    from importlib import reload
    from src import config
    reload(config)
    from src.api import performance_monitor
    reload(performance_monitor)

    try:
        from src.model import ModelLoader, Predictor

        # Charger le modèle
        logger.info("  Chargement du modèle...")
        model_loader = ModelLoader()
        model_loader.load_model()
        predictor = Predictor()
        logger.info("  ✓ Modèle chargé")

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

        monitor = performance_monitor.PerformanceMonitor()

        # Profiler la prédiction
        with monitor.profile():
            prediction = predictor.predict(patient_data)
            logger.info(f"  Prédiction: {prediction[0]}")

        # Récupérer les métriques
        metrics = monitor.get_metrics()

        if metrics:
            logger.info("\n  Métriques de prédiction:")
            logger.info(
                f"    - Temps d'inférence: {metrics.inference_time_ms:.2f}ms"
            )
            logger.info(f"    - CPU time: {metrics.cpu_time_ms:.2f}ms")
            logger.info(f"    - Mémoire: {metrics.memory_mb:.2f}MB")
            logger.info(
                f"    - Delta mémoire: {metrics.memory_delta_mb:+.2f}MB"
            )
            logger.info(f"    - Appels de fonction: {metrics.function_calls}")

            if metrics.top_functions:
                logger.info("\n  Top 3 fonctions:")
                for i, func in enumerate(metrics.top_functions[:3], 1):
                    logger.info(
                        f"    {i}. {func['function']} - "
                        f"{func['cumulative_time_ms']:.2f}ms "
                        f"({func['calls']} appels)"
                    )

            logger.info("  ✓ Test réussi: prédiction profilée")
            return True
        else:
            logger.error("  ✗ Aucune métrique collectée")
            return False

    except Exception as e:
        logger.error(f"  ✗ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Point d'entrée principal."""
    logger.info("=" * 60)
    logger.info("Tests du Performance Monitoring")
    logger.info("=" * 60)

    results = []

    # Test 1: Monitoring désactivé
    results.append(("Monitoring désactivé", test_monitoring_disabled()))

    # Test 2: Monitoring activé
    results.append(("Monitoring activé", test_monitoring_enabled()))

    # Test 3: Prédiction réelle
    results.append(("Prédiction réelle", test_with_model_prediction()))

    # Résumé
    logger.info("\n" + "=" * 60)
    logger.info("Résumé des tests")
    logger.info("=" * 60)

    all_passed = True
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"  {status}: {test_name}")
        if not result:
            all_passed = False

    logger.info("=" * 60)

    if all_passed:
        logger.info("✓ SUCCÈS: Tous les tests sont passés")
        sys.exit(0)
    else:
        logger.error("✗ ÉCHEC: Certains tests ont échoué")
        sys.exit(1)


if __name__ == "__main__":
    main()
