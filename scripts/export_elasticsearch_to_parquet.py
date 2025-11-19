#!/usr/bin/env python3
"""
Script pour extraire les données de ml-api-message vers un fichier Parquet.

Le format Parquet généré suit la même structure que le dataset d'entraînement :
- Features de base (14 colonnes)
- Features dérivées (14 colonnes générées par feature engineering)
- Target (basé sur la prédiction)

Usage:
    python scripts/export_elasticsearch_to_parquet.py [--output path.parquet]
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Dict

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


def extract_documents_from_elasticsearch(
    indexer
) -> List[Dict]:
    """
    Extrait tous les documents de l'index ml-api-message.

    Args:
        indexer: Instance de ElasticsearchIndexer

    Returns:
        List[Dict]: Liste des documents
    """
    logger.info(
        f"Récupération des documents de '{indexer.message_index}'..."
    )

    try:
        # Utiliser scroll pour récupérer tous les documents
        response = indexer.client.search(
            index=indexer.message_index,
            scroll='5m',
            size=1000,
            body={
                "query": {"match_all": {}},
                "sort": [{"@timestamp": "asc"}]
            }
        )

        scroll_id = response['_scroll_id']
        total_docs = response['hits']['total']['value']
        logger.info(f"  Total de documents trouvés: {total_docs}")

        # Récupérer tous les documents
        all_docs = []
        while True:
            hits = response['hits']['hits']
            if not hits:
                break

            for hit in hits:
                all_docs.append(hit['_source'])

            # Récupérer le batch suivant
            response = indexer.client.scroll(
                scroll_id=scroll_id,
                scroll='5m'
            )

        # Nettoyer le scroll
        indexer.client.clear_scroll(scroll_id=scroll_id)

        logger.info(f"  Documents récupérés: {len(all_docs)}")
        return all_docs

    except Exception as e:
        logger.error(f"Erreur lors de l'extraction: {e}")
        return []


def convert_to_dataframe(documents: List[Dict]):
    """
    Convertit les documents Elasticsearch en DataFrame.

    Args:
        documents: Liste des documents

    Returns:
        DataFrame: DataFrame avec les features de base
    """
    import pandas as pd

    logger.info("\nConversion en DataFrame...")

    rows = []
    skipped = 0

    for doc in documents:
        input_data = doc.get('input_data')
        result = doc.get('result')

        if not input_data or not result:
            skipped += 1
            continue

        # Extraire les features de base
        # Note: Les noms avec underscores ont été normalisés par le collector
        row = {
            'GENDER': input_data.get('GENDER'),
            'AGE': input_data.get('AGE'),
            'SMOKING': input_data.get('SMOKING'),
            'YELLOW_FINGERS': input_data.get('YELLOW_FINGERS'),
            'ANXIETY': input_data.get('ANXIETY'),
            'PEER_PRESSURE': input_data.get('PEER_PRESSURE'),
            'CHRONIC DISEASE': input_data.get('CHRONIC_DISEASE'),
            'FATIGUE': input_data.get('FATIGUE'),
            'ALLERGY': input_data.get('ALLERGY'),
            'WHEEZING': input_data.get('WHEEZING'),
            'ALCOHOL CONSUMING': input_data.get('ALCOHOL'),
            'COUGHING': input_data.get('COUGHING'),
            'SHORTNESS OF BREATH': input_data.get('SHORTNESS_OF_BREATH'),
            'SWALLOWING DIFFICULTY': input_data.get('SWALLOWING_DIFFICULTY'),
            'CHEST PAIN': input_data.get('CHEST_PAIN'),
            'target': result.get('prediction')  # 0 ou 1
        }

        # Vérifier que toutes les valeurs sont présentes
        if None in row.values():
            skipped += 1
            continue

        rows.append(row)

    if skipped > 0:
        logger.warning(f"  {skipped} document(s) ignoré(s) (données manquantes)")

    df = pd.DataFrame(rows)
    logger.info(f"  DataFrame créé: {len(df)} lignes, {len(df.columns)} colonnes")

    return df


def apply_feature_engineering(df):
    """
    Applique le feature engineering pour générer les features dérivées.

    Args:
        df: DataFrame avec les features de base + target

    Returns:
        DataFrame: DataFrame avec features de base + features dérivées + target
    """
    from src.model.feature_engineering import FeatureEngineer

    logger.info("\nApplication du feature engineering...")

    # Sauvegarder la colonne target (sera perdue par engineer_features)
    target = df['target'].copy()

    # Créer l'ingénieur de features
    engineer = FeatureEngineer()

    # Appliquer les transformations (sans target)
    df_engineered = engineer.engineer_features(df)

    # Réinsérer la colonne target à la fin
    df_engineered['target'] = target

    logger.info(
        f"  Features générées: {len(df_engineered.columns)} colonnes totales"
    )

    return df_engineered


def save_to_parquet(df, output_path: str):
    """
    Sauvegarde le DataFrame au format Parquet.

    Args:
        df: DataFrame à sauvegarder
        output_path: Chemin du fichier de sortie
    """
    logger.info(f"\nSauvegarde vers {output_path}...")

    # Créer le répertoire si nécessaire
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Sauvegarder
    df.to_parquet(output_path, index=False, engine='pyarrow')

    # Vérifier la taille du fichier
    file_size = output_file.stat().st_size
    if file_size < 1024:
        size_str = f"{file_size} B"
    elif file_size < 1024 * 1024:
        size_str = f"{file_size / 1024:.2f} KB"
    else:
        size_str = f"{file_size / (1024 * 1024):.2f} MB"

    logger.info(f"  Fichier créé: {size_str}")


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description='Exporter ml-api-message vers Parquet'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='model/inference_dataset.parquet',
        help='Chemin du fichier Parquet de sortie (default: model/inference_dataset.parquet)'  # noqa: E501
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Export de ml-api-message vers Parquet")
    logger.info("=" * 60)

    # Importer après le logging est configuré
    from src.logs_pipeline.indexer import ElasticsearchIndexer

    # Créer l'indexeur
    indexer = ElasticsearchIndexer()

    # Se connecter
    logger.info("\nConnexion à Elasticsearch...")
    if not indexer.connect():
        logger.error("✗ Impossible de se connecter à Elasticsearch")
        logger.error(
            "  Assurez-vous qu'Elasticsearch est démarré avec: "
            "make pipeline-elasticsearch-up"
        )
        sys.exit(1)

    logger.info("✓ Connexion réussie")

    # Vérifier que l'index existe
    if not indexer.client.indices.exists(index=indexer.message_index):
        logger.error(
            f"\n✗ L'index '{indexer.message_index}' n'existe pas"
        )
        logger.error("  Exécutez d'abord le pipeline: make pipeline-once")
        indexer.close()
        sys.exit(1)

    # Extraire les documents
    documents = extract_documents_from_elasticsearch(indexer)
    indexer.close()

    if not documents:
        logger.error("\n✗ Aucun document à exporter")
        sys.exit(1)

    # Convertir en DataFrame
    df = convert_to_dataframe(documents)

    if df.empty:
        logger.error("\n✗ DataFrame vide après conversion")
        sys.exit(1)

    # Appliquer le feature engineering
    df_engineered = apply_feature_engineering(df)

    # Sauvegarder
    save_to_parquet(df_engineered, args.output)

    # Résumé
    logger.info("\n" + "=" * 60)
    logger.info("Résumé de l'export:")
    logger.info("=" * 60)
    logger.info(f"  Documents ES extraits: {len(documents)}")
    logger.info(f"  Lignes dans le Parquet: {len(df_engineered)}")
    logger.info(f"  Colonnes: {len(df_engineered.columns)}")
    logger.info(f"  Fichier: {args.output}")
    logger.info("=" * 60)
    logger.info("✓ SUCCÈS: Export terminé")

    # Afficher les premières lignes
    logger.info("\nAperçu des données exportées:")
    logger.info(f"\n{df_engineered.head(3)}")

    sys.exit(0)


if __name__ == "__main__":
    main()
