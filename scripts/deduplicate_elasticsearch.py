#!/usr/bin/env python3
"""
Script pour dédoublonner les index Elasticsearch.

Dédouplonne:
- ml-api-message: Messages de prédiction (basé sur transaction_id)
- ml-api-perfs: Métriques de performance (basé sur transaction_id)

La déduplication se fait sur la base du champ 'transaction_id'.
Seul le document le plus récent (basé sur @timestamp) est conservé.

Usage:
    python scripts/deduplicate_elasticsearch.py
"""

import logging
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime

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


def parse_timestamp(timestamp_str: str) -> datetime:
    """
    Parse un timestamp ISO 8601.

    Args:
        timestamp_str: Timestamp au format ISO 8601

    Returns:
        datetime: Objet datetime
    """
    # Retirer le 'Z' final si présent
    if timestamp_str.endswith('Z'):
        timestamp_str = timestamp_str[:-1]

    try:
        return datetime.fromisoformat(timestamp_str)
    except ValueError:
        # Si le parsing échoue, retourner une date minimale
        return datetime.min


def deduplicate_index(indexer, index_name: str) -> dict:
    """
    Déduplique un index Elasticsearch.

    Args:
        indexer: Instance d'ElasticsearchIndexer
        index_name: Nom de l'index à dédoublonner

    Returns:
        dict: Statistiques de déduplication
    """
    logger.info("=" * 60)
    logger.info(f"Déduplication de l'index {index_name}")
    logger.info("=" * 60)

    # Vérifier que l'index existe
    if not indexer.client.indices.exists(index=index_name):
        logger.warning(
            f"\n⊘ L'index '{index_name}' n'existe pas"
        )
        logger.info("  Rien à dédoublonner")
        return {
            'index': index_name,
            'total_docs': 0,
            'deleted': 0,
            'errors': 0,
            'exists': False
        }

    # Récupérer tous les documents
    logger.info(f"\nRécupération des documents de '{index_name}'...")

    try:
        # Utiliser scroll pour récupérer tous les documents
        response = indexer.client.search(
            index=index_name,
            scroll='2m',
            size=1000,
            body={
                "query": {"match_all": {}},
                "sort": [{"@timestamp": "desc"}]
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
                all_docs.append({
                    'id': hit['_id'],
                    'source': hit['_source']
                })

            # Récupérer le batch suivant
            response = indexer.client.scroll(
                scroll_id=scroll_id,
                scroll='2m'
            )

        # Nettoyer le scroll
        indexer.client.clear_scroll(scroll_id=scroll_id)

        logger.info(f"  Documents récupérés: {len(all_docs)}")

        # Grouper par transaction_id
        logger.info("\nAnalyse des doublons...")
        transactions = defaultdict(list)
        docs_without_transaction_id = 0

        for doc in all_docs:
            transaction_id = doc['source'].get('transaction_id')
            if transaction_id:
                transactions[transaction_id].append(doc)
            else:
                docs_without_transaction_id += 1

        logger.info(f"  Transactions uniques: {len(transactions)}")
        logger.info(
            f"  Documents sans transaction_id: {docs_without_transaction_id}"
        )

        # Identifier les doublons
        duplicates_to_delete = []
        duplicate_transactions = 0

        for transaction_id, docs in transactions.items():
            if len(docs) > 1:
                duplicate_transactions += 1
                # Trier par timestamp (plus récent en premier)
                docs.sort(
                    key=lambda d: parse_timestamp(
                        d['source'].get('@timestamp', '')
                    ),
                    reverse=True
                )

                # Garder le premier (plus récent), supprimer les autres
                for doc in docs[1:]:
                    duplicates_to_delete.append(doc['id'])

        logger.info(
            f"  Transactions avec doublons: {duplicate_transactions}"
        )
        logger.info(
            f"  Documents à supprimer: {len(duplicates_to_delete)}"
        )

        if not duplicates_to_delete:
            logger.info("\n✓ Aucun doublon trouvé, l'index est déjà propre")
            return {
                'index': index_name,
                'total_docs': total_docs,
                'deleted': 0,
                'errors': 0,
                'exists': True
            }

        # Supprimer les doublons
        logger.info(f"\nSuppression de {len(duplicates_to_delete)} doublons...")

        deleted_count = 0
        errors = 0

        for doc_id in duplicates_to_delete:
            try:
                indexer.client.delete(
                    index=index_name,
                    id=doc_id
                )
                deleted_count += 1
                if deleted_count % 100 == 0:
                    logger.info(f"  Progression: {deleted_count}/{len(duplicates_to_delete)}")
            except Exception as e:
                logger.error(f"  Erreur lors de la suppression de {doc_id}: {e}")
                errors += 1

        # Rafraîchir l'index
        indexer.client.indices.refresh(index=index_name)

        # Résumé
        logger.info("\n" + "=" * 60)
        logger.info("Résumé de la déduplication:")
        logger.info("=" * 60)
        logger.info(f"  Documents avant: {total_docs}")
        logger.info(f"  Doublons supprimés: {deleted_count}")
        logger.info(f"  Erreurs: {errors}")
        logger.info(f"  Documents après: {total_docs - deleted_count}")
        logger.info("=" * 60)

        if errors > 0:
            logger.warning(
                f"✓ Déduplication terminée avec {errors} erreur(s)"
            )
        else:
            logger.info("✓ SUCCÈS: Déduplication terminée sans erreur")

        return {
            'index': index_name,
            'total_docs': total_docs,
            'deleted': deleted_count,
            'errors': errors,
            'exists': True
        }

    except Exception as e:
        logger.error(f"\n✗ Erreur lors de la déduplication: {e}")
        return {
            'index': index_name,
            'total_docs': 0,
            'deleted': 0,
            'errors': 1,
            'exists': True
        }


def main():
    """Point d'entrée principal."""
    from src.logs_pipeline.indexer import ElasticsearchIndexer

    logger.info("=" * 70)
    logger.info("Déduplication des index Elasticsearch")
    logger.info("=" * 70)

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

    logger.info("✓ Connexion réussie\n")

    # Dédoublonner les index
    indexes = [
        indexer.message_index,  # ml-api-message
        indexer.perf_index       # ml-api-perfs
    ]

    results = []
    for index_name in indexes:
        result = deduplicate_index(indexer, index_name)
        results.append(result)
        logger.info("")  # Ligne vide entre les index

    # Fermer la connexion
    indexer.close()

    # Résumé global
    logger.info("=" * 70)
    logger.info("RÉSUMÉ GLOBAL DE LA DÉDUPLICATION")
    logger.info("=" * 70)

    total_deleted = 0
    total_errors = 0

    for result in results:
        if result['exists']:
            logger.info(
                f"  {result['index']:20} : "
                f"{result['deleted']} doublons supprimés "
                f"(sur {result['total_docs']} documents)"
            )
            total_deleted += result['deleted']
            total_errors += result['errors']
        else:
            logger.info(
                f"  {result['index']:20} : n'existe pas (ignoré)"
            )

    logger.info("")
    logger.info(f"  Total doublons supprimés : {total_deleted}")
    logger.info(f"  Total erreurs            : {total_errors}")
    logger.info("=" * 70)

    if total_errors > 0:
        logger.warning(
            f"\n✓ Déduplication terminée avec {total_errors} erreur(s)"
        )
        sys.exit(1)
    else:
        logger.info("\n✓ SUCCÈS: Déduplication terminée sans erreur")
        sys.exit(0)


if __name__ == "__main__":
    main()
