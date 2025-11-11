# Variables d'environnement

Ce fichier documente les variables d'environnement utilisées dans le projet.

## Configuration

Pour configurer le projet, copiez le fichier `.env.example` vers `.env` et ajustez les valeurs selon vos besoins :

```bash
cp .env.example .env
```

**Important** : Le fichier `.env` contient des informations sensibles et ne doit jamais être commité dans git (il est déjà dans `.gitignore`).

## Variables disponibles

### Configuration du modèle ML

- `MODEL_PATH` : Chemin vers le fichier du modèle ML (.pkl)
  - **Par défaut** : `./model/model.pkl`
  - **Type** : string (chemin relatif ou absolu)

### Configuration de l'API FastAPI

- `API_HOST` : Adresse IP sur laquelle l'API écoute
  - **Par défaut** : `0.0.0.0`
  - **Type** : string

- `API_PORT` : Port sur lequel l'API écoute
  - **Par défaut** : `8000`
  - **Type** : integer

### Configuration Redis

- `REDIS_HOST` : Hôte du serveur Redis
  - **Par défaut** : `localhost`
  - **Type** : string

- `REDIS_PORT` : Port du serveur Redis
  - **Par défaut** : `6379`
  - **Type** : integer

- `REDIS_DB` : Numéro de la base de données Redis
  - **Par défaut** : `0`
  - **Type** : integer

- `REDIS_LOGS_KEY` : Clé Redis pour stocker les logs
  - **Par défaut** : `api_logs`
  - **Type** : string

- `REDIS_LOGS_MAX_SIZE` : Nombre maximum de logs à conserver
  - **Par défaut** : `1000`
  - **Type** : integer

### Configuration Gradio

- `GRADIO_HOST` : Adresse IP sur laquelle Gradio écoute
  - **Par défaut** : `0.0.0.0`
  - **Type** : string

- `GRADIO_PORT` : Port sur lequel Gradio écoute
  - **Par défaut** : `7860`
  - **Type** : integer

- `API_URL` : URL de l'API FastAPI
  - **Par défaut** : `http://localhost:8000`
  - **Type** : string (URL complète)

### Environnement

- `ENV` : Environnement d'exécution
  - **Par défaut** : `development`
  - **Valeurs possibles** : `development`, `staging`, `production`
  - **Type** : string

- `LOG_LEVEL` : Niveau de log
  - **Par défaut** : `INFO`
  - **Valeurs possibles** : `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
  - **Type** : string

- `LOGGING_HANDLER` : Type de handler pour les logs de l'API
  - **Par défaut** : `stdout`
  - **Valeurs possibles** :
    - `stdout` : Logs uniquement vers la console (standard output)
    - `redis` : Logs vers la console ET stockage dans Redis
  - **Type** : string
  - **Note** : En mode `redis`, les logs sont à la fois affichés dans la console et stockés dans Redis pour consultation via l'endpoint `/logs`. En mode `stdout`, les logs sont uniquement affichés dans la console.

- `UI_LOG_LEVEL` : Niveau de log pour l'interface Gradio
  - **Par défaut** : `INFO`
  - **Valeurs possibles** : `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
  - **Type** : string
  - **Note** : Configure le niveau de log spécifique pour l'interface utilisateur Gradio. Les logs UI sont toujours affichés sur stdout.

## Utilisation dans le code

Les variables d'environnement sont chargées via le module `src/config.py` :

```python
from src.config import settings

# Accéder aux variables
model_path = settings.MODEL_PATH
api_host = settings.API_HOST
```

## Configuration Docker

Pour Docker, vous pouvez :

1. Utiliser un fichier `.env` à la racine du projet
2. Passer les variables via `docker-compose.yml`
3. Utiliser l'option `-e` avec `docker run`

Exemple avec docker-compose :

```yaml
services:
  api:
    environment:
      - MODEL_PATH=/app/model/model.pkl
      - REDIS_HOST=redis
      - REDIS_PORT=6379
```
