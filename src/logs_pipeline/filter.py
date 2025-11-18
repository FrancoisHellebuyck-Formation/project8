"""
Filtre de logs pour le pipeline.

Ce module filtre les logs selon un pattern défini dans la configuration.
Par défaut, seuls les logs contenant "API Call - POST /predict" sont gardés.
"""

import logging
from typing import Dict, List

from .config import config

logger = logging.getLogger(__name__)


class LogFilter:
    """Filtre les logs selon un pattern défini."""

    def __init__(self, pattern: str = None):
        """
        Initialise le filtre.

        Args:
            pattern: Pattern à rechercher dans les logs
        """
        self.pattern = pattern or config.filter_pattern

    def filter(self, documents: List[Dict]) -> List[Dict]:
        """
        Filtre les documents selon le pattern.

        Args:
            documents: Liste de documents à filtrer

        Returns:
            List[Dict]: Documents filtrés
        """
        filtered = []

        for doc in documents:
            if self._matches_pattern(doc):
                filtered.append(doc)

        logger.info(
            f"Filtrage: {len(filtered)}/{len(documents)} "
            f"documents correspondent au pattern '{self.pattern}'"
        )

        return filtered

    def _matches_pattern(self, document: Dict) -> bool:
        """
        Vérifie si un document correspond au pattern.

        Args:
            document: Document à vérifier

        Returns:
            bool: True si le document correspond au pattern
        """
        # Vérifier dans le message
        message = document.get('message', '')
        if self.pattern in message:
            return True

        # Vérifier aussi dans raw_log si présent
        raw_log = document.get('raw_log', '')
        if self.pattern in raw_log:
            return True

        # Vérifier le path HTTP si présent
        http_path = document.get('http_path', '')
        http_method = document.get('http_method', '')
        if http_path == '/predict' and http_method == 'POST':
            return True

        return False
