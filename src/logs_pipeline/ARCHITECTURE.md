# Architecture du Pipeline de Logs

## Flux de données

```
┌─────────────────────────────────────────────────────────────────┐
│                         API GRADIO                               │
│                  (HuggingFace Spaces)                            │
│                                                                   │
│  - Logs d'appels API                                             │
│  - Logs de métriques de performance                              │
│  - Logs système                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP GET /logs_api
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      COLLECTOR                                   │
│                   (collector.py)                                 │
│                                                                   │
│  - Récupère tous les logs depuis Gradio                          │
│  - Transforme au format Elasticsearch                            │
│  - Déduplique les logs                                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ documents[] (TOUS les logs)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       FILTER                                     │
│                    (filter.py)                                   │
│                                                                   │
│  Accepte:                                                        │
│  - Logs contenant "API Call - POST /predict"                    │
│  - Logs contenant "performance_metrics"                         │
│  - Logs avec http_path="/predict" et http_method="POST"         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ filtered_documents[]
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      INDEXER                                     │
│                   (indexer.py)                                   │
│                                                                   │
│  Triple indexation dans Elasticsearch:                           │
└─────────────────────────────────────────────────────────────────┘
         │                    │                    │
         │                    │                    │
         ▼                    ▼                    ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  ml-api-logs     │  │ ml-api-message   │  │  ml-api-perfs    │
│  (NON FILTRÉS)   │  │   (FILTRÉS)      │  │   (FILTRÉS)      │
├──────────────────┤  ├──────────────────┤  ├──────────────────┤
│ TOUS LES LOGS    │  │ Messages parsés  │  │ Métriques de     │
│ de l'API sans    │  │ avec input_data  │  │ performance avec │
│ aucun filtrage   │  │ et result        │  │ transaction_id   │
│                  │  │                  │  │                  │
│ Usage:           │  │ Usage:           │  │ Usage:           │
│ - Débogage       │  │ - Analyse drift  │  │ - Optimisation   │
│ - Audit complet  │  │ - Prédictions    │  │ - Métriques CPU  │
│ - Investigation  │  │ - Data science   │  │ - Temps inférence│
└──────────────────┘  └──────────────────┘  └──────────────────┘
```

## Index Elasticsearch

### 1. ml-api-logs (NON FILTRÉS)

**Source**: TOUS les documents collectés depuis Gradio (sans filtrage)

**Champs**:
- `@timestamp` : Date/heure du log
- `level` : Niveau de log (INFO, ERROR, etc.)
- `logger` : Nom du logger
- `message` : Message complet du log
- `raw_log` : Log brut tel qu'envoyé par l'API
- `transaction_id` : ID unique de la transaction
- `http_method` : Méthode HTTP
- `http_path` : Path HTTP
- `status_code` : Code HTTP de réponse
- `execution_time_ms` : Temps d'exécution
- `input_data` : Données d'entrée (objet JSON)
- `result` : Résultat de la prédiction (objet JSON)

**Cas d'usage**:
- Débogage complet de l'API
- Audit et traçabilité
- Investigation d'incidents
- Vue exhaustive de tous les événements

### 2. ml-api-message (FILTRÉS)

**Source**: Documents FILTRÉS qui contiennent `input_data` et `result`

**Champs**:
- `@timestamp` : Date/heure du log
- `transaction_id` : ID unique de la transaction
- `http_method` : Méthode HTTP
- `http_path` : Path HTTP
- `status_code` : Code HTTP de réponse
- `execution_time_ms` : Temps d'exécution
- `input_data` : Données patient structurées (14 features)
- `result` : Prédiction structurée (prediction, probability, message)

**Cas d'usage**:
- Analyse des prédictions du modèle
- Détection du drift de données
- Export vers Parquet pour analyse (Evidently AI)
- Dashboard de monitoring des prédictions

### 3. ml-api-perfs (FILTRÉS)

**Source**: Documents FILTRÉS qui contiennent `performance_metrics` dans le message

**Champs**:
- `@timestamp` : Date/heure du log
- `transaction_id` : ID unique de la transaction
- `inference_time_ms` : Temps d'inférence en ms
- `cpu_time_ms` : Temps CPU en ms
- `memory_mb` : Mémoire utilisée en MB
- `memory_delta_mb` : Delta de mémoire en MB
- `function_calls` : Nombre d'appels de fonctions
- `latency_ms` : Latence totale en ms
- `top_functions` : Liste des fonctions les plus coûteuses (nested)

**Cas d'usage**:
- Optimisation des performances du modèle
- Identification des goulots d'étranglement
- Monitoring de la latence
- Dashboard de performances système

## Modules

### config.py
Gère la configuration du pipeline via variables d'environnement.

### collector.py
Récupère TOUS les logs depuis l'API Gradio HuggingFace.

### filter.py
Filtre les logs pour identifier ceux qui doivent être parsés et indexés dans `ml-api-message` et `ml-api-perfs`.

**Critères d'acceptation**:
1. Message contient "API Call - POST /predict"
2. Message contient "performance_metrics"
3. http_path == "/predict" ET http_method == "POST"

### indexer.py
Indexe les documents dans Elasticsearch avec triple indexation:
- **TOUS les logs** → `ml-api-logs` (pas de filtrage)
- **Logs filtrés parsés** → `ml-api-message` (avec input_data et result)
- **Logs filtrés de performance** → `ml-api-perfs` (avec performance_metrics)

### pipeline.py
Orchestre le flux complet:
1. Collecte TOUS les logs depuis Gradio
2. Filtre les logs pour identifier les prédictions et métriques
3. Indexe:
   - TOUS les logs dans `ml-api-logs`
   - Logs filtrés dans `ml-api-message` et `ml-api-perfs`

## Exemple de flux

### Log de prédiction API

**Entrée Gradio**:
```
2025-01-20 10:30:00 - api - INFO - [abc-123] POST /predict - 200 - 45ms - {"AGE": 65, "GENDER": "M", ...} - {"prediction": "YES", "probability": 0.85, ...}
```

**Résultat**:
- ✅ Indexé dans `ml-api-logs` (log complet brut)
- ✅ Indexé dans `ml-api-message` (données parsées structurées)
- ❌ NON indexé dans `ml-api-perfs` (pas de métriques de performance)

### Log de métriques de performance

**Entrée Gradio**:
```
2025-01-20 10:30:01 - api - INFO - {"performance_metrics": {"transaction_id": "abc-123", "inference_time_ms": 25.5, "cpu_time_ms": 18.2, ...}}
```

**Résultat**:
- ✅ Indexé dans `ml-api-logs` (log complet brut)
- ❌ NON indexé dans `ml-api-message` (pas de input_data/result)
- ✅ Indexé dans `ml-api-perfs` (métriques extraites)

### Log système générique

**Entrée Gradio**:
```
2025-01-20 10:29:50 - api - INFO - API démarrée avec succès
```

**Résultat**:
- ✅ Indexé dans `ml-api-logs` (log complet brut)
- ❌ NON indexé dans `ml-api-message` (pas une prédiction)
- ❌ NON indexé dans `ml-api-perfs` (pas de métriques)

## Avantages de cette architecture

### 1. Séparation des préoccupations
- **ml-api-logs**: Vue exhaustive pour le débogage
- **ml-api-message**: Données métier pour l'analyse
- **ml-api-perfs**: Métriques techniques pour l'optimisation

### 2. Performance des requêtes
Chaque index est optimisé pour son cas d'usage avec des mappings spécifiques.

### 3. Flexibilité
Le filtrage peut être ajusté sans perdre les données brutes qui restent dans `ml-api-logs`.

### 4. Traçabilité complète
Grâce au `transaction_id`, on peut joindre les données des 3 index pour une vue 360° d'une transaction.

### 5. Conformité et audit
`ml-api-logs` conserve TOUS les logs pour la traçabilité et l'audit complet.
