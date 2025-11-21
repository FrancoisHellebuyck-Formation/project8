# Architecture Technique du Projet MLOps

## Vue d'ensemble

Ce document décrit l'architecture technique complète du projet, incluant les composants, les flux de données et les interactions entre les différents services.

## Table des matières

- [Architecture globale](#architecture-globale)
- [Composants principaux](#composants-principaux)
- [Flux de données](#flux-de-données)
- [Infrastructure Docker](#infrastructure-docker)
- [Pipeline de logs](#pipeline-de-logs)
- [Monitoring et performance](#monitoring-et-performance)
- [Sécurité et scalabilité](#sécurité-et-scalabilité)

## Architecture globale

```
┌─────────────────────────────────────────────────────────────────────┐
│                         UTILISATEUR FINAL                            │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ↓
        ┌──────────────────────────────────────────┐
        │                                          │
        ↓                                          ↓
┌──────────────┐                          ┌──────────────┐
│   Gradio UI  │                          │  REST Client │
│  (Port 7860) │                          │   (cURL/HTTP)│
└──────────────┘                          └──────────────┘
        │                                          │
        │              HTTP POST /predict          │
        └──────────────────┬──────────────────────┘
                           ↓
                   ┌──────────────┐
                   │  FastAPI API │
                   │  (Port 8000) │
                   └──────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ↓                  ↓                  ↓
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ Redis Cache  │   │  ML Model    │   │  Monitoring  │
│ (Port 6379)  │   │  (Singleton) │   │  (cProfile)  │
└──────────────┘   └──────────────┘   └──────────────┘
        │
        ↓
┌──────────────────────────────────────────────────────┐
│              PIPELINE LOGS                           │
│  ┌──────────┐   ┌──────────┐   ┌──────────────┐    │
│  │Collector │ → │  Filter  │ → │   Indexer    │    │
│  └──────────┘   └──────────┘   └──────────────┘    │
└──────────────────────────────────────────────────────┘
                           ↓
                   ┌──────────────┐
                   │Elasticsearch │
                   │  (Port 9200) │
                   └──────────────┘
                           │
                           ↓
                   ┌──────────────┐
                   │    Kibana    │
                   │  (Port 5601) │
                   └──────────────┘
```

## Composants principaux

### 1. Interface utilisateur (Gradio)

**Localisation** : `src/ui/app.py`

**Responsabilités** :
- Interface web intuitive pour les utilisateurs finaux
- Formulaire de saisie des données patient (14 features)
- Communication avec l'API FastAPI
- Affichage des résultats de prédiction

**Technologies** :
- Gradio 4.0+
- Python 3.13+

**Endpoints exposés** :
- `/` : Interface principale
- `/logs_api` : Endpoint pour le pipeline de logs

**Flux de données** :
```
Utilisateur → Formulaire Gradio → Validation → HTTP POST → API FastAPI
                                                                  ↓
Utilisateur ← Affichage résultat ← JSON Response ← Prédiction ML ←
```

### 2. API REST (FastAPI)

**Localisation** : `src/api/main.py`

**Responsabilités** :
- Exposition des endpoints REST
- Validation des données (Pydantic)
- Orchestration des prédictions
- Gestion des logs (Redis)
- Monitoring des performances

**Endpoints** :

| Endpoint | Méthode | Description | Documentation |
|----------|---------|-------------|---------------|
| `/` | GET | Informations API | [API_DOCUMENTATION.md](API_DOCUMENTATION.md) |
| `/health` | GET | Health check | [API_DOCUMENTATION.md](API_DOCUMENTATION.md) |
| `/predict` | POST | Prédiction simple | [API_DOCUMENTATION.md](API_DOCUMENTATION.md) |
| `/predict_proba` | POST | Prédiction avec probabilités | [API_DOCUMENTATION.md](API_DOCUMENTATION.md) |
| `/logs` | GET | Récupération des logs | [API_DOCUMENTATION.md](API_DOCUMENTATION.md) |
| `/logs` | DELETE | Suppression des logs Redis | [CLEAR_LOGS_ENDPOINT.md](CLEAR_LOGS_ENDPOINT.md) |
| `/logs/stats` | GET | Statistiques des logs | [API_DOCUMENTATION.md](API_DOCUMENTATION.md) |

**Middlewares** :
- CORS (toutes origines en développement)
- Logging middleware (transaction ID, timing)
- Performance monitoring (cProfile)

**Configuration** :
```python
# Variables d'environnement (.env)
MODEL_PATH=./model/model.pkl
API_HOST=0.0.0.0
API_PORT=8000
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
LOG_TO_REDIS=true
REDIS_LOGS_MAX_SIZE=1000
ENABLE_PERFORMANCE_MONITORING=true
```

### 3. Modèle ML (scikit-learn)

**Localisation** : `src/model/`

**Architecture** :
```
model_loader.py    → Singleton pattern pour chargement unique
predictor.py       → Orchestration prédiction + feature engineering
feature_engineering.py → Calcul des 14 features dérivées
```

**Pattern Singleton** :
```python
class ModelLoader:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_model()
        return cls._instance
```

**Features** :

| Type | Nombre | Description |
|------|--------|-------------|
| **Entrée** | 14 | Fournies par l'utilisateur |
| **Dérivées** | 14 | Calculées automatiquement |
| **Total** | 28 | Utilisées par le modèle |

Détails : [FEATURE_ENGINEERING.md](FEATURE_ENGINEERING.md)

**Processus de prédiction** :
```
Input (14 features)
    → Feature Engineering (+ 14 features)
    → Total (28 features)
    → Model.predict()
    → Prédiction (0/1) + Probabilité
```

### 4. Cache Redis

**Localisation** : Redis standalone (Docker ou local)

**Responsabilités** :
- Stockage temporaire des logs API
- FIFO (First In First Out) avec limite configurable
- Consultation via endpoint `/logs`
- Source de données pour le pipeline Elasticsearch

**Structure des logs** :
```json
{
  "timestamp": "2024-11-20T10:30:45.123456",
  "level": "INFO",
  "message": "[transaction_id] POST /predict - 200 - 45ms - input - result",
  "data": {
    "transaction_id": "uuid",
    "input_data": {...},
    "result": {...},
    "performance_metrics": {...}
  }
}
```

**Configuration** :
- Limite : 1000 logs (configurable via `REDIS_LOGS_MAX_SIZE`)
- Clé Redis : `api_logs`
- Format : Liste (LPUSH/LRANGE)

### 5. Pipeline de logs Elasticsearch

**Localisation** : `src/logs_pipeline/`

**Architecture** :
```
collector.py  →  Récupération des logs depuis Redis ou Gradio
     ↓
filter.py     →  Filtrage des logs pertinents
     ↓
indexer.py    →  Triple indexation Elasticsearch
     ↓
pipeline.py   →  Orchestration du processus complet
```

**Flux détaillé** :
```
┌─────────────────────────────────────────────────────────────────┐
│                    SOURCES DE LOGS                              │
├────────────────────────┬────────────────────────────────────────┤
│    Redis (API logs)    │  Gradio (/logs_api endpoint)          │
└────────────────────────┴────────────────────────────────────────┘
                              ↓
                    ┌─────────────────┐
                    │   COLLECTOR     │
                    │  - Connexion    │
                    │  - Déduplication│
                    │  - Parsing      │
                    └─────────────────┘
                              ↓
                    ┌─────────────────┐
                    │     FILTER      │
                    │  - Pattern match│
                    │  - HTTP method  │
                    │  - Performance  │
                    └─────────────────┘
                              ↓
                    ┌─────────────────────────────────────┐
                    │           INDEXER                   │
                    │                                     │
                    │  ┌───────────────────────────────┐ │
                    │  │  ALL_DOCUMENTS (non filtrés)  │ │
                    │  └───────────────────────────────┘ │
                    │              ↓                      │
                    │  ┌───────────────────────────────┐ │
                    │  │    ml-api-logs (TOUS)         │ │
                    │  └───────────────────────────────┘ │
                    │                                     │
                    │  ┌───────────────────────────────┐ │
                    │  │ FILTERED_DOCUMENTS (filtrés)  │ │
                    │  └───────────────────────────────┘ │
                    │         ↓              ↓            │
                    │  ┌─────────────┐ ┌──────────────┐ │
                    │  │ml-api-message│ │ml-api-perfs │ │
                    │  └─────────────┘ └──────────────┘ │
                    └─────────────────────────────────────┘
                              ↓
                    ┌─────────────────┐
                    │  ELASTICSEARCH  │
                    │  3 index créés  │
                    └─────────────────┘
```

**Triple indexation** :

1. **ml-api-logs** : TOUS les logs sans filtrage
   - Usage : Débogage complet, audit
   - Contenu : Tous les champs bruts

2. **ml-api-message** : Logs filtrés avec données de prédiction
   - Usage : Analyse du drift de données
   - Contenu : input_data, result, transaction_id

3. **ml-api-perfs** : Logs filtrés avec métriques de performance
   - Usage : Optimisation du modèle
   - Contenu : inference_time_ms, cpu_time_ms, memory_mb, etc.

Documentation complète : [src/logs_pipeline/README.md](../src/logs_pipeline/README.md)

### 6. Elasticsearch + Kibana

**Elasticsearch (Port 9200)** :
- Stockage persistant des logs
- Recherche full-text
- Agrégations pour dashboards

**Kibana (Port 5601)** :
- Visualisation des logs
- Création de dashboards
- Exploration des données

**Index patterns recommandés** :
- `ml-api-logs*` : Tous les logs
- `ml-api-message*` : Logs de prédictions
- `ml-api-perfs*` : Métriques de performance

**Dashboards recommandés** :
1. **Dashboard Prédictions** :
   - Nombre de prédictions par heure
   - Distribution des résultats (YES/NO)
   - Top 10 features les plus fréquentes
   - Temps de réponse moyen

2. **Dashboard Performance** :
   - Latence moyenne (p50, p95, p99)
   - CPU usage
   - Mémoire utilisée
   - Top fonctions coûteuses

Documentation : [PERFORMANCE_METRICS.md](PERFORMANCE_METRICS.md)

## Flux de données

### Flux 1 : Prédiction utilisateur (nominal)

```
┌──────────────┐
│ Utilisateur  │
└──────┬───────┘
       │ 1. Remplit formulaire (14 features)
       ↓
┌──────────────┐
│  Gradio UI   │
└──────┬───────┘
       │ 2. POST /predict
       │    Content-Type: application/json
       │    Body: {AGE: 65, GENDER: 1, ...}
       ↓
┌──────────────┐
│  FastAPI API │
│  Middleware  │
└──────┬───────┘
       │ 3. Génération transaction_id (UUID)
       │ 4. Validation Pydantic (PatientData)
       │ 5. Log request (Redis)
       ↓
┌──────────────┐
│  Predictor   │
└──────┬───────┘
       │ 6. Feature Engineering (14 → 28 features)
       ↓
┌──────────────┐
│ Model Loader │
│  (Singleton) │
└──────┬───────┘
       │ 7. model.predict(X)
       │ 8. model.predict_proba(X)
       ↓
┌──────────────┐
│  Predictor   │
└──────┬───────┘
       │ 9. Formatage résultat
       │    {prediction: 1, probability: 0.85, message: "..."}
       ↓
┌──────────────┐
│  FastAPI API │
└──────┬───────┘
       │ 10. Log response (Redis)
       │ 11. Performance metrics (Redis)
       │ 12. Return JSON
       ↓
┌──────────────┐
│  Gradio UI   │
└──────┬───────┘
       │ 13. Affichage résultat
       ↓
┌──────────────┐
│ Utilisateur  │
└──────────────┘
```

**Temps de réponse typique** : 20-60ms

### Flux 2 : Pipeline de logs vers Elasticsearch

```
┌──────────────┐        ┌──────────────┐
│  Redis Cache │        │  Gradio API  │
│  (API logs)  │        │ (/logs_api)  │
└──────┬───────┘        └──────┬───────┘
       │                       │
       │ 1. Collecte           │
       └───────┬───────────────┘
               ↓
       ┌──────────────┐
       │  Collector   │
       │  - Fetch     │
       │  - Dedupe    │
       │  - Parse     │
       └──────┬───────┘
              │ 2. Documents bruts
              ↓
       ┌──────────────┐
       │   Filter     │
       │  - Pattern   │
       │  - HTTP path │
       └──────┬───────┘
              │ 3. Documents filtrés
              ↓
       ┌──────────────────────────┐
       │      Indexer             │
       │                          │
       │  all_documents →         │
       │    ml-api-logs (TOUS)    │
       │                          │
       │  filtered_documents →    │
       │    ml-api-message        │
       │    ml-api-perfs          │
       └──────┬───────────────────┘
              │ 4. Bulk insert
              ↓
       ┌──────────────┐
       │Elasticsearch │
       │  - Index 1   │
       │  - Index 2   │
       │  - Index 3   │
       └──────┬───────┘
              │ 5. Visualisation
              ↓
       ┌──────────────┐
       │    Kibana    │
       └──────────────┘
```

**Fréquence de collecte** : Configurable (défaut : 10 secondes)

### Flux 3 : Monitoring de performance

```
┌──────────────┐
│  API Request │
└──────┬───────┘
       │ 1. Entrée endpoint /predict
       ↓
┌──────────────────┐
│ PerformanceMonitor│
│   .start()        │
└──────┬────────────┘
       │ 2. cProfile.enable()
       │ 3. Capture mémoire initiale
       │ 4. Capture temps CPU initial
       ↓
┌──────────────┐
│  Predictor   │
│  .predict()  │
└──────┬───────┘
       │ 5. Exécution prédiction
       ↓
┌──────────────────┐
│ PerformanceMonitor│
│   .stop()         │
└──────┬────────────┘
       │ 6. cProfile.disable()
       │ 7. Calcul delta mémoire
       │ 8. Calcul temps CPU
       │ 9. Analyse top fonctions
       ↓
┌──────────────┐
│  Métriques   │
│  - inference_time_ms     │
│  - cpu_time_ms          │
│  - memory_mb            │
│  - memory_delta_mb      │
│  - function_calls       │
│  - latency_ms           │
│  - top_functions (top 5)│
└──────┬─────────────────┘
       │ 10. Log vers Redis
       ↓
┌──────────────┐
│ Redis Cache  │
└──────┬───────┘
       │ 11. Pipeline collecte
       ↓
┌──────────────┐
│Elasticsearch │
│ ml-api-perfs │
└──────────────┘
```

Documentation : [PERFORMANCE_METRICS.md](PERFORMANCE_METRICS.md)

## Infrastructure Docker

### Architecture Docker Compose

```yaml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - redis
    volumes:
      - ./model:/app/model
    environment:
      - REDIS_HOST=redis
      - MODEL_PATH=/app/model/model.pkl

  ui:
    build:
      context: .
      dockerfile: Dockerfile.ui
    ports:
      - "7860:7860"
    depends_on:
      - api
    environment:
      - API_URL=http://api:8000

  redis:
    image: redis:latest
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.10.0
    ports:
      - "9200:9200"
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    volumes:
      - es_data:/usr/share/elasticsearch/data

  kibana:
    image: docker.elastic.co/kibana/kibana:8.10.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
```

### Network isolation

```
┌────────────────────────────────────────────┐
│         Docker Network: project8_default   │
│                                            │
│  ┌──────┐  ┌──────┐  ┌───────┐  ┌──────┐ │
│  │  API │←→│  UI  │←→│ Redis │←→│  ES  │ │
│  └──────┘  └──────┘  └───────┘  └──────┘ │
│      ↑                                ↑    │
└──────┼────────────────────────────────┼────┘
       │                                │
    Port 8000                       Port 9200
    Port 7860                       Port 5601
```

### Volumes persistants

| Service | Volume | Contenu |
|---------|--------|---------|
| Redis | `redis_data` | Cache des logs |
| Elasticsearch | `es_data` | Index Elasticsearch |
| API | `./model` | Modèle ML (bind mount) |

## Monitoring et performance

### Métriques collectées

**8 métriques principales** :

1. **transaction_id** : UUID unique
2. **inference_time_ms** : Temps d'inférence ML
3. **cpu_time_ms** : Temps CPU utilisé
4. **memory_mb** : Mémoire totale
5. **memory_delta_mb** : Variation mémoire
6. **function_calls** : Nombre d'appels
7. **latency_ms** : Latence totale
8. **top_functions** : Top 5 fonctions coûteuses

Documentation complète : [PERFORMANCE_METRICS.md](PERFORMANCE_METRICS.md)

### Dashboards Kibana recommandés

**Dashboard 1 : Vue d'ensemble ML**
- Graphe : Prédictions par heure (time series)
- Pie chart : Distribution YES/NO
- Table : Temps de réponse (p50, p95, p99)
- Heatmap : Patterns horaires

**Dashboard 2 : Performance détaillée**
- Graphe : Latence moyenne (time series)
- Graphe : CPU usage (time series)
- Graphe : Mémoire utilisée (time series)
- Table : Top 10 fonctions coûteuses

### Alertes recommandées

| Métrique | Seuil Warning | Seuil Critical |
|----------|---------------|----------------|
| Latence | > 100ms | > 200ms |
| CPU time | > 100ms | > 200ms |
| Memory delta | > 50MB | > 100MB |
| Inference time | > 50ms | > 100ms |

## Sécurité et scalabilité

### Sécurité

**Niveau actuel (développement)** :
- CORS : Toutes origines
- Authentification : Aucune
- HTTPS : Non configuré

**Recommandations production** :

1. **CORS restreint** :
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://votre-domaine.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

2. **Authentification API** :
   - API Key dans headers
   - OAuth 2.0 / JWT
   - Rate limiting

3. **HTTPS** :
   - Certificat SSL/TLS
   - Reverse proxy (nginx)

4. **Validation renforcée** :
   - Sanitisation des inputs
   - Limites de taille de requête
   - Timeout des connexions

### Scalabilité

**Architecture actuelle** : Monolithique

**Évolution horizontale** :

```
                    ┌──────────────┐
                    │ Load Balancer│
                    │   (nginx)    │
                    └──────┬───────┘
                           │
        ┌──────────────────┼──────────────────┐
        ↓                  ↓                  ↓
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  API Node 1  │   │  API Node 2  │   │  API Node 3  │
└──────┬───────┘   └──────┬───────┘   └──────┬───────┘
       │                  │                  │
       └──────────────────┼──────────────────┘
                          ↓
                  ┌──────────────┐
                  │ Redis Cluster│
                  └──────┬───────┘
                         ↓
                  ┌──────────────┐
                  │ ES Cluster   │
                  └──────────────┘
```

**Optimisations** :

1. **Cache modèle** :
   - Modèle chargé une fois (Singleton) ✅
   - Pas de rechargement à chaque requête

2. **Connection pooling** :
   - Redis connection pool
   - Elasticsearch connection pool

3. **Batch predictions** :
   - Endpoint pour prédictions multiples
   - Vectorisation avec numpy

4. **Async endpoints** :
   - FastAPI async/await
   - Non-blocking I/O

## Configuration

### Variables d'environnement

Documentation complète : [ENV_VARIABLES.md](ENV_VARIABLES.md)

**Principales variables** :

```bash
# API
API_HOST=0.0.0.0
API_PORT=8000

# Modèle
MODEL_PATH=./model/model.pkl

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
LOG_TO_REDIS=true
REDIS_LOGS_MAX_SIZE=1000

# Elasticsearch
ES_HOST=localhost
ES_PORT=9200

# Gradio
GRADIO_URL=http://localhost:7860

# Performance
ENABLE_PERFORMANCE_MONITORING=true

# HuggingFace (optionnel)
HF_TOKEN=hf_xxxxx
```

### Fichiers de configuration

| Fichier | Description |
|---------|-------------|
| `.env` | Variables d'environnement (ne pas commiter) |
| `.env.example` | Template de configuration |
| `pyproject.toml` | Dépendances Python |
| `docker-compose.yml` | Infrastructure Docker |
| `.flake8` | Configuration linting |
| `CLAUDE.md` | Règles de développement |

## Commandes utiles

Documentation complète : [MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md)

**Développement** :
```bash
make dev              # Setup complet
make run-api          # Lancer API
make run-ui           # Lancer Gradio
```

**Tests** :
```bash
make test             # Tous les tests
make test-coverage    # Avec couverture
make lint             # Vérifier le code
```

**Docker** :
```bash
make docker-build     # Construire images
make docker-up        # Lancer conteneurs
make docker-down      # Arrêter conteneurs
```

**Pipeline** :
```bash
make pipeline-elasticsearch-up    # Lancer ES + Kibana
make pipeline-once               # Exécuter pipeline une fois
make pipeline-continuous         # Pipeline continu
```

**Logs** :
```bash
make logs             # Afficher logs Redis
make clear-logs       # Vider cache Redis
```

## Références

- [README.md](../README.md) - Documentation principale
- [CLAUDE.md](../CLAUDE.md) - Règles de développement
- [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - Documentation API complète
- [PERFORMANCE_METRICS.md](PERFORMANCE_METRICS.md) - Métriques de performance
- [FEATURE_ENGINEERING.md](FEATURE_ENGINEERING.md) - Features du modèle
- [src/logs_pipeline/README.md](../src/logs_pipeline/README.md) - Pipeline de logs

---

**Version** : 1.0.0
**Dernière mise à jour** : 20 novembre 2024
**Projet** : OpenClassrooms MLOps - Projet 8
