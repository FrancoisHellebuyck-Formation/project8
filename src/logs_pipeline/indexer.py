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
            index: Nom de l'index pour les logs bruts
        """
        if not ELASTICSEARCH_AVAILABLE:
            raise ImportError(
                "elasticsearch n'est pas installé. "
                "Installez-le avec: pip install elasticsearch"
            )

        self.host = host or config.elasticsearch_host
        self.port = port or config.elasticsearch_port
        self.index = index or config.elasticsearch_index
        self.message_index = "ml-api-message"  # Index pour messages parsés
        self.perf_index = "ml-api-perfs"  # Index pour métriques de performance  # noqa: E501
        self.top_func_index = "ml-api-top-func"  # Index pour top functions dénormalisées  # noqa: E501
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
        """Crée les index s'ils n'existent pas."""
        try:
            # Index pour les logs bruts complets
            if not self.client.indices.exists(index=self.index):
                logs_mapping = {
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
                self.client.indices.create(
                    index=self.index, body=logs_mapping
                )
                logger.info(f"Index '{self.index}' créé avec succès")

            # Index pour les messages parsés uniquement
            if not self.client.indices.exists(index=self.message_index):
                message_mapping = {
                    "mappings": {
                        "properties": {
                            "@timestamp": {"type": "date"},
                            "transaction_id": {"type": "keyword"},
                            "http_method": {"type": "keyword"},
                            "http_path": {"type": "keyword"},
                            "status_code": {"type": "integer"},
                            "execution_time_ms": {"type": "float"},
                            "input_data": {
                                "type": "object",
                                "properties": {
                                    "AGE": {"type": "integer"},
                                    "GENDER": {"type": "keyword"},
                                    "SMOKING": {"type": "integer"},
                                    "YELLOW_FINGERS": {"type": "integer"},
                                    "ANXIETY": {"type": "integer"},
                                    "PEER_PRESSURE": {"type": "integer"},
                                    "CHRONIC_DISEASE": {"type": "integer"},
                                    "FATIGUE": {"type": "integer"},
                                    "ALLERGY": {"type": "integer"},
                                    "WHEEZING": {"type": "integer"},
                                    "ALCOHOL": {"type": "integer"},
                                    "COUGHING": {"type": "integer"},
                                    "SHORTNESS_OF_BREATH": {
                                        "type": "integer"
                                    },
                                    "SWALLOWING_DIFFICULTY": {
                                        "type": "integer"
                                    },
                                    "CHEST_PAIN": {"type": "integer"}
                                }
                            },
                            "result": {
                                "type": "object",
                                "properties": {
                                    "prediction": {"type": "keyword"},
                                    "probability": {"type": "float"},
                                    "message": {"type": "text"}
                                }
                            }
                        }
                    }
                }
                self.client.indices.create(
                    index=self.message_index, body=message_mapping
                )
                logger.info(
                    f"Index '{self.message_index}' créé avec succès"
                )

            # Index pour les métriques de performance
            if not self.client.indices.exists(index=self.perf_index):
                perf_mapping = {
                    "mappings": {
                        "properties": {
                            "@timestamp": {"type": "date"},
                            "transaction_id": {"type": "keyword"},
                            "inference_time_ms": {"type": "float"},
                            "cpu_time_ms": {"type": "float"},
                            "memory_mb": {"type": "float"},
                            "memory_delta_mb": {"type": "float"},
                            "function_calls": {"type": "integer"},
                            "latency_ms": {"type": "float"},
                            "top_functions": {
                                "type": "nested",
                                "properties": {
                                    "function": {"type": "keyword"},
                                    "file": {"type": "keyword"},
                                    "line": {"type": "integer"},
                                    "cumulative_time_ms": {"type": "float"},
                                    "total_time_ms": {"type": "float"},
                                    "calls": {"type": "integer"}
                                }
                            }
                        }
                    }
                }
                self.client.indices.create(
                    index=self.perf_index, body=perf_mapping
                )
                logger.info(
                    f"Index '{self.perf_index}' créé avec succès"
                )

            # Index pour les top functions dénormalisées
            if not self.client.indices.exists(index=self.top_func_index):
                top_func_mapping = {
                    "mappings": {
                        "properties": {
                            "@timestamp": {"type": "date"},
                            "transaction_id": {"type": "keyword"},
                            "function": {"type": "keyword"},
                            "file": {"type": "keyword"},
                            "line": {"type": "integer"},
                            "cumulative_time_ms": {"type": "float"},
                            "total_time_ms": {"type": "float"},
                            "calls": {"type": "integer"}
                        }
                    }
                }
                self.client.indices.create(
                    index=self.top_func_index, body=top_func_mapping
                )
                logger.info(
                    f"Index '{self.top_func_index}' créé avec succès"
                )
        except Exception as e:
            logger.error(f"Erreur lors de la création des index: {e}")

    def _extract_message_data(self, doc: Dict) -> Optional[Dict]:
        """
        Extrait les données structurées d'un document pour l'index message.

        Args:
            doc: Document source complet

        Returns:
            Dict: Document avec uniquement les données structurées, ou None
        """
        # Ne garder que les documents qui ont des données parsées
        if not doc.get('input_data') or not doc.get('result'):
            return None

        message_doc = {
            '@timestamp': doc.get('@timestamp'),
            'transaction_id': doc.get('transaction_id'),
            'http_method': doc.get('http_method'),
            'http_path': doc.get('http_path'),
            'status_code': doc.get('status_code'),
            'execution_time_ms': doc.get('execution_time_ms'),
            'input_data': doc.get('input_data'),
            'result': doc.get('result')
        }

        return message_doc

    def _extract_perf_data(self, doc: Dict) -> Optional[Dict]:
        """
        Extrait les métriques de performance d'un document.

        Args:
            doc: Document source complet

        Returns:
            Dict: Document avec uniquement les métriques de performance,
                  ou None
        """
        import json

        # Chercher "performance_metrics" dans le message
        message = doc.get('message', '')

        # Essayer de parser le message comme JSON
        try:
            parsed = json.loads(message)
            if 'performance_metrics' in parsed:
                perf_metrics = parsed['performance_metrics']

                # Créer le document de performance
                perf_doc = {
                    '@timestamp': doc.get('@timestamp'),
                    'transaction_id': perf_metrics.get('transaction_id'),
                    'inference_time_ms': perf_metrics.get(
                        'inference_time_ms'
                    ),
                    'cpu_time_ms': perf_metrics.get('cpu_time_ms'),
                    'memory_mb': perf_metrics.get('memory_mb'),
                    'memory_delta_mb': perf_metrics.get('memory_delta_mb'),
                    'function_calls': perf_metrics.get('function_calls'),
                    'latency_ms': perf_metrics.get('latency_ms'),
                    'top_functions': perf_metrics.get('top_functions', [])
                }

                return perf_doc
        except (json.JSONDecodeError, TypeError):
            pass

        return None

    def _extract_top_functions(self, doc: Dict) -> List[Dict]:
        """
        Extrait et dénormalise les top_functions d'un document.

        Args:
            doc: Document source complet

        Returns:
            List[Dict]: Liste de documents de fonctions avec transaction_id
        """
        import json

        # Chercher "performance_metrics" dans le message
        message = doc.get('message', '')

        # Essayer de parser le message comme JSON
        try:
            parsed = json.loads(message)
            if 'performance_metrics' in parsed:
                perf_metrics = parsed['performance_metrics']
                top_functions = perf_metrics.get('top_functions', [])
                transaction_id = perf_metrics.get('transaction_id')
                timestamp = doc.get('@timestamp')

                # Dénormaliser: créer un document par fonction
                func_docs = []
                for func in top_functions:
                    func_doc = {
                        '@timestamp': timestamp,
                        'transaction_id': transaction_id,
                        'function': func.get('function'),
                        'file': func.get('file'),
                        'line': func.get('line'),
                        'cumulative_time_ms': func.get('cumulative_time_ms'),
                        'total_time_ms': func.get('total_time_ms'),
                        'calls': func.get('calls')
                    }
                    func_docs.append(func_doc)

                return func_docs
        except (json.JSONDecodeError, TypeError):
            pass

        return []

    def index_documents(
        self,
        all_documents: List[Dict],
        filtered_documents: Optional[List[Dict]] = None
    ) -> int:
        """
        Indexe les documents dans Elasticsearch.
        - Tous les logs (bruts, non filtrés) dans ml-api-logs
        - Messages parsés (filtrés) dans ml-api-message
        - Métriques de performance (filtrés) dans ml-api-perfs

        Args:
            all_documents: Liste de TOUS les documents (non filtrés)
            filtered_documents: Liste des documents filtrés (optionnel).
                               Si None, utilise all_documents

        Returns:
            int: Nombre de documents indexés avec succès
        """
        if not all_documents:
            logger.info("Aucun document à indexer")
            return 0

        # Si aucun document filtré fourni, utiliser tous les documents
        if filtered_documents is None:
            filtered_documents = all_documents

        try:
            if self.client is None:
                if not self.connect():
                    return 0

            # Préparer les actions pour bulk insert
            # 1. TOUS les documents vont dans l'index des logs bruts (sans filtrage)  # noqa: E501
            actions = [
                {
                    "_index": self.index,
                    "_source": doc
                }
                for doc in all_documents
            ]

            # 2. Documents FILTRÉS avec données parsées dans l'index messages
            for doc in filtered_documents:
                message_doc = self._extract_message_data(doc)
                if message_doc:
                    actions.append({
                        "_index": self.message_index,
                        "_source": message_doc
                    })

            # 3. Documents FILTRÉS avec métriques de performance dans l'index perfs  # noqa: E501
            for doc in filtered_documents:
                perf_doc = self._extract_perf_data(doc)
                if perf_doc:
                    actions.append({
                        "_index": self.perf_index,
                        "_source": perf_doc
                    })

            # 4. Documents FILTRÉS avec top_functions dénormalisées
            for doc in filtered_documents:
                func_docs = self._extract_top_functions(doc)
                for func_doc in func_docs:
                    actions.append({
                        "_index": self.top_func_index,
                        "_source": func_doc
                    })

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
                message_count = len(
                    [d for d in filtered_documents if self._extract_message_data(d)]  # noqa: E501
                )
                perf_count = len(
                    [d for d in filtered_documents if self._extract_perf_data(d)]  # noqa: E501
                )
                func_count = sum(
                    len(self._extract_top_functions(d))
                    for d in filtered_documents
                )
                logger.info(
                    f"Indexation: {success} documents indexés avec succès "
                    f"({len(all_documents)} logs bruts, "
                    f"{message_count} messages parsés, "
                    f"{perf_count} métriques de performance, "
                    f"{func_count} top functions)"
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
