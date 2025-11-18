"""
Indexeur Elasticsearch pour le pipeline de logs.

Ce module indexe les logs filtrés dans Elasticsearch.
"""

import logging
from typing import Dict, List, Optional

from .config import config

logger = logging.getLogger(__name__)

# Import optionnel d'elasticsearch
try:
    from elasticsearch import Elasticsearch
    from elasticsearch.helpers import bulk
    ELASTICSEARCH_AVAILABLE = True
except ImportError:
    ELASTICSEARCH_AVAILABLE = False


class ElasticsearchIndexer:
    """Indexeur de logs dans Elasticsearch."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        index: Optional[str] = None
    ):
        """
        Initialise l'indexeur.

        Args:
            host: Hôte Elasticsearch
            port: Port Elasticsearch
            index: Nom de l'index
        """
        if not ELASTICSEARCH_AVAILABLE:
            raise ImportError(
                "elasticsearch n'est pas installé. "
                "Installez-le avec: pip install elasticsearch"
            )

        self.host = host or config.elasticsearch_host
        self.port = port or config.elasticsearch_port
        self.index = index or config.elasticsearch_index
        self.client: Optional[Elasticsearch] = None

    def connect(self) -> bool:
        """
        Teste la connexion à Elasticsearch.

        Returns:
            bool: True si connecté, False sinon
        """
        try:
            # Elasticsearch 8.x utilise une URL complète
            url = f"http://{self.host}:{self.port}"
            self.client = Elasticsearch(
                [url],
                verify_certs=False,
                ssl_show_warn=False,
                max_retries=0,  # Pas de retry pour la vérification
                retry_on_timeout=False
            )
            # Vérifier la connexion
            if self.client.ping():
                logger.info(
                    f"Connecté à Elasticsearch sur {self.host}:{self.port}"
                )
                # Créer l'index s'il n'existe pas
                self._create_index_if_not_exists()
                return True
            else:
                logger.error("Impossible de ping Elasticsearch")
                return False
        except Exception as e:
            logger.error(f"Erreur de connexion à Elasticsearch: {e}")
            return False

    def _create_index_if_not_exists(self) -> None:
        """Crée l'index s'il n'existe pas."""
        try:
            if not self.client.indices.exists(index=self.index):
                # Définir le mapping
                mapping = {
                    "mappings": {
                        "properties": {
                            "@timestamp": {"type": "date"},
                            "level": {"type": "keyword"},
                            "logger": {"type": "keyword"},
                            "message": {"type": "text"},
                            "transaction_id": {"type": "keyword"},
                            "http_method": {"type": "keyword"},
                            "http_path": {"type": "keyword"},
                            "status_code": {"type": "integer"},
                            "execution_time_ms": {"type": "float"},
                            "input_data": {"type": "object"},
                            "result": {"type": "object"},
                            "raw_log": {"type": "text"}
                        }
                    }
                }
                self.client.indices.create(index=self.index, body=mapping)
                logger.info(f"Index '{self.index}' créé avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'index: {e}")

    def index_documents(self, documents: List[Dict]) -> int:
        """
        Indexe une liste de documents dans Elasticsearch.

        Args:
            documents: Liste de documents à indexer

        Returns:
            int: Nombre de documents indexés avec succès
        """
        if not documents:
            logger.info("Aucun document à indexer")
            return 0

        try:
            if self.client is None:
                if not self.connect():
                    return 0

            # Préparer les actions pour bulk insert
            actions = [
                {
                    "_index": self.index,
                    "_source": doc
                }
                for doc in documents
            ]

            # Indexer en masse
            success, errors = bulk(
                self.client,
                actions,
                raise_on_error=False,
                stats_only=False
            )

            failed = len(errors)

            # Logger les erreurs si présentes
            if errors:
                logger.warning(
                    f"Indexation: {success} documents indexés, "
                    f"{failed} échoués"
                )
                for error in errors[:3]:  # Afficher les 3 premières erreurs
                    logger.error(f"Erreur d'indexation: {error}")
            else:
                logger.info(
                    f"Indexation: {success} documents indexés avec succès"
                )

            return success

        except Exception as e:
            logger.error(f"Erreur lors de l'indexation: {e}")
            return 0

    def close(self) -> None:
        """Ferme la connexion Elasticsearch."""
        if self.client:
            self.client.close()
            logger.info("Connexion Elasticsearch fermée")
