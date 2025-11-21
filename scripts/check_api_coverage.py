#!/usr/bin/env python3
"""
Script pour vérifier la couverture de tests de l'API.

Ce script est conçu pour être utilisé:
1. En pre-commit hook pour bloquer les commits avec couverture insuffisante
2. En CI/CD pour valider les PRs
3. Manuellement pour vérifier la couverture avant un commit

Usage:
    python scripts/check_api_coverage.py [--min-coverage 85]

Exit codes:
    0: Couverture suffisante
    1: Couverture insuffisante ou erreur
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Tuple


def run_coverage_tests(min_coverage: int = 85) -> Tuple[bool, Dict]:
    """
    Exécute les tests de l'API avec couverture.

    Args:
        min_coverage: Pourcentage minimum de couverture requis

    Returns:
        Tuple (success: bool, coverage_data: dict)
    """
    print("=" * 60)
    print("🧪 Exécution des tests API avec couverture...")
    print("=" * 60)

    # Exécuter pytest avec couverture
    cmd = [
        "uv", "run", "pytest",
        "tests/api/",
        "-v",
        "--cov=src/api",
        "--cov-report=json:coverage-api.json",
        "--cov-report=term-missing",
        f"--cov-fail-under={min_coverage}"
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=False,
            text=True
        )

        # Lire le fichier de couverture JSON
        coverage_file = Path("coverage-api.json")
        if not coverage_file.exists():
            print("❌ Fichier de couverture non trouvé")
            return False, {}

        with open(coverage_file) as f:
            coverage_data = json.load(f)

        success = result.returncode == 0
        return success, coverage_data

    except Exception as e:
        print(f"❌ Erreur lors de l'exécution des tests: {e}")
        return False, {}


def display_coverage_summary(coverage_data: Dict, min_coverage: int):
    """
    Affiche un résumé de la couverture.

    Args:
        coverage_data: Données de couverture depuis coverage.json
        min_coverage: Seuil minimum de couverture
    """
    if not coverage_data:
        return

    total = coverage_data['totals']['percent_covered']

    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DE LA COUVERTURE API")
    print("=" * 60)
    print(f"Couverture totale: {total:.2f}%")
    print(f"Seuil minimum:     {min_coverage}%")

    if total >= min_coverage:
        print("✅ SUCCÈS - Couverture supérieure au seuil")
    else:
        print(f"❌ ÉCHEC - Couverture insuffisante ({total:.2f}% < "
              f"{min_coverage}%)")

    print("\nDétail par fichier:")
    print("-" * 60)

    # Trier par couverture croissante
    files_coverage = []
    for file, stats in coverage_data['files'].items():
        if 'src/api' in file:
            pct = stats['summary']['percent_covered']
            files_coverage.append((file, pct))

    files_coverage.sort(key=lambda x: x[1])

    for file, pct in files_coverage:
        filename = file.replace('src/api/', '')
        status = "✅" if pct >= min_coverage else "⚠️ "
        print(f"  {status} {filename:40s} {pct:6.2f}%")

    print("=" * 60)

    # Afficher les fichiers avec faible couverture
    low_coverage = [(f, p) for f, p in files_coverage if p < min_coverage]
    if low_coverage:
        print("\n⚠️  FICHIERS AVEC COUVERTURE INSUFFISANTE:")
        print("-" * 60)
        for file, pct in low_coverage:
            filename = file.replace('src/api/', '')
            missing = min_coverage - pct
            print(f"  • {filename}: {pct:.2f}% (manque {missing:.2f}%)")
        print("-" * 60)


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description="Vérifie la couverture de tests de l'API"
    )
    parser.add_argument(
        "--min-coverage",
        type=int,
        default=80,
        help="Pourcentage minimum de couverture requis (défaut: 80)"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Mode strict: échoue immédiatement si couverture insuffisante"
    )

    args = parser.parse_args()

    # Exécuter les tests avec couverture
    success, coverage_data = run_coverage_tests(args.min_coverage)

    # Afficher le résumé
    display_coverage_summary(coverage_data, args.min_coverage)

    # Retourner le code de sortie approprié
    if not success:
        print("\n❌ Couverture insuffisante détectée!")
        print(f"   Assurez-vous que la couverture de l'API est >= "
              f"{args.min_coverage}%")
        print("   Ajoutez des tests pour les fichiers listés ci-dessus.")
        sys.exit(1)
    else:
        print("\n✅ Couverture API validée!")
        sys.exit(0)


if __name__ == "__main__":
    main()
