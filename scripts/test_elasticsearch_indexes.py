#!/usr/bin/env python3
"""
Script pour tester la création des index Elasticsearch.

Usage:
    python scripts/test_elasticsearch_indexes.py
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
    logger.info("Test de création des index Elasticsearch")
    logger.info("=" * 60)

    # Créer l'indexeur
    indexer = ElasticsearchIndexer()

    # Se connecter (cela créera les index)
    logger.info("\nConnexion à Elasticsearch...")
    if not indexer.connect():
        logger.error("✗ Impossible de se connecter à Elasticsearch")
        logger.error(
            "  Assurez-vous qu'Elasticsearch est démarré avec: "
            "make pipeline-elasticsearch-up"
        )
        sys.exit(1)

    logger.info("✓ Connexion réussie")

    # Vérifier les index
    logger.info("\nVérification des index...")

    # Index des logs bruts
    if indexer.client.indices.exists(index=indexer.index):
        logger.info(f"✓ Index '{indexer.index}' existe")
        mapping = indexer.client.indices.get_mapping(index=indexer.index)
        fields = mapping[indexer.index]['mappings']['properties'].keys()
        logger.info(f"  Champs: {', '.join(sorted(fields))}")
    else:
        logger.error(f"✗ Index '{indexer.index}' n'existe pas")

    # Index des messages parsés
    if indexer.client.indices.exists(index=indexer.message_index):
        logger.info(f"✓ Index '{indexer.message_index}' existe")
        mapping = indexer.client.indices.get_mapping(
            index=indexer.message_index
        )
        fields = mapping[indexer.message_index]['mappings'][
            'properties'
        ].keys()
        logger.info(f"  Champs: {', '.join(sorted(fields))}")
    else:
        logger.error(f"✗ Index '{indexer.message_index}' n'existe pas")

    # Fermer la connexion
    indexer.close()

    logger.info("\n" + "=" * 60)
    logger.info("✓ Test terminé avec succès")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
