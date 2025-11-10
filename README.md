# Projet 8 - MLOps : API de Prédiction ML

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![Redis](https://img.shields.io/badge/Redis-5.0+-red.svg)](https://redis.io/)

API REST pour effectuer des prédictions avec un modèle de machine learning, avec gestion des logs dans Redis.

## 📋 Table des matières

- [Architecture](#architecture)
- [Fonctionnalités](#fonctionnalités)
- [Installation](#installation)
- [Utilisation](#utilisation)
- [Documentation](#documentation)
- [Développement](#développement)
- [Tests](#tests)
- [Déploiement](#déploiement)

## 🏗️ Architecture

Le projet est structuré en 3 parties principales :

### 1. Modèle ML (`./model`)
- Modèle de machine learning entraîné
- Chargé une seule fois au démarrage (pattern Singleton)
- Feature engineering automatique

### 2. API FastAPI (`./src/api`)
- API REST pour interroger le modèle
- Endpoints : `/predict`, `/health`, `/logs`
- Logs stockés dans Redis

### 3. Front-end Gradio (`./src/ui`) - *À venir*
- Interface utilisateur Gradio
- Communique avec l'API FastAPI

### Infrastructure

- **Docker 1** : API + Modèle ML
- **Docker 2** : Interface Gradio
- **Redis** : Cache pour les logs

## ✨ Fonctionnalités

### API
- ✅ Prédictions ML via endpoint REST
- ✅ Feature engineering automatique (14 → 28 features)
- ✅ Logs stockés dans Redis
- ✅ Health check endpoint
- ✅ Documentation interactive (Swagger/ReDoc)
- ✅ Validation des données avec Pydantic
- ✅ CORS configuré

### Modèle
- ✅ Chargement Singleton (une seule fois)
- ✅ Calcul automatique des features dérivées
- ✅ Support predict() et predict_proba()
- ✅ Chemin du modèle paramétrable (.env)

### Logs
- ✅ Stockage dans Redis (FIFO)
- ✅ Consultation via endpoint `/logs`
- ✅ Statistiques disponibles
- ✅ Filtrage par niveau et limite

## 🚀 Installation

### Prérequis

- Python 3.13+
- Docker (pour Redis)
- make (optionnel mais recommandé)

### Installation rapide

```bash
# Cloner le repository
git clone <url>
cd project8

# Configuration initiale (installe tout + lance Redis)
make dev

# Dans un autre terminal, lancer l'API
make run-api
```

### Installation manuelle

```bash
# Créer l'environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# ou
.venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -e .

# Copier le fichier .env
cp .env.example .env

# Lancer Redis
docker run -d -p 6379:6379 redis:latest

# Lancer l'API
uvicorn src.api.main:app --reload
```

## 📖 Utilisation

### Commandes Make

```bash
# Aide
make help

# Installation
make install          # Production
make install-dev      # Développement

# Développement
make run-api          # Lancer l'API
make run-redis        # Lancer Redis
make dev             # Environnement complet

# Tests et qualité
make lint            # Vérifier le code
make test            # Lancer les tests
make test-coverage   # Tests avec couverture

# Docker
make docker-build    # Construire les images
make docker-up       # Lancer les conteneurs
make docker-down     # Arrêter les conteneurs

# Utilitaires
make health          # Vérifier l'API
make predict-test    # Tester une prédiction
make logs           # Afficher les logs
```

### API Endpoints

#### Health Check
```bash
curl http://localhost:8000/health
```

#### Prédiction
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "AGE": 65,
    "GENDER": 1,
    "SMOKING": 1,
    "ALCOHOL CONSUMING": 1,
    "PEER_PRESSURE": 0,
    "YELLOW_FINGERS": 1,
    "ANXIETY": 0,
    "FATIGUE": 1,
    "ALLERGY": 0,
    "WHEEZING": 1,
    "COUGHING": 1,
    "SHORTNESS OF BREATH": 1,
    "SWALLOWING DIFFICULTY": 0,
    "CHEST PAIN": 1
  }'
```

#### Logs
```bash
# Récupérer les logs
curl http://localhost:8000/logs?limit=50

# Statistiques
curl http://localhost:8000/logs/stats
```

### Documentation interactive

- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc

## 📚 Documentation

- [CLAUDE.md](CLAUDE.md) - Règles de développement et architecture
- [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - Documentation complète de l'API
- [FEATURE_ENGINEERING.md](FEATURE_ENGINEERING.md) - Feature engineering automatique
- [ENV_VARIABLES.md](ENV_VARIABLES.md) - Variables d'environnement
- [MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md) - Guide du Makefile

## 🛠️ Développement

### Structure du projet

```
project8/
├── src/
│   ├── api/              # API FastAPI
│   │   ├── main.py       # Application principale
│   │   ├── schemas.py    # Modèles Pydantic
│   │   └── redis_logger.py
│   ├── model/            # Package modèle ML
│   │   ├── model_loader.py
│   │   ├── predictor.py
│   │   └── feature_engineering.py
│   └── config.py         # Configuration (.env)
├── model/                # Modèle ML entraîné
│   └── model.pkl
├── tests/                # Tests
├── .env                  # Variables d'environnement (ne pas commiter)
├── .env.example          # Template .env
├── pyproject.toml        # Dépendances
├── Makefile              # Commandes utiles
└── README.md
```

### Standards de code

- **Longueur de ligne** : 88 caractères max
- **Linting** : flake8 (voir `.flake8`)
- **Style** : PEP 8
- **Tests** : pytest

### Workflow de développement

```bash
# 1. Créer une branche
git checkout -b feature/ma-feature

# 2. Développer et tester
make lint
make test

# 3. Commiter
git add .
git commit -m "feat: ma nouvelle fonctionnalité"

# 4. Push
git push origin feature/ma-feature
```

### Variables d'environnement

Voir [ENV_VARIABLES.md](ENV_VARIABLES.md) pour la liste complète.

Principales variables :
```env
MODEL_PATH=./model/model.pkl
API_HOST=0.0.0.0
API_PORT=8000
REDIS_HOST=localhost
REDIS_PORT=6379
```

## 🧪 Tests

```bash
# Tous les tests
make test

# Avec couverture
make test-coverage

# Ouvrir le rapport
open htmlcov/index.html  # macOS
```

## 🐳 Déploiement

### Docker Compose

```bash
# Construire et lancer
make docker-build
make docker-up

# Vérifier
make health

# Arrêter
make docker-down
```

### CI/CD

Pipeline GitHub Actions :
- Linting avec flake8
- Tests avec pytest
- Build des images Docker
- Déploiement automatisé

```bash
# Commande CI
make ci
```

## 📝 Features du modèle

### Features d'entrée (14)

L'utilisateur fournit uniquement ces 14 features :
- AGE, GENDER, SMOKING, ALCOHOL CONSUMING
- PEER_PRESSURE, YELLOW_FINGERS, ANXIETY, FATIGUE
- ALLERGY, WHEEZING, COUGHING, SHORTNESS OF BREATH
- SWALLOWING DIFFICULTY, CHEST PAIN

### Features dérivées (14)

Calculées automatiquement par le système :
- SMOKING_x_AGE, SMOKING_x_ALCOHOL
- RESPIRATORY_SYMPTOMS, TOTAL_SYMPTOMS
- BEHAVIORAL_RISK_SCORE, SEVERE_SYMPTOMS
- AGE_GROUP, HIGH_RISK_PROFILE
- AGE_SQUARED, CANCER_TRIAD
- SMOKER_WITH_RESP_SYMPTOMS, ADVANCED_SYMPTOMS
- SYMPTOMS_PER_AGE, RESP_SYMPTOM_RATIO

Voir [FEATURE_ENGINEERING.md](FEATURE_ENGINEERING.md) pour plus de détails.

## 🤝 Contribution

1. Fork le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commiter les changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📄 Licence

Ce projet fait partie du parcours OpenClassrooms MLOps.

## 👥 Auteurs

- OpenClassrooms - Projet 8

## 🔗 Liens utiles

- [Documentation FastAPI](https://fastapi.tiangolo.com/)
- [Documentation Redis](https://redis.io/docs/)
- [Pydantic](https://docs.pydantic.dev/)
- [scikit-learn](https://scikit-learn.org/)
