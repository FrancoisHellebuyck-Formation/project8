"""
Collecteur de logs depuis l'API Gradio HuggingFace.

Ce module récupère les logs via l'endpoint Gradio /logs_api
et les transforme en documents structurés.
"""

import logging
import re
from datetime import datetime
from typing import Dict, List, Optional

from .config import config

logger = logging.getLogger(__name__)

# Import optionnel de gradio_client
try:
    from gradio_client import Client
    GRADIO_CLIENT_AVAILABLE = True
except ImportError:
    GRADIO_CLIENT_AVAILABLE = False


class LogCollector:
    """Collecteur de logs depuis l'API Gradio HuggingFace."""

    def __init__(
        self,
        gradio_url: Optional[str] = None,
        hf_token: Optional[str] = None
    ):
        """
        Initialise le collecteur.

        Args:
            gradio_url: URL de l'API Gradio
            hf_token: Token HuggingFace (optionnel)
        """
        if not GRADIO_CLIENT_AVAILABLE:
            raise ImportError(
                "gradio_client n'est pas installé. "
                "Installez-le avec: pip install gradio-client"
            )

        self.gradio_url = gradio_url or config.gradio_url
        self.hf_token = hf_token or config.hf_token
        self.client: Optional[Client] = None
        self.processed_logs: set = set()

    def connect(self) -> bool:
        """
        Teste la connexion à l'API Gradio.

        Returns:
            bool: True si connecté, False sinon
        """
        try:
            self.client = Client(self.gradio_url, hf_token=self.hf_token)
            return True
        except Exception as e:
            logger.error(f"Impossible de se connecter à Gradio: {e}")
            return False

    def fetch_logs(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Récupère les logs depuis l'API Gradio avec pagination automatique.

        Args:
            limit: Nombre maximum de logs à récupérer.
                   Si None, récupère tous les logs disponibles

        Returns:
            List[Dict]: Liste de tous les logs récupérés
        """
        try:
            if self.client is None:
                if not self.connect():
                    return []

            all_logs = []
            offset = 0
            batch_size = 100  # Limite maximale par requête de l'API

            # Si limit est spécifié, on s'arrête à cette limite
            max_logs = limit if limit is not None else float('inf')

            # Essayer d'abord avec le paramètre offset (nouvelle API)
            try:
                while len(all_logs) < max_logs:
                    # Calculer combien de logs récupérer dans ce batch
                    remaining = max_logs - len(all_logs)
                    current_limit = min(batch_size, remaining)

                    # Appeler l'endpoint /logs_api avec offset
                    result = self.client.predict(
                        limit=int(current_limit),
                        offset=offset,
                        api_name="/logs_api"
                    )

                    # result est un dict avec 'total' et 'logs'
                    batch_logs = result.get('logs', [])
                    total = result.get('total', 0)

                    if not batch_logs:
                        # Plus de logs disponibles
                        break

                    all_logs.extend(batch_logs)
                    offset += len(batch_logs)

                    logger.info(
                        f"Récupéré batch de {len(batch_logs)} logs "
                        f"(offset: {offset - len(batch_logs)}, "
                        f"total disponible: {total})"
                    )

                    # Si on a récupéré moins de logs que demandé,
                    # c'est qu'il n'y en a plus
                    if len(batch_logs) < current_limit:
                        break

            except Exception as e:
                # Si l'offset n'est pas supporté, utiliser l'ancienne API
                if "offset" in str(e).lower():
                    logger.warning(
                        "L'API ne supporte pas la pagination "
                        "(paramètre offset). Récupération limitée à 100 logs."
                    )
                    # Fallback: récupérer sans offset
                    fetch_limit = min(limit if limit else 100, 100)
                    result = self.client.predict(
                        limit=int(fetch_limit),
                        api_name="/logs_api"
                    )
                    all_logs = result.get('logs', [])
                else:
                    raise

            logger.info(
                f"Récupération terminée: {len(all_logs)} logs au total"
            )
            return all_logs

        except Exception as e:
            logger.error(f"Erreur lors de la récupération des logs: {e}")
            return []

    def parse_log_entry(self, log_str: str) -> Optional[Dict]:
        """
        Parse une entrée de log et extrait les informations.

        Format attendu:
        2025-01-15 10:30:45 - api - INFO - [uuid] API Call - POST /predict ...

        Args:
            log_str: Chaîne de log brute

        Returns:
            Optional[Dict]: Document structuré ou None
        """
        try:
            # Pattern pour parser le log
            # Format: timestamp - name - level - message
            pattern = (
                r'^(?P<timestamp>[\d-]+ [\d:]+) - '
                r'(?P<logger>\w+) - '
                r'(?P<level>\w+) - '
                r'(?P<message>.+)$'
            )

            match = re.match(pattern, log_str)
            if not match:
                return None

            groups = match.groupdict()

            # Parser le timestamp
            try:
                timestamp = datetime.strptime(
                    groups['timestamp'],
                    '%Y-%m-%d %H:%M:%S'
                )
            except ValueError:
                timestamp = datetime.utcnow()

            # Extraire transaction_id si présent
            transaction_id = None
            message = groups['message']
            transaction_pattern = r'^\[([a-f0-9-]+)\]\s+'
            transaction_match = re.match(transaction_pattern, message)
            if transaction_match:
                transaction_id = transaction_match.group(1)
                message = re.sub(transaction_pattern, '', message)

            # Créer le document
            document = {
                '@timestamp': timestamp.isoformat(),
                'level': groups['level'],
                'logger': groups['logger'],
                'message': message,
                'raw_log': log_str
            }

            if transaction_id:
                document['transaction_id'] = transaction_id

            # Extraire des données supplémentaires du message si disponible
            self._extract_additional_fields(document, message)

            return document

        except Exception as e:
            logger.warning(f"Impossible de parser le log: {e}")
            return None

    def _extract_additional_fields(
        self, document: Dict, message: str
    ) -> None:
        """
        Extrait des champs supplémentaires du message.

        Args:
            document: Document à enrichir
            message: Message de log
        """
        # Extraire méthode et path
        api_call_pattern = r'API Call - (?P<method>\w+) (?P<path>/[\w/]+)'
        match = re.search(api_call_pattern, message)
        if match:
            document['http_method'] = match.group('method')
            document['http_path'] = match.group('path')

        # Extraire status code
        status_pattern = r'Status: (\d+)'
        match = re.search(status_pattern, message)
        if match:
            document['status_code'] = int(match.group(1))

        # Extraire execution time
        time_pattern = r'Time: ([\d.]+)ms'
        match = re.search(time_pattern, message)
        if match:
            document['execution_time_ms'] = float(match.group(1))

        # Extraire input data (JSON)
        input_pattern = r'Input: ({.+?})'
        match = re.search(input_pattern, message)
        if match:
            try:
                import json
                document['input_data'] = json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Extraire result data (JSON)
        result_pattern = r'Result: ({.+?})$'
        match = re.search(result_pattern, message)
        if match:
            try:
                import json
                document['result'] = json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

    def collect(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Collecte les logs depuis l'API Gradio avec pagination automatique.

        Args:
            limit: Nombre maximum de logs à récupérer.
                   Si None, récupère tous les logs disponibles

        Returns:
            List[Dict]: Liste de documents structurés (déjà parsés par l'API)
        """
        logs = self.fetch_logs(limit)
        documents = []

        for log_entry in logs:
            # log_entry est déjà un dict avec timestamp, level, message, data
            # On le transforme au format Elasticsearch

            # Créer un hash unique pour identifier les logs déjà traités
            log_hash = f"{log_entry.get('timestamp')}_{log_entry.get('message')}"
            if log_hash in self.processed_logs:
                continue

            # Convertir le timestamp au format ISO 8601
            timestamp_str = log_entry.get('timestamp', '')
            if timestamp_str:
                try:
                    # Parser le format '2025-11-15 09:27:29'
                    dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                    # Convertir en ISO 8601
                    timestamp_str = dt.isoformat() + 'Z'
                except ValueError:
                    # Si le parsing échoue, garder la valeur originale
                    pass

            # Transformer au format Elasticsearch
            document = {
                '@timestamp': timestamp_str,
                'level': log_entry.get('level', ''),
                'message': log_entry.get('message', ''),
            }

            # Ajouter les données supplémentaires si présentes
            if log_entry.get('data'):
                data = log_entry['data']
                # Extraire les champs importants
                if 'method' in data:
                    document['http_method'] = data['method']
                if 'path' in data:
                    document['http_path'] = data['path']
                if 'status_code' in data:
                    document['status_code'] = data['status_code']
                if 'execution_time_ms' in data:
                    document['execution_time_ms'] = data['execution_time_ms']
                if 'transaction_id' in data:
                    document['transaction_id'] = data['transaction_id']
                if 'input_data' in data:
                    document['input_data'] = data['input_data']
                if 'result' in data:
                    document['result'] = data['result']

            documents.append(document)
            self.processed_logs.add(log_hash)

        return documents
