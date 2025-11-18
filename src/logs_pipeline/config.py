"""
Configuration du pipeline de logs.

Ce module définit la configuration du pipeline d'intégration
des logs vers Elasticsearch.
"""

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()


@dataclass
class PipelineConfig:
    """Configuration du pipeline de logs."""

    # Redis
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_db: int = int(os.getenv("REDIS_DB", "0"))
    redis_logs_key: str = os.getenv("REDIS_LOGS_KEY", "api_logs")

    # Elasticsearch
    elasticsearch_host: str = os.getenv("ELASTICSEARCH_HOST", "localhost")
    elasticsearch_port: int = int(os.getenv("ELASTICSEARCH_PORT", "9200"))
    elasticsearch_index: str = os.getenv(
        "ELASTICSEARCH_INDEX", "ml-api-logs"
    )

    # Gradio
    gradio_url: str = os.getenv(
        "GRADIO_URL", "https://francoisformation-oc-project8.hf.space"
    )
    hf_token: Optional[str] = os.getenv("HF_TOKEN", None)

    # Pipeline
    batch_size: int = int(os.getenv("PIPELINE_BATCH_SIZE", "100"))
    poll_interval: int = int(os.getenv("PIPELINE_POLL_INTERVAL", "10"))
    filter_pattern: str = os.getenv(
        "PIPELINE_FILTER_PATTERN", "API Call - POST /predict"
    )

    @property
    def redis_url(self) -> str:
        """URL de connexion Redis."""
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def elasticsearch_url(self) -> str:
        """URL de connexion Elasticsearch."""
        return f"http://{self.elasticsearch_host}:{self.elasticsearch_port}"


# Instance globale de configuration
config = PipelineConfig()
