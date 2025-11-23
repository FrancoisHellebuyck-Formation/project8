#!/usr/bin/env python3
"""
Script pour générer la documentation Sphinx.

Ce script permet de générer la documentation HTML du projet
en utilisant Sphinx et l'extension autodoc.

Usage:
    python scripts/generate_docs.py [--clean] [--open]

Options:
    --clean: Nettoie le répertoire de build avant la génération
    --open: Ouvre la documentation dans le navigateur après génération
"""

import argparse
import os
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path


def clean_build_dir(docs_dir: Path):
    """
    Nettoie le répertoire de build de la documentation.

    Args:
        docs_dir: Chemin vers le répertoire docs
    """
    build_dir = docs_dir / "_build"
    if build_dir.exists():
        print(f"🧹 Nettoyage de {build_dir}...")
        shutil.rmtree(build_dir)
        print("✅ Répertoire de build nettoyé")


def generate_docs(docs_dir: Path, clean: bool = False):
    """
    Génère la documentation HTML avec Sphinx.

    Args:
        docs_dir: Chemin vers le répertoire docs
        clean: Si True, nettoie avant de générer

    Returns:
        bool: True si la génération a réussi, False sinon
    """
    if clean:
        clean_build_dir(docs_dir)

    print("📚 Génération de la documentation Sphinx...")

    # Commande sphinx-build
    cmd = [
        "uv",
        "run",
        "sphinx-build",
        "-b",
        "html",
        str(docs_dir),
        str(docs_dir / "_build" / "html"),
    ]

    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        print("✅ Documentation générée avec succès!")
        return True
    except subprocess.CalledProcessError as e:
        print("❌ Erreur lors de la génération de la documentation:")
        print(e.stderr)
        return False


def open_docs(docs_dir: Path):
    """
    Ouvre la documentation dans le navigateur.

    Args:
        docs_dir: Chemin vers le répertoire docs
    """
    index_path = docs_dir / "_build" / "html" / "index.html"
    if not index_path.exists():
        print(f"❌ Fichier {index_path} introuvable")
        return

    print("🌐 Ouverture de la documentation dans le navigateur...")
    webbrowser.open(f"file://{index_path.absolute()}")


def main():
    """Point d'entrée principal du script."""
    parser = argparse.ArgumentParser(
        description="Génère la documentation Sphinx du projet"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Nettoie le répertoire de build avant la génération"
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Ouvre la documentation dans le navigateur après génération"
    )

    args = parser.parse_args()

    # Déterminer le chemin du répertoire docs
    project_root = Path(__file__).parent.parent
    docs_dir = project_root / "docs"

    if not docs_dir.exists():
        print(f"❌ Répertoire docs introuvable: {docs_dir}")
        sys.exit(1)

    # Changer vers le répertoire racine du projet
    os.chdir(project_root)

    # Générer la documentation
    success = generate_docs(docs_dir, clean=args.clean)

    if not success:
        sys.exit(1)

    # Ouvrir dans le navigateur si demandé
    if args.open:
        open_docs(docs_dir)

    print()
    print(f"📖 Documentation disponible dans: {docs_dir / '_build' / 'html'}")
    print(f"   Ouvrir avec: open {docs_dir / '_build' / 'html' / 'index.html'}")


if __name__ == "__main__":
    main()
