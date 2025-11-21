"""
Package proxy pour connecter Gradio (7860) à FastAPI (8000).

Ce package fournit un client proxy qui expose tous les endpoints
de l'API FastAPI via une interface Gradio accessible.
"""

from .client import APIProxyClient
from .gradio_app import create_proxy_interface

__all__ = ["APIProxyClient", "create_proxy_interface"]
