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
Indexe les logs dans Elasticsearch avec une triple indexation :
- **Index `ml-api-logs`** : Logs bruts complets avec tous les champs
- **Index `ml-api-message`** : Messages parsés avec uniquement les données structurées (input_data, result)
- **Index `ml-api-perfs`** : Métriques de performance (transaction_id, temps d'inférence, CPU, mémoire, etc.)
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

**Avantages de la triple indexation :**
- `ml-api-logs` : Pour le débogage et l'audit complet
- `ml-api-message` : Pour l'analyse des prédictions et du drift de données
- `ml-api-perfs` : Pour l'analyse des performances et l'optimisation du modèle

## Visualisation avec Kibana

1. Ouvrir Kibana : http://localhost:5601
2. Aller dans "Stack Management" > "Index Patterns"
3. Créer trois index patterns :
   - `ml-api-logs*` pour les logs complets
   - `ml-api-message*` pour les messages parsés uniquement
   - `ml-api-perfs*` pour les métriques de performance
4. Aller dans "Discover" pour visualiser les logs

### Tester la création des index

```bash
make pipeline-test-indexes
```

Cette commande vérifie que les trois index sont créés avec les bons mappings.

### Vider les index Elasticsearch

Pour supprimer tous les logs indexés et repartir de zéro :

```bash
make pipeline-clear-indexes
```

Cette commande supprime les index `ml-api-logs`, `ml-api-message` et `ml-api-perfs`. Les index seront automatiquement recréés au prochain lancement du pipeline.

⚠️ **Attention** : Cette action est irréversible. Tous les logs indexés seront définitivement supprimés.

### Dédoublonner les index

Si les index contiennent des doublons (même `transaction_id`), vous pouvez les supprimer :

```bash
make pipeline-deduplicate
```

Cette commande :
1. Récupère tous les documents des index `ml-api-message` et `ml-api-perfs`
2. Groupe les documents par `transaction_id`
3. Pour chaque groupe, conserve uniquement le document le plus récent (basé sur `@timestamp`)
4. Supprime les doublons

**Exemple de sortie** :
```
Documents avant: 1523
Doublons supprimés: 245
Documents après: 1278
```

**Note** : Les documents sans `transaction_id` sont conservés intacts.

### Exporter vers Parquet

Pour exporter les données de `ml-api-message` vers un fichier Parquet :

```bash
make pipeline-export-parquet
```

Cette commande :
1. Extrait tous les documents de l'index `ml-api-message`
2. Convertit les données au format DataFrame avec les 14 features de base
3. Applique le feature engineering pour générer les 14 features dérivées
4. Ajoute la colonne `target` basée sur la prédiction
5. Sauvegarde au format Parquet dans `model/inference_dataset.parquet`

**Structure du fichier généré** :
- 14 features de base (GENDER, AGE, SMOKING, etc.)
- 14 features dérivées (SMOKING_x_AGE, RESPIRATORY_SYMPTOMS, etc.)
- 1 colonne target (0 ou 1, basée sur la prédiction)
- **Total : 29 colonnes** (même format que `model/training_dataset.parquet`)

**Personnaliser le chemin de sortie** :
```bash
python scripts/export_elasticsearch_to_parquet.py --output mon_fichier.parquet
```

**Cas d'usage** :
- Analyser les prédictions en production
- Détecter le drift de données (comparer avec training_dataset.parquet)
- Créer des rapports de performance du modèle
- Alimenter un dashboard d'analyse

**Exemple de sortie** :
```
Documents ES extraits: 1278
Lignes dans le Parquet: 1278
Colonnes: 29
Fichier: model/inference_dataset.parquet (245.6 KB)
```

### Analyser le drift de données avec Evidently AI

Pour comparer le dataset d'entraînement avec les données de production et détecter le drift :

```bash
make pipeline-analyze-drift
```

Cette commande :
1. Charge le dataset de référence (`model/training_dataset.parquet`)
2. Charge le dataset de production (`model/inference_dataset.parquet`)
3. Génère un rapport HTML interactif avec Evidently AI
4. Affiche un résumé textuel du drift dans la console
5. Sauvegarde le rapport dans `reports/data_drift_report.html`

**Métriques analysées** :
- **Data Drift** : Détection du drift pour chaque feature (test de Kolmogorov-Smirnov)
- **Data Quality** : Valeurs manquantes, duplications, types de données
- **Target Drift** : Évolution de la distribution de la variable cible

**Exemple de sortie console** :
```
============================================================
Résumé du drift de données
============================================================

Taille des datasets:
  Référence: 309 lignes
  Production: 1,278 lignes

Distribution de la target:
  Référence: 87.4% positifs
  Production: 92.1% positifs
  Drift: 4.7%
  ✓ Drift de target acceptable (<5%)

Drift des features principales:
  AGE:
    Moyenne: 62.73 → 65.12 (drift: 2.39)
    KS test: stat=0.0823, p=0.3421
    ✓ Pas de drift significatif

  SMOKING:
    Moyenne: 0.74 → 0.81 (drift: 0.07)
    KS test: stat=0.1245, p=0.0287
    ⚠ Drift détecté (p < 0.05)

============================================================
Conclusion:
============================================================
⚠ Drift modéré détecté
  1 feature(s) avec drift: SMOKING
  Surveillance recommandée
============================================================

✓ Rapport HTML disponible: reports/data_drift_report.html
  Ouvrez-le dans votre navigateur pour voir les détails
```

**Personnaliser les chemins** :
```bash
python scripts/analyze_data_drift.py \
    --reference model/training_dataset.parquet \
    --current model/inference_dataset.parquet \
    --output reports/mon_rapport.html
```

**Ouvrir le rapport HTML** :
```bash
# Le rapport contient des visualisations interactives :
# - Graphiques de distribution pour chaque feature
# - Heatmap des corrélations
# - Tests statistiques détaillés
# - Recommandations d'action

open reports/data_drift_report.html  # macOS
xdg-open reports/data_drift_report.html  # Linux
```

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
