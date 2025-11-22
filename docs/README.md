# Documentation Sphinx

Ce répertoire contient la documentation générée automatiquement du projet ML API.

## Génération de la documentation

### Avec Make (recommandé)

```bash
# Générer la documentation
make docs

# Nettoyer et régénérer
make docs-clean

# Générer et ouvrir dans le navigateur
make docs-open
```

### Avec le script Python

```bash
# Génération simple
python scripts/generate_docs.py

# Avec nettoyage
python scripts/generate_docs.py --clean

# Ouvrir dans le navigateur
python scripts/generate_docs.py --open
```

## Structure

```
docs/
├── conf.py              # Configuration Sphinx
├── index.rst            # Page d'accueil
├── modules/             # Documentation des modules
│   ├── api.rst          # Module API
│   ├── model.rst        # Module Modèle
│   ├── ui.rst           # Module UI
│   ├── simulator.rst    # Module Simulateur
│   └── logs_pipeline.rst # Module Pipeline de logs
├── _build/              # Documentation générée (ignoré par git)
├── _static/             # Fichiers statiques
└── _templates/          # Templates personnalisés
```

## Accès à la documentation

Une fois générée, la documentation est disponible à :
```
docs/_build/html/index.html
```

Ouvrez ce fichier dans votre navigateur pour naviguer dans la documentation complète du projet.

## Configuration

La configuration Sphinx se trouve dans [conf.py](conf.py) et inclut :

- **Extensions** : autodoc, napoleon, viewcode, intersphinx, autodoc-typehints
- **Thème** : sphinx_rtd_theme (Read the Docs)
- **Support** : Google-style et NumPy-style docstrings
- **Type hints** : Affichés dans les descriptions

## Mise à jour

La documentation est générée automatiquement à partir des docstrings du code source.
Pour mettre à jour la documentation :

1. Modifiez les docstrings dans le code
2. Régénérez la documentation avec `make docs`
3. Vérifiez le résultat dans `docs/_build/html/`
