# Changelog - Système de Contrôle de Couverture Automatique

## [1.0.0] - 2025-01-21

### ✨ Ajouté

#### Workflow CI/CD
- **Vérification automatique de la couverture API** (≥85%)
  - Nouvelle étape `Check API coverage specifically` dans `.github/workflows/cicd.yml`
  - Génération automatique de rapport JSON de couverture
  - Affichage du résumé de couverture dans les logs CI/CD
  - Upload optionnel vers Codecov

- **Rapport de couverture détaillé**
  - Affichage console avec détail par fichier
  - Identification automatique des fichiers avec couverture insuffisante
  - Code de sortie approprié (fail si < 85%)

#### Commandes Makefile
- **`make test-coverage`** : Tests avec couverture globale (seuil: 80%)
  - Ajout du flag `--cov-fail-under=80`
  - Message d'erreur clair si échec

- **`make test-api-coverage`** (NOUVEAU) : Tests API avec couverture stricte (seuil: 85%)
  - Vérification ciblée sur `src/api/`
  - Génération de rapports HTML (`htmlcov-api/`) et JSON (`coverage-api.json`)
  - Résumé automatique console avec détail par fichier
  - Script Python inline pour parser et afficher les résultats

- **Mise à jour du help** : Documentation des nouvelles commandes avec seuils

#### Scripts
- **`scripts/check_api_coverage.py`** (NOUVEAU) : Script autonome de vérification
  - Support des arguments CLI (`--min-coverage`, `--strict`)
  - Exécution des tests avec pytest
  - Parsing du rapport JSON
  - Affichage formaté des résultats
  - Identification des fichiers avec faible couverture
  - Calcul du pourcentage manquant par fichier
  - Exit codes appropriés (0=succès, 1=échec)
  - Compatible avec pre-commit hooks

#### Configuration Pre-commit
- **`.pre-commit-config.yaml`** (NOUVEAU) : Hooks Git automatiques
  - Hook `check-api-coverage` : Vérifie la couverture avant commit
  - Hook `check-tests-pass` : Vérifie que tous les tests passent avant push
  - Hook `flake8` : Linting automatique
  - Hooks standards : trailing-whitespace, end-of-file-fixer, etc.
  - Déclenchement intelligent basé sur les fichiers modifiés

#### Configuration Pytest/Coverage
- **`pyproject.toml`** : Configuration de couverture améliorée
  - `fail_under = 80` : Seuil global par défaut
  - `show_missing = true` : Afficher les lignes manquantes
  - `precision = 2` : Précision à 2 décimales
  - `[tool.coverage.paths]` : Configuration des chemins sources

#### Documentation
- **`docs/COVERAGE_GUIDELINES.md`** (NOUVEAU - 360 lignes)
  - Guide complet d'utilisation
  - Seuils de couverture (globale 80%, API 85%)
  - Commandes et scripts disponibles
  - Configuration détaillée
  - Bonnes pratiques de développement
  - Interprétation des rapports
  - Ajout de tests étape par étape
  - Résolution de problèmes
  - Objectifs court/moyen/long terme
  - Conseils TDD, mocking, fixtures

- **`docs/COVERAGE_AUTOMATION.md`** (NOUVEAU - 500 lignes)
  - Vue d'ensemble du système
  - Composants mis en place (détail technique)
  - Flux de travail (développement local + CI/CD)
  - Diagrammes Mermaid
  - Exemples d'utilisation pratiques
  - Métriques et rapports générés
  - Résolution de problèmes détaillée
  - Bonnes pratiques avec exemples de code
  - Statistiques et évolution
  - Checklist d'activation

- **`CHANGELOG_COVERAGE.md`** (NOUVEAU - ce fichier)
  - Historique complet des changements
  - Versions et dates
  - Détail de chaque ajout/modification

### 🔧 Modifié

#### Workflow CI/CD (`.github/workflows/cicd.yml`)
- Ligne 46 : Ajout de `--cov-fail-under=80` aux tests globaux
- Lignes 48-56 : Upload vers Codecov (optionnel)
- Lignes 58-88 : Vérification spécifique de la couverture API
  - Exécution de pytest avec `--cov=src/api`
  - Génération de `coverage-api.json`
  - Parsing et affichage du résumé Python

#### Makefile
- Ligne 39 : Description de `test-coverage` mise à jour (ajout "≥80%")
- Ligne 41 : Ajout de `test-api-coverage` dans le help
- Lignes 147-154 : `test-coverage` modifié avec `--cov-fail-under=80`
- Lignes 156-161 : `test-api` modifié pour tester `test_api.py` et `test_main.py`
- Lignes 163-192 : `test-api-coverage` (NOUVEAU) avec vérification stricte

#### Configuration Pytest (`pyproject.toml`)
- Lignes 91-101 : Ajout de configuration de rapport de couverture
  - `fail_under`, `show_missing`, `precision`
  - `[tool.coverage.paths]` pour chemins sources

#### .gitignore
- Ligne 173 : Ajout de `htmlcov-api/` (rapport HTML API)
- Ligne 181 : Ajout de `coverage-api.json` (rapport JSON API)

### 📋 Fichiers Créés

```
scripts/check_api_coverage.py           180 lignes  - Script de vérification
.pre-commit-config.yaml                  45 lignes  - Configuration hooks
docs/COVERAGE_GUIDELINES.md             360 lignes  - Guide utilisateur
docs/COVERAGE_AUTOMATION.md             500 lignes  - Documentation technique
CHANGELOG_COVERAGE.md                   250 lignes  - Ce fichier
```

### 📊 Impact

#### Qualité de Code
- ✅ Couverture globale minimum garantie : 80%
- ✅ Couverture API minimum garantie : 85%
- ✅ Détection automatique des régressions de couverture
- ✅ Blocage des commits avec couverture insuffisante (optionnel)

#### Développement
- ✅ Feedback immédiat sur la couverture (local + CI/CD)
- ✅ Rapports HTML interactifs pour identifier les lignes non testées
- ✅ Commandes simples (`make test-api-coverage`)
- ✅ Documentation complète et accessible

#### CI/CD
- ✅ Vérification automatique sur chaque push/PR
- ✅ Rapports de couverture dans les logs
- ✅ Échec de build si couverture insuffisante
- ✅ Intégration Codecov optionnelle

### 🎯 Seuils de Couverture

| Scope | Seuil | Commande | Status |
|-------|-------|----------|--------|
| Global | ≥80% | `make test-coverage` | ✅ Actif |
| API | ≥85% | `make test-api-coverage` | ✅ Actif |
| Model | - | `make test-model` | ℹ️ Pas de seuil |
| Proxy | - | `make test-proxy` | ℹ️ Pas de seuil |

### 📦 Dépendances

Aucune dépendance Python supplémentaire requise. Utilise :
- `pytest` (déjà installé)
- `pytest-cov` (déjà installé)
- `pre-commit` (optionnel, recommandé)

### 🚀 Activation

```bash
# 1. Installer pre-commit (optionnel)
pip install pre-commit
pre-commit install

# 2. Vérifier la couverture actuelle
make test-api-coverage

# 3. Si nécessaire, ajouter des tests jusqu'à atteindre 85%

# 4. Committer (avec hooks actifs)
git add .
git commit -m "Add coverage automation"

# 5. Push (déclenche CI/CD)
git push
```

### 📝 Notes de Migration

#### Pour les Développeurs

**Avant** :
```bash
make test  # Pas de vérification de couverture
git commit
git push
```

**Maintenant** :
```bash
make test-coverage      # Vérifie couverture globale ≥80%
make test-api-coverage  # Vérifie couverture API ≥85%
git commit              # Pre-commit hook vérifie la couverture
git push                # CI/CD vérifie la couverture
```

**Changement de comportement** :
- ⚠️ Les commits peuvent être bloqués si couverture < 85% (avec pre-commit)
- ⚠️ Les PRs peuvent être refusées si couverture < seuil (CI/CD)
- ✅ Feedback immédiat sur la qualité du code

#### Pour le CI/CD

**Changements dans le workflow** :
- ✅ Étape supplémentaire : "Check API coverage"
- ✅ Étape supplémentaire : "Display API coverage summary"
- ⚠️ Build échoue si couverture API < 85%

**Temps d'exécution** :
- +30-60s pour la vérification de couverture API
- Négligeable car tests déjà exécutés en parallèle

### 🔗 Liens

- [Guide d'utilisation](docs/COVERAGE_GUIDELINES.md)
- [Documentation technique](docs/COVERAGE_AUTOMATION.md)
- [Workflow CI/CD](.github/workflows/cicd.yml)
- [Configuration pre-commit](.pre-commit-config.yaml)

### 👥 Contributeurs

- Project8 Team

### 📅 Roadmap

#### Version 1.1 (Futur)
- [ ] Intégration SonarQube
- [ ] Badges de couverture dans README
- [ ] Graphiques d'évolution de la couverture
- [ ] Alertes Slack/Email si couverture baisse

#### Version 1.2 (Futur)
- [ ] Couverture par endpoint (routes individuelles)
- [ ] Tests de mutation (mutation testing)
- [ ] Rapport de couverture différentiel (PR uniquement)

---

## [0.9.0] - Avant 2025-01-21

### État Initial

- ✅ Tests existants mais sans vérification de couverture automatique
- ✅ Commande `make test-coverage` basique (sans seuil)
- ❌ Pas de seuil minimum défini
- ❌ Pas de vérification en CI/CD
- ❌ Pas de documentation sur la couverture
- ❌ Pas de pre-commit hooks

---

**Format du changelog** : [Keep a Changelog](https://keepachangelog.com/)
**Versioning** : [Semantic Versioning](https://semver.org/)
