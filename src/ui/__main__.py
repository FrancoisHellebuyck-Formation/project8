"""
Point d'entrée principal pour lancer l'interface Gradio.

Ce fichier permet de lancer l'interface via:
    python -m src.ui
"""

from .app import launch_ui

if __name__ == "__main__":
    launch_ui()
