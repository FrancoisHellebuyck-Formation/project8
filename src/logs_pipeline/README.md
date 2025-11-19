# Pipeline d'intégration des logs dans Elasticsearch

Ce package implémente un pipeline autonome et non intrusif pour intégrer les logs de l'API dans Elasticsearch.

## Architecture

Le pipeline se compose de 5 modules :

### 1. `config.py` - Configuration
Gère la configuration du pipeline via variables d'environnement :
- **Elasticsearch** : host, port, index
- **Gradio** : URL de l'API HuggingFace, token HF
- **Pipeline** : batch_size, poll_interval, filter_pattern

### 2. `collector.py` - Collecteur de logs
Récupère les logs depuis l'API Gradio HuggingFace :
- Connexion au endpoint `/logs_api` de Gradio
- Support du HF_TOKEN pour les Spaces privés
- Transformation au format Elasticsearch
- Déduplication des logs

### 3. `filter.py` - Filtre de logs
Filtre les logs selon un pattern défini :
- Par défaut : `"API Call - POST /predict"`
- Vérifie le message, le path HTTP et la méthode

### 4. `indexer.py` - Indexeur Elasticsearch
Indexe les logs dans Elasticsearch avec une double indexation :
- **Index `ml-api-logs`** : Logs bruts complets avec tous les champs
- **Index `ml-api-message`** : Messages parsés avec uniquement les données structurées (input_data, result)
- Création automatique des index avec mapping adapté
- Indexation en masse (bulk insert)
- Gestion de la connexion

### 5. `pipeline.py` - Orchestrateur
Orchestre le flux complet :
- Vérification des pré-requis
- Mode exécution unique : `run_once()`
- Mode exécution continue : `run_continuous()`

## Installation

### 1. Installer les dépendances

```bash
make install-dev
```

Cela installera :
- `elasticsearch>=8.11.0`
- `gradio-client>=1.13.3`

### 2. Configurer les variables d'environnement

Copier `.env.example` vers `.env` et configurer :

```bash
# Configuration Pipeline Elasticsearch
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_INDEX=ml-api-logs

# Configuration du Pipeline de Logs
PIPELINE_BATCH_SIZE=100
PIPELINE_POLL_INTERVAL=10
PIPELINE_FILTER_PATTERN=API Call - POST /predict

# URL Gradio pour le collecteur de logs
GRADIO_URL=https://francoisformation-oc-project8.hf.space

# HuggingFace Token (pour accès aux Spaces privés)
HF_TOKEN=your_token_here
```

### 3. Lancer Elasticsearch et Kibana

```bash
make pipeline-elasticsearch-up
```

Cela lance :
- Elasticsearch sur http://localhost:9200
- Kibana sur http://localhost:5601

## Utilisation

### Vérifier les pré-requis

Avant de lancer le pipeline, vérifiez que tous les pré-requis sont remplis :

```bash
make pipeline-check
```

Cette commande vérifie :
1. Connexion à l'API Gradio HuggingFace
2. Connexion à Elasticsearch
3. Dépendances Python installées

### Exécuter le pipeline une fois

```bash
make pipeline-once
```

Cette commande :
1. Vérifie les pré-requis
2. Collecte les logs depuis Gradio (max 100)
3. Filtre les logs POST /predict
4. Indexe dans Elasticsearch

### Exécuter le pipeline en continu

```bash
make pipeline-continuous
```

Le pipeline s'exécute en boucle toutes les 10 secondes (configurable).
Appuyez sur `Ctrl+C` pour arrêter.

### Utilisation en ligne de commande

```bash
# Mode une fois
uv run python -m src.logs_pipeline --once --limit 100

# Mode continu
uv run python -m src.logs_pipeline --continuous --interval 10

# Avec URL Gradio personnalisée
uv run python -m src.logs_pipeline --once \
    --gradio-url https://my-space.hf.space \
    --hf-token YOUR_TOKEN

# Afficher l'aide
uv run python -m src.logs_pipeline --help
```

## Utilisation programmatique

```python
from src.logs_pipeline import LogsPipeline

# Créer le pipeline
pipeline = LogsPipeline()

# Vérifier les pré-requis
if pipeline.check_prerequisites():
    # Exécuter une fois
    stats = pipeline.run_once(limit=100)
    print(f"Logs collectés: {stats['collected']}")
    print(f"Logs filtrés: {stats['filtered']}")
    print(f"Logs indexés: {stats['indexed']}")
else:
    print("Pré-requis non satisfaits")

# Ou exécuter en continu
pipeline.run_continuous(limit=100, poll_interval=10)
```

## Structure des index Elasticsearch

Le pipeline crée automatiquement deux index distincts :

### 1. Index `ml-api-logs` - Logs bruts complets

Contient tous les logs avec l'ensemble des champs :
- `@timestamp` : Date/heure du log (format ISO 8601)
- `level` : Niveau de log (INFO, ERROR, etc.)
- `logger` : Nom du logger
- `message` : Message complet du log
- `raw_log` : Log brut tel qu'envoyé par l'API
- `transaction_id` : ID unique de la transaction (UUID)
- `http_method` : Méthode HTTP (POST)
- `http_path` : Path HTTP (/predict)
- `status_code` : Code HTTP de réponse
- `execution_time_ms` : Temps d'exécution en ms
- `input_data` : Données d'entrée de la prédiction (objet JSON)
- `result` : Résultat de la prédiction (objet JSON)

### 2. Index `ml-api-message` - Messages parsés uniquement

Contient uniquement les logs qui ont été parsés avec succès (avec input_data et result) :
- `@timestamp` : Date/heure du log
- `transaction_id` : ID unique de la transaction
- `http_method` : Méthode HTTP
- `http_path` : Path HTTP
- `status_code` : Code HTTP de réponse
- `execution_time_ms` : Temps d'exécution
- `input_data` : Données d'entrée structurées avec tous les champs patients :
  - AGE, GENDER, SMOKING, YELLOW_FINGERS, ANXIETY, PEER_PRESSURE,
  - CHRONIC_DISEASE, FATIGUE, ALLERGY, WHEEZING, ALCOHOL, COUGHING,
  - SHORTNESS_OF_BREATH, SWALLOWING_DIFFICULTY, CHEST_PAIN
- `result` : Résultat structuré avec :
  - prediction (YES/NO)
  - probability (0.0 à 1.0)
  - message (texte descriptif)

**Avantages de la double indexation :**
- `ml-api-logs` : Pour le débogage et l'audit complet
- `ml-api-message` : Pour l'analyse des prédictions et du drift de données

## Visualisation avec Kibana

1. Ouvrir Kibana : http://localhost:5601
2. Aller dans "Stack Management" > "Index Patterns"
3. Créer deux index patterns :
   - `ml-api-logs*` pour les logs complets
   - `ml-api-message*` pour les messages parsés uniquement
4. Aller dans "Discover" pour visualiser les logs

### Tester la création des index

```bash
make pipeline-test-indexes
```

Cette commande vérifie que les deux index sont créés avec les bons mappings.

### Vider les index Elasticsearch

Pour supprimer tous les logs indexés et repartir de zéro :

```bash
make pipeline-clear-indexes
```

Cette commande supprime les index `ml-api-logs` et `ml-api-message`. Les index seront automatiquement recréés au prochain lancement du pipeline.

⚠️ **Attention** : Cette action est irréversible. Tous les logs indexés seront définitivement supprimés.

## Arrêter le pipeline

Pour arrêter Elasticsearch et Kibana :

```bash
make pipeline-elasticsearch-down
```

## Architecture non intrusive

Le pipeline est complètement indépendant du code de l'API :
- Aucune modification du code existant
- Récupération des logs via l'API Gradio publique
- Peut être lancé/arrêté à tout moment
- Ne perturbe pas le fonctionnement de l'API

## Dépannage

### Elasticsearch non disponible

```
✗ Impossible de se connecter à Elasticsearch. Host: localhost:9200
  Lancez Elasticsearch avec: make pipeline-elasticsearch-up
```

**Solution** : Lancer Elasticsearch avec `make pipeline-elasticsearch-up`

### Gradio non disponible

```
✗ Impossible de se connecter à l'API Gradio. URL: https://...
```

**Solutions** :
- Vérifier que l'URL Gradio est correcte
- Vérifier que le HF_TOKEN est valide (si Space privé)
- Vérifier la connexion internet

### Dépendance manquante

```
✗ gradio_client non installé.
```

**Solution** : Installer les dépendances avec `make install-dev`
