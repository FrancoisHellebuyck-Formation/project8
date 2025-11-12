"""
Script pour analyser le data drift généré par le simulateur.

Ce script permet de visualiser comment l'âge des patients évolue
au cours d'une simulation avec data drift activé.
"""

import random
from typing import List


def analyze_age_drift(
    num_requests: int = 200,
    enable_drift: bool = True,
    target_mean: float = 75.0,
    drift_start_pct: float = 0.0,
    drift_end_pct: float = 100.0
) -> List[int]:
    """
    Génère une série d'âges simulant le drift.

    Args:
        num_requests: Nombre de requêtes à simuler.
        enable_drift: Si True, active le drift.
        target_mean: Âge moyen cible du drift.
        drift_start_pct: Début du drift en %.
        drift_end_pct: Fin du drift en %.

    Returns:
        Liste des âges générés.
    """
    ages = []

    for request_count in range(1, num_requests + 1):
        if not enable_drift:
            age = random.randint(20, 90)
        else:
            progress_pct = (request_count / num_requests) * 100

            if progress_pct < drift_start_pct:
                age = random.randint(20, 90)
            elif progress_pct >= drift_end_pct:
                age = int(random.gauss(target_mean, 10))
                age = max(20, min(90, age))
            else:
                drift_progress = (
                    (progress_pct - drift_start_pct) /
                    (drift_end_pct - drift_start_pct)
                )

                if random.random() < drift_progress:
                    age = int(random.gauss(target_mean, 10))
                    age = max(20, min(90, age))
                else:
                    age = random.randint(20, 90)

        ages.append(age)

    return ages


def print_age_statistics(ages: List[int], window_size: int = 20):
    """
    Affiche les statistiques d'âge par fenêtre.

    Args:
        ages: Liste des âges.
        window_size: Taille de la fenêtre glissante.
    """
    print("\n📊 Statistiques d'âge par fenêtre:\n")
    print(f"{'Requêtes':>15} | {'Âge moyen':>10} | "
          f"{'Min':>5} | {'Max':>5} | {'Écart-type':>10}")
    print("-" * 60)

    num_windows = len(ages) // window_size
    for i in range(num_windows):
        start_idx = i * window_size
        end_idx = start_idx + window_size
        window_ages = ages[start_idx:end_idx]

        avg_age = sum(window_ages) / len(window_ages)
        min_age = min(window_ages)
        max_age = max(window_ages)

        # Calcul de l'écart-type
        variance = sum((x - avg_age) ** 2 for x in window_ages) / len(window_ages)  # noqa: E501
        std_dev = variance ** 0.5

        print(
            f"{start_idx + 1:>6}-{end_idx:>6} | "
            f"{avg_age:>10.1f} | "
            f"{min_age:>5} | "
            f"{max_age:>5} | "
            f"{std_dev:>10.1f}"
        )


def main():
    """Point d'entrée principal."""
    print("=" * 60)
    print("  ANALYSEUR DE DATA DRIFT - SIMULATEUR ML")
    print("=" * 60)

    # Simulation sans drift
    print("\n🔷 Simulation SANS drift (baseline):")
    ages_no_drift = analyze_age_drift(
        num_requests=200,
        enable_drift=False
    )
    print_age_statistics(ages_no_drift)

    # Simulation avec drift immédiat
    print("\n\n🔶 Simulation AVEC drift immédiat (0% → 100%):")
    ages_immediate_drift = analyze_age_drift(
        num_requests=200,
        enable_drift=True,
        target_mean=75.0,
        drift_start_pct=0.0,
        drift_end_pct=100.0
    )
    print_age_statistics(ages_immediate_drift)

    # Simulation avec drift progressif
    print("\n\n🔴 Simulation AVEC drift progressif (50% → 100%):")
    ages_progressive_drift = analyze_age_drift(
        num_requests=200,
        enable_drift=True,
        target_mean=75.0,
        drift_start_pct=50.0,
        drift_end_pct=100.0
    )
    print_age_statistics(ages_progressive_drift)

    print("\n" + "=" * 60)
    print("✅ Analyse terminée!")
    print()


if __name__ == "__main__":
    main()
