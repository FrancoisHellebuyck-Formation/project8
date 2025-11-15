"""
Script CLI pour exécuter le simulateur d'utilisateurs.

Usage:
    python -m src.simulator --requests 100 --users 10
    python -m src.simulator --help
"""

import argparse
import sys

from ..config import settings
from .simulator import SimulationConfig, UserSimulator


def main():
    """Point d'entrée principal du simulateur."""
    parser = argparse.ArgumentParser(
        description="Simulateur d'utilisateurs pour l'API de prédiction",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  # Simulation simple avec 100 requêtes et 10 utilisateurs (FastAPI)
  python -m src.simulator --requests 100 --users 10

  # Simulation via Gradio API en local
  python -m src.simulator --use-gradio --gradio-url http://localhost:7860 -r 100 -u 10

  # Simulation via HuggingFace Spaces (Space public)
  python -m src.simulator --use-gradio --gradio-url https://francoisformation-oc-project8.hf.space -r 50 -u 5

  # Simulation via HuggingFace Spaces (Space privé avec token)
  python -m src.simulator --use-gradio --gradio-url https://francoisformation-oc-project8.hf.space --hf-token hf_xxx -r 50 -u 5

  # Simulation avec API distante et verbose (FastAPI)
  python -m src.simulator --url http://api.example.com:8000 --requests 50 -v

  # Test de charge avec 1000 requêtes et 50 utilisateurs
  python -m src.simulator -r 1000 -u 50 --delay 0.1

  # Test de l'endpoint predict_proba
  python -m src.simulator --endpoint /predict_proba -r 200 -u 20

  # Simulation avec data drift sur l'âge (vers 70 ans)
  python -m src.simulator -r 200 -u 10 --enable-age-drift --age-drift-target 70

  # Drift progressif entre 20% et 80% de la simulation
  python -m src.simulator -r 500 -u 20 --enable-age-drift \\
      --age-drift-target 75 --age-drift-start 20 --age-drift-end 80
        """,
    )

    # Mode de simulation
    parser.add_argument(
        "--use-gradio",
        action="store_true",
        default=False,
        help="Utilise l'API Gradio au lieu de l'API FastAPI directe",
    )

    parser.add_argument(
        "--gradio-url",
        type=str,
        default=None,
        help="URL Gradio (défaut: http://localhost:7860 si --use-gradio)",
    )

    parser.add_argument(
        "--hf-token",
        type=str,
        default=None,
        help="Token HuggingFace pour accès aux Spaces privés",
    )

    parser.add_argument(
        "--url",
        type=str,
        default=settings.SIMULATOR_API_URL,
        help=f"URL de base de l'API FastAPI (défaut: {settings.SIMULATOR_API_URL})",
    )

    parser.add_argument(
        "-r",
        "--requests",
        type=int,
        default=settings.SIMULATOR_NUM_REQUESTS,
        help=f"Nombre total de requêtes à envoyer "
        f"(défaut: {settings.SIMULATOR_NUM_REQUESTS})",
    )

    parser.add_argument(
        "-u",
        "--users",
        type=int,
        default=settings.SIMULATOR_CONCURRENT_USERS,
        help=f"Nombre d'utilisateurs concurrents "
        f"(défaut: {settings.SIMULATOR_CONCURRENT_USERS})",
    )

    parser.add_argument(
        "-d",
        "--delay",
        type=float,
        default=settings.SIMULATOR_DELAY,
        help=f"Délai en secondes entre chaque requête "
        f"(défaut: {settings.SIMULATOR_DELAY})",
    )

    parser.add_argument(
        "-t",
        "--timeout",
        type=float,
        default=settings.SIMULATOR_TIMEOUT,
        help=f"Timeout en secondes pour chaque requête "
        f"(défaut: {settings.SIMULATOR_TIMEOUT})",
    )

    parser.add_argument(
        "-e",
        "--endpoint",
        type=str,
        default=settings.SIMULATOR_ENDPOINT,
        choices=["/predict", "/predict_proba"],
        help=f"Endpoint à tester (défaut: {settings.SIMULATOR_ENDPOINT})",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=settings.SIMULATOR_VERBOSE,
        help=f"Mode verbose - affiche les détails de chaque requête "
        f"(défaut: {settings.SIMULATOR_VERBOSE})",
    )

    # Options de data drift
    parser.add_argument(
        "--enable-age-drift",
        action="store_true",
        default=settings.SIMULATOR_ENABLE_AGE_DRIFT,
        help=f"Active le data drift sur l'âge des patients "
        f"(défaut: {settings.SIMULATOR_ENABLE_AGE_DRIFT})",
    )

    parser.add_argument(
        "--age-drift-target",
        type=float,
        default=settings.SIMULATOR_AGE_DRIFT_TARGET,
        help=f"Âge moyen cible pour le drift "
        f"(défaut: {settings.SIMULATOR_AGE_DRIFT_TARGET})",
    )

    parser.add_argument(
        "--age-drift-start",
        type=float,
        default=settings.SIMULATOR_AGE_DRIFT_START,
        help=f"Début du drift en pourcentage "
        f"(défaut: {settings.SIMULATOR_AGE_DRIFT_START})",
    )

    parser.add_argument(
        "--age-drift-end",
        type=float,
        default=settings.SIMULATOR_AGE_DRIFT_END,
        help=f"Fin du drift en pourcentage "
        f"(défaut: {settings.SIMULATOR_AGE_DRIFT_END})",
    )

    args = parser.parse_args()

    # Validation des paramètres
    if args.requests <= 0:
        print("❌ Erreur: le nombre de requêtes doit être > 0")
        sys.exit(1)

    if args.users <= 0:
        print("❌ Erreur: le nombre d'utilisateurs doit être > 0")
        sys.exit(1)

    if args.delay < 0:
        print("❌ Erreur: le délai doit être >= 0")
        sys.exit(1)

    if args.timeout <= 0:
        print("❌ Erreur: le timeout doit être > 0")
        sys.exit(1)

    # Validation des paramètres de drift
    if args.enable_age_drift:
        if args.age_drift_target < 20 or args.age_drift_target > 90:
            print("❌ Erreur: l'âge cible doit être entre 20 et 90")
            sys.exit(1)

        if args.age_drift_start < 0 or args.age_drift_start > 100:
            print("❌ Erreur: le début du drift doit être entre 0 et 100")
            sys.exit(1)

        if args.age_drift_end < 0 or args.age_drift_end > 100:
            print("❌ Erreur: la fin du drift doit être entre 0 et 100")
            sys.exit(1)

        if args.age_drift_start >= args.age_drift_end:
            print("❌ Erreur: le début du drift doit être < à la fin")
            sys.exit(1)

    # Créer la configuration
    config = SimulationConfig(
        api_url=args.url,
        num_requests=args.requests,
        concurrent_users=args.users,
        delay_between_requests=args.delay,
        timeout=args.timeout,
        endpoint=args.endpoint,
        verbose=args.verbose,
        use_gradio=args.use_gradio,
        gradio_url=args.gradio_url,
        hf_token=args.hf_token,
        enable_age_drift=args.enable_age_drift,
        age_drift_target_mean=args.age_drift_target,
        age_drift_start_pct=args.age_drift_start,
        age_drift_end_pct=args.age_drift_end,
    )

    # Afficher la configuration
    print("\n" + "=" * 60)
    print("  SIMULATEUR D'UTILISATEURS - API DE PRÉDICTION ML")
    print("=" * 60)

    # Afficher le mode de simulation
    if args.use_gradio:
        gradio_url = args.gradio_url or "http://localhost:7860"
        print(f"\n🔌 Mode: Gradio API ({gradio_url})")
        if args.hf_token:
            print("🔐 Token HuggingFace: Configuré")
    else:
        print(f"\n🔌 Mode: FastAPI directe ({args.url})")

    # Afficher un avertissement si le drift est activé
    if args.enable_age_drift:
        print("\n⚠️  DATA DRIFT ACTIVÉ sur l'âge des patients:")
        print(f"   Âge cible: {args.age_drift_target:.0f} ans")
        print(
            f"   Période: {args.age_drift_start:.0f}% - "
            f"{args.age_drift_end:.0f}% de la simulation"
        )
        print()

    # Lancer la simulation
    try:
        simulator = UserSimulator(config)
        result = simulator.run()

        # Afficher les résultats
        print("\n")
        print(result)
        print()

        # Code de sortie basé sur le taux de succès
        success_rate = (
            result.successful_requests / result.total_requests * 100
        )
        if success_rate == 100:
            print("✅ Simulation terminée avec succès!")
            sys.exit(0)
        elif success_rate >= 90:
            print(
                f"⚠️  Simulation terminée avec {success_rate:.1f}% de succès"
            )
            sys.exit(0)
        else:
            print(
                f"❌ Simulation terminée avec seulement "
                f"{success_rate:.1f}% de succès"
            )
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Simulation interrompue par l'utilisateur")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Erreur lors de la simulation: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
