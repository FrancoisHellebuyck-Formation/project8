#!/usr/bin/env python3
"""
Script d'analyse du drift de données avec Evidently AI.

Compare le dataset d'entraînement avec les données de production
pour détecter les dérives de données et de prédictions.

Usage:
    python scripts/analyze_data_drift.py [--reference train.parquet] \
                                          [--current prod.parquet] \
                                          [--output report.html]
"""

import argparse
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


def check_evidently_installed():
    """Vérifie qu'Evidently AI est installé."""
    try:
        import evidently  # noqa: F401
        return True
    except ImportError:
        logger.error("✗ Evidently AI n'est pas installé")
        logger.error("  Installez-le avec: uv pip install evidently")
        return False


def load_datasets(reference_path: str, current_path: str):
    """
    Charge les datasets de référence et de production.

    Args:
        reference_path: Chemin vers le dataset d'entraînement
        current_path: Chemin vers le dataset de production

    Returns:
        Tuple[DataFrame, DataFrame]: (reference_data, current_data)
    """
    import pandas as pd

    logger.info("\nChargement des datasets...")

    # Vérifier que les fichiers existent
    if not Path(reference_path).exists():
        logger.error(f"✗ Fichier de référence introuvable: {reference_path}")
        sys.exit(1)

    if not Path(current_path).exists():
        logger.error(f"✗ Fichier de production introuvable: {current_path}")
        logger.error(
            "  Exportez d'abord les données: make pipeline-export-parquet"
        )
        sys.exit(1)

    # Charger les datasets
    reference_data = pd.read_parquet(reference_path)
    current_data = pd.read_parquet(current_path)

    logger.info(f"  Dataset de référence: {reference_data.shape}")
    logger.info(f"  Dataset de production: {current_data.shape}")

    # Vérifier que les colonnes correspondent
    ref_cols = set(reference_data.columns)
    curr_cols = set(current_data.columns)

    if ref_cols != curr_cols:
        missing_in_current = ref_cols - curr_cols
        extra_in_current = curr_cols - ref_cols

        if missing_in_current:
            logger.warning(
                f"  ⚠ Colonnes manquantes dans production: "
                f"{missing_in_current}"
            )

        if extra_in_current:
            logger.warning(
                f"  ⚠ Colonnes supplémentaires dans production: "
                f"{extra_in_current}"
            )

    return reference_data, current_data


def generate_data_drift_report(
    reference_data,
    current_data,
    output_path: str
):
    """
    Génère un rapport de drift de données avec Evidently AI.

    Args:
        reference_data: Dataset de référence
        current_data: Dataset de production
        output_path: Chemin du fichier HTML de sortie
    """
    from evidently import Report
    from evidently.metrics import (
        DriftedColumnsCount,
        DatasetMissingValueCount,
        ValueDrift,
    )

    logger.info("\nGénération du rapport de drift...")

    # Identifier les colonnes communes
    common_columns = list(
        set(reference_data.columns) & set(current_data.columns)
    )

    # Target présente dans référence mais pas dans production
    target_in_ref = 'target' in reference_data.columns
    target_in_curr = 'target' in current_data.columns

    logger.info(f"  Colonnes communes: {len(common_columns)}")
    logger.info(f"  Target dans référence: {target_in_ref}")
    logger.info(f"  Target dans production: {target_in_curr}")

    # Si target manquante dans current, on l'ajoute temporairement
    # avec les mêmes valeurs que référence pour permettre l'analyse
    if target_in_ref and not target_in_curr:
        logger.warning(
            "  ⚠ Target manquante dans production, "
            "ajout temporaire pour l'analyse"
        )
        # Copier current_data pour ne pas modifier l'original
        current_data = current_data.copy()
        # Ajouter une colonne target fictive (moyenne de ref)
        current_data['target'] = int(
            reference_data['target'].mean() > 0.5
        )

    # Créer les métriques
    metrics = [
        DriftedColumnsCount(),
        DatasetMissingValueCount(),
    ]

    # Ajouter drift par colonne pour les principales features
    important_features = [
        'AGE', 'SMOKING', 'YELLOW_FINGERS', 'ANXIETY',
        'CHRONIC DISEASE', 'FATIGUE', 'WHEEZING', 'COUGHING'
    ]

    for feature in important_features:
        if feature in common_columns:
            metrics.append(ValueDrift(column=feature))

    # Créer le rapport
    report = Report(metrics=metrics)

    # Générer le rapport
    logger.info("  Calcul des métriques de drift...")
    snapshot = report.run(
        reference_data=reference_data,
        current_data=current_data
    )

    # Sauvegarder le rapport
    logger.info(f"  Sauvegarde du rapport vers {output_path}...")
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    snapshot.save_html(str(output_file))

    # Taille du fichier
    file_size = output_file.stat().st_size
    if file_size < 1024:
        size_str = f"{file_size} B"
    elif file_size < 1024 * 1024:
        size_str = f"{file_size / 1024:.2f} KB"
    else:
        size_str = f"{file_size / (1024 * 1024):.2f} MB"

    logger.info(f"  Rapport créé: {size_str}")

    return snapshot


def extract_drift_summary(reference_data, current_data):
    """
    Extrait un résumé textuel du drift.

    Args:
        reference_data: Dataset de référence
        current_data: Dataset de production
    """
    from scipy import stats

    logger.info("\n" + "=" * 60)
    logger.info("Résumé du drift de données")
    logger.info("=" * 60)

    # Statistiques générales
    logger.info("\nTaille des datasets:")
    logger.info(f"  Référence: {len(reference_data):,} lignes")
    logger.info(f"  Production: {len(current_data):,} lignes")

    # Drift de la target
    ref_target_mean = reference_data['target'].mean()
    curr_target_mean = current_data['target'].mean()
    target_drift = abs(curr_target_mean - ref_target_mean)

    logger.info("\nDistribution de la target:")
    logger.info(
        f"  Référence: {ref_target_mean:.1%} positifs"
    )
    logger.info(
        f"  Production: {curr_target_mean:.1%} positifs"
    )
    logger.info(
        f"  Drift: {target_drift:.1%}"
    )

    if target_drift > 0.05:
        logger.warning("  ⚠ ALERTE: Drift de target significatif (>5%)")
    else:
        logger.info("  ✓ Drift de target acceptable (<5%)")

    # Analyser les features principales
    logger.info("\nDrift des features principales:")

    important_features = [
        'AGE', 'SMOKING', 'YELLOW_FINGERS', 'ANXIETY',
        'CHRONIC DISEASE', 'FATIGUE', 'WHEEZING', 'COUGHING'
    ]

    drift_features = []

    for feature in important_features:
        if feature not in reference_data.columns:
            continue

        ref_mean = reference_data[feature].mean()
        curr_mean = current_data[feature].mean()
        drift = abs(curr_mean - ref_mean)

        # Test de Kolmogorov-Smirnov
        try:
            ks_stat, p_value = stats.ks_2samp(
                reference_data[feature].dropna(),
                current_data[feature].dropna()
            )

            drift_detected = p_value < 0.05

            logger.info(f"  {feature}:")
            logger.info(
                f"    Moyenne: {ref_mean:.2f} → {curr_mean:.2f} "
                f"(drift: {drift:.2f})"
            )
            logger.info(f"    KS test: stat={ks_stat:.4f}, p={p_value:.4f}")

            if drift_detected:
                logger.warning("    ⚠ Drift détecté (p < 0.05)")
                drift_features.append(feature)
            else:
                logger.info("    ✓ Pas de drift significatif")

        except Exception as e:
            logger.warning(f"    ⚠ Erreur lors du test: {e}")

    # Résumé final
    logger.info("\n" + "=" * 60)
    logger.info("Conclusion:")
    logger.info("=" * 60)

    if len(drift_features) == 0 and target_drift <= 0.05:
        logger.info("✓ Aucun drift significatif détecté")
        logger.info("  Le modèle est stable en production")
    elif len(drift_features) <= 2 and target_drift <= 0.10:
        logger.warning("⚠ Drift modéré détecté")
        logger.warning(
            f"  {len(drift_features)} feature(s) avec drift: "
            f"{', '.join(drift_features)}"
        )
        logger.warning("  Surveillance recommandée")
    else:
        logger.error("✗ Drift important détecté")
        logger.error(
            f"  {len(drift_features)} feature(s) avec drift: "
            f"{', '.join(drift_features)}"
        )
        logger.error(f"  Drift de target: {target_drift:.1%}")
        logger.error("  ⚠ Réentraînement du modèle recommandé")

    logger.info("=" * 60)


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description='Analyser le drift de données avec Evidently AI'
    )
    parser.add_argument(
        '--reference',
        type=str,
        default='model/training_dataset.parquet',
        help='Chemin vers le dataset de référence (default: model/training_dataset.parquet)'  # noqa: E501
    )
    parser.add_argument(
        '--current',
        type=str,
        default='model/inference_dataset.parquet',
        help='Chemin vers le dataset de production (default: model/inference_dataset.parquet)'  # noqa: E501
    )
    parser.add_argument(
        '--output',
        type=str,
        default='reports/data_drift_report.html',
        help='Chemin du rapport HTML (default: reports/data_drift_report.html)'  # noqa: E501
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Analyse du drift de données avec Evidently AI")
    logger.info("=" * 60)

    # Vérifier qu'Evidently est installé
    if not check_evidently_installed():
        sys.exit(1)

    # Charger les datasets
    reference_data, current_data = load_datasets(
        args.reference,
        args.current
    )

    # Générer le rapport Evidently
    generate_data_drift_report(
        reference_data,
        current_data,
        args.output
    )

    # Extraire un résumé textuel
    extract_drift_summary(reference_data, current_data)

    logger.info(f"\n✓ Rapport HTML disponible: {args.output}")
    logger.info("  Ouvrez-le dans votre navigateur pour voir les détails")

    sys.exit(0)


if __name__ == "__main__":
    main()
