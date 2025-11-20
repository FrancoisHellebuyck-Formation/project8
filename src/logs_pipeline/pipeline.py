"""
Pipeline d'intégration des logs dans Elasticsearch.

Ce module orchestre la collecte, le filtrage et l'indexation des logs.
"""

import logging
import time
from typing import Optional

from .collector import LogCollector
from .config import config
from .filter import LogFilter
from .indexer import ElasticsearchIndexer

logger = logging.getLogger(__name__)


class LogsPipeline:
    """Pipeline d'intégration des logs dans Elasticsearch."""

    def __init__(
        self,
        gradio_url: Optional[str] = None,
        hf_token: Optional[str] = None,
        elasticsearch_host: Optional[str] = None,
        elasticsearch_port: Optional[int] = None,
        elasticsearch_index: Optional[str] = None,
        filter_pattern: Optional[str] = None
    ):
        """
        Initialise le pipeline.

        Args:
            gradio_url: URL de l'API Gradio
            hf_token: Token HuggingFace
            elasticsearch_host: Hôte Elasticsearch
            elasticsearch_port: Port Elasticsearch
            elasticsearch_index: Nom de l'index
            filter_pattern: Pattern de filtrage
        """
        self.collector = LogCollector(
            gradio_url=gradio_url,
            hf_token=hf_token
        )
        self.filter = LogFilter(pattern=filter_pattern)
        self.indexer = ElasticsearchIndexer(
            host=elasticsearch_host,
            port=elasticsearch_port,
            index=elasticsearch_index
        )

    def check_prerequisites(self) -> bool:
        """
        Vérifie que tous les pré-requis sont remplis.

        Returns:
            bool: True si tous les pré-requis sont OK, False sinon
        """
        logger.info("Vérification des pré-requis...")

        all_ok = True

        # 1. Vérifier la connexion à Gradio
        logger.info("1. Vérification de la connexion à Gradio...")
        if not self.collector.connect():
            logger.error(
                "✗ Impossible de se connecter à l'API Gradio. "
                f"URL: {self.collector.gradio_url}"
            )
            all_ok = False
        else:
            logger.info(
                f"✓ Connexion à Gradio OK ({self.collector.gradio_url})"
            )

        # 2. Vérifier la connexion à Elasticsearch
        logger.info("2. Vérification de la connexion à Elasticsearch...")
        if not self.indexer.connect():
            logger.error(
                "✗ Impossible de se connecter à Elasticsearch. "
                f"Host: {self.indexer.host}:{self.indexer.port}"
            )
            logger.error(
                "  Lancez Elasticsearch avec: make pipeline-elasticsearch-up"
            )
            all_ok = False
        else:
            logger.info(
                f"✓ Connexion à Elasticsearch OK "
                f"({self.indexer.host}:{self.indexer.port})"
            )

        # 3. Vérifier que les dépendances sont installées
        logger.info("3. Vérification des dépendances...")
        try:
            from gradio_client import Client  # noqa: F401
            logger.info("✓ gradio_client installé")
        except ImportError:
            logger.error(
                "✗ gradio_client non installé. "
                "Installez-le avec: pip install gradio-client"
            )
            all_ok = False

        try:
            from elasticsearch import Elasticsearch  # noqa: F401
            logger.info("✓ elasticsearch installé")
        except ImportError:
            logger.error(
                "✗ elasticsearch non installé. "
                "Installez-le avec: pip install elasticsearch"
            )
            all_ok = False

        if all_ok:
            logger.info("✓ Tous les pré-requis sont remplis")
        else:
            logger.error("✗ Certains pré-requis ne sont pas remplis")

        return all_ok

    def run_once(
        self,
        limit: Optional[int] = None,
        skip_prerequisites: bool = False
    ) -> dict:
        """
        Exécute le pipeline une seule fois.

        Args:
            limit: Nombre maximum de logs à récupérer.
                   Si None, récupère tous les logs disponibles (pagination automatique)
            skip_prerequisites: Ignore la vérification des pré-requis

        Returns:
            dict: Statistiques d'exécution
        """
        logger.info("Démarrage du pipeline (exécution unique)")

        # Vérifier les pré-requis
        if not skip_prerequisites:
            if not self.check_prerequisites():
                logger.error(
                    "Impossible de démarrer le pipeline: "
                    "pré-requis non satisfaits"
                )
                return {
                    "collected": 0,
                    "filtered": 0,
                    "indexed": 0,
                    "error": "Prerequisites check failed"
                }

        stats = {
            "collected": 0,
            "filtered": 0,
            "indexed": 0
        }

        try:
            # 1. Collecter les logs
            logger.info("Collecte des logs...")
            documents = self.collector.collect(limit=limit)
            stats["collected"] = len(documents)
            logger.info(f"{stats['collected']} documents collectés")

            if not documents:
                logger.info("Aucun nouveau log à traiter")
                return stats

            # 2. Filtrer les logs
            logger.info("Filtrage des logs...")
            filtered_documents = self.filter.filter(documents)
            stats["filtered"] = len(filtered_documents)
            logger.info(
                f"{stats['filtered']} documents filtrés "
                f"(sur {stats['collected']})"
            )

            # 3. Indexer dans Elasticsearch
            # IMPORTANT: Tous les logs vont dans ml-api-logs (documents)
            # Seuls les logs filtrés vont dans ml-api-message et ml-api-perfs
            logger.info("Indexation dans Elasticsearch...")
            indexed = self.indexer.index_documents(
                all_documents=documents,
                filtered_documents=filtered_documents
            )
            stats["indexed"] = indexed
            logger.info(f"{indexed} documents indexés")

        except Exception as e:
            logger.error(f"Erreur lors de l'exécution du pipeline: {e}")

        logger.info(
            f"Pipeline terminé - Collectés: {stats['collected']}, "
            f"Filtrés: {stats['filtered']}, "
            f"Indexés: {stats['indexed']}"
        )

        return stats

    def run_continuous(
        self,
        limit: Optional[int] = None,
        poll_interval: Optional[int] = None
    ) -> None:
        """
        Exécute le pipeline en continu.

        Args:
            limit: Nombre maximum de logs à récupérer à chaque itération.
                   Si None, récupère tous les logs disponibles (pagination automatique)
            poll_interval: Intervalle entre chaque exécution (secondes)
        """
        interval = poll_interval or config.poll_interval

        logger.info(
            f"Démarrage du pipeline en mode continu "
            f"(intervalle: {interval}s)"
        )

        # Vérifier les pré-requis une fois au démarrage
        if not self.check_prerequisites():
            logger.error(
                "Impossible de démarrer le pipeline: "
                "pré-requis non satisfaits"
            )
            return

        try:
            iteration = 0
            while True:
                iteration += 1
                logger.info(f"=== Itération {iteration} ===")
                # Ne pas revérifier les pré-requis à chaque itération
                self.run_once(limit=limit, skip_prerequisites=True)
                logger.info(f"Attente de {interval} secondes...")
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("Arrêt du pipeline (Ctrl+C)")
        except Exception as e:
            logger.error(f"Erreur fatale dans le pipeline: {e}")
        finally:
            self.close()

    def close(self) -> None:
        """Ferme les connexions."""
        logger.info("Fermeture des connexions...")
        self.indexer.close()
