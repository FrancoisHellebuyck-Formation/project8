"""
Package logs_pipeline - Pipeline d'intégration des logs dans Elasticsearch.

Ce package collecte les logs de l'API (depuis Redis), filtre les logs
de prédiction (POST /predict) et les indexe dans Elasticsearch.

Le pipeline fonctionne de manière autonome et non intrusive.
"""

from .pipeline import LogsPipeline

__all__ = ["LogsPipeline"]
