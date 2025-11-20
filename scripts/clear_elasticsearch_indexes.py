#!/usr/bin/env python3
"""
Script pour vider les index Elasticsearch.

Usage:
    python scripts/clear_elasticsearch_indexes.py
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


def main():
    """Point d'entrée principal."""
    from src.logs_pipeline.indexer import ElasticsearchIndexer

    logger.info("=" * 60)
    logger.info("Suppression des index Elasticsearch")
    logger.info("=" * 60)

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

    # Liste des index à supprimer
    indexes_to_delete = [
        indexer.index,           # ml-api-logs
        indexer.message_index,   # ml-api-message
        indexer.perf_index,      # ml-api-perfs
    ]

    logger.info("\n" + "=" * 60)
    logger.info("Suppression des index:")
    logger.info("=" * 60)

    deleted_count = 0
    for index_name in indexes_to_delete:
        try:
            if indexer.client.indices.exists(index=index_name):
                logger.info(f"\n  Suppression de l'index '{index_name}'...")
                indexer.client.indices.delete(index=index_name)
                logger.info(f"  ✓ Index '{index_name}' supprimé")
                deleted_count += 1
            else:
                logger.info(
                    f"  ⊘ Index '{index_name}' n'existe pas (rien à faire)"
                )
        except Exception as e:
            logger.error(f"  ✗ Erreur lors de la suppression de '{index_name}': {e}")

    # Fermer la connexion
    indexer.close()

    logger.info("\n" + "=" * 60)
    if deleted_count > 0:
        logger.info(f"✓ SUCCÈS: {deleted_count} index supprimé(s)")
        logger.info(
            "  Les index seront recréés automatiquement au prochain "
            "lancement du pipeline"
        )
    else:
        logger.info("✓ Aucun index à supprimer")
    logger.info("=" * 60)

    sys.exit(0)


if __name__ == "__main__":
    main()
