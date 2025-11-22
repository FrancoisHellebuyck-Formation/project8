# Scripts du projet

Ce répertoire contient les scripts utilitaires pour le projet MLOps.

## Scripts disponibles

### `convert_to_onnx.py`

**Description**: Convertit le modèle scikit-learn (pickle) en ONNX pour améliorer la portabilité et la sécurité.

**Usage**:
```bash
# Conversion standard avec validation
python scripts/convert_to_onnx.py --validate

# Ou avec make
make convert-onnx

# Conversion rapide sans validation
make convert-onnx-quick
```

**Options**:
- `--input, -i`: Chemin du modèle pickle (défaut: `model/model.pkl`)
- `--output, -o`: Chemin de sortie ONNX (défaut: `model/model.onnx`)
- `--validate`: Valider le modèle après conversion
- `--n-features`: Nombre de features (défaut: 28)
- `--opset`: Version de l'opset ONNX (défaut: 12)

**Documentation**: Voir [docs/ONNX_MIGRATION.md](../docs/ONNX_MIGRATION.md)

### `check_api_coverage.py`

**Description**: Vérifie la couverture de tests de l'API et génère un rapport détaillé.

**Usage**:
```bash
python scripts/check_api_coverage.py --min-coverage 80
```

**Pré-requis**: Utilisé automatiquement par le pre-commit hook

## Installation des dépendances

Certains scripts nécessitent des dépendances supplémentaires:

```bash
# Pour convert_to_onnx.py
uv add onnx onnxruntime skl2onnx

# Toutes les dépendances de développement
uv sync --all-extras
```

## Développement

### Ajouter un nouveau script

1. Créer le fichier dans `scripts/`
2. Ajouter le shebang: `#!/usr/bin/env python3`
3. Rendre exécutable: `chmod +x scripts/mon_script.py`
4. Ajouter la docstring avec usage
5. Ajouter une commande Make si pertinent
6. Mettre à jour ce README

### Bonnes pratiques

- Toujours inclure une docstring complète
- Utiliser `argparse` pour les arguments
- Gérer les erreurs avec des messages clairs
- Ajouter des tests si le script est critique
- Documenter dans README.md

## Tests

Pour tester les scripts:

```bash
# Test du script de conversion ONNX
python scripts/convert_to_onnx.py --help
python scripts/convert_to_onnx.py --validate

# Test du script de couverture
python scripts/check_api_coverage.py --min-coverage 70
```

## Troubleshooting

### Script non exécutable

```bash
chmod +x scripts/nom_du_script.py
```

### Dépendances manquantes

```bash
uv sync
# ou pour un package spécifique
uv add nom_du_package
```

### Erreur de chemin

Tous les scripts doivent être exécutés depuis la racine du projet:
```bash
# ✅ Correct
python scripts/convert_to_onnx.py

# ❌ Incorrect
cd scripts && python convert_to_onnx.py
```

## Références

- [Documentation ONNX](../docs/ONNX_MIGRATION.md)
- [Documentation sécurité](../docs/SECURITY.md)
- [Architecture du projet](../docs/ARCHITECTURE.md)
