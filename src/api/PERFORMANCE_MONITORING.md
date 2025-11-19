# Performance Monitoring

Ce document décrit le système de monitoring des performances d'inférence implémenté dans l'API.

## Vue d'ensemble

Le monitoring de performance utilise `cProfile` pour profiler l'exécution du modèle ML et `psutil` pour mesurer l'utilisation des ressources système. Les métriques sont automatiquement loggées dans le système de logs existant.

## Métriques collectées

Le système collecte les métriques suivantes pour chaque prédiction :

### Métriques temporelles
- **Inference Time (ms)** : Temps total d'exécution de la prédiction
- **CPU Time (ms)** : Temps CPU total consommé
- **Latency** : Latence de bout en bout (équivalent à inference time)

### Métriques mémoire
- **Memory (MB)** : Utilisation mémoire totale du processus
- **Memory Delta (MB)** : Variation de mémoire pendant l'inférence

### Métriques de profiling
- **Function Calls** : Nombre total d'appels de fonction
- **Top Functions** : Les 5 fonctions les plus coûteuses avec leur temps cumulatif

### Métriques de throughput
Le throughput peut être calculé en divisant le nombre de requêtes par le temps total d'exécution sur une période donnée.

## Configuration

### Activation/Désactivation

Le monitoring est contrôlé par la variable d'environnement `ENABLE_PERFORMANCE_MONITORING` :

```bash
# Dans .env
ENABLE_PERFORMANCE_MONITORING=true   # Activer le monitoring
ENABLE_PERFORMANCE_MONITORING=false  # Désactiver le monitoring (par défaut)
```

### Impact sur les performances

Lorsque le monitoring est **activé** :
- Overhead CPU : ~5-10% (dû à cProfile)
- Overhead mémoire : ~1-2 MB par prédiction
- Temps de réponse : +2-5ms par requête

Lorsque le monitoring est **désactivé** :
- Aucun overhead
- Les prédictions s'exécutent à vitesse normale

**Recommandation** : Activez le monitoring uniquement :
- En environnement de développement
- Pour le débogage de performances
- Pour des tests de charge spécifiques
- **Désactivez-le en production** pour des performances optimales

## Utilisation

### Dans l'API

Le monitoring est automatiquement intégré aux endpoints `/predict` et `/predict_proba`. Aucune modification du code n'est nécessaire.

```python
# Le monitoring est transparent pour l'utilisateur
response = requests.post(
    "http://localhost:8000/predict",
    json=patient_data
)
```

### Logs générés

Quand le monitoring est activé, chaque prédiction génère un log JSON structuré contenant toutes les métriques :

#### Log JSON de performance

```json
{
  "performance_metrics": {
    "inference_time_ms": 26.46,
    "cpu_time_ms": 26.35,
    "memory_mb": 263.48,
    "memory_delta_mb": 1.55,
    "function_calls": 26025,
    "latency_ms": 26.46,
    "top_functions": [
      {
        "function": "predict",
        "file": "predictor.py",
        "line": 45,
        "cumulative_time_ms": 26.22,
        "total_time_ms": 11.30,
        "calls": 1
      },
      {
        "function": "engineer_features",
        "file": "feature_engineering.py",
        "line": 89,
        "cumulative_time_ms": 14.96,
        "total_time_ms": 2.15,
        "calls": 1
      },
      {
        "function": "predict",
        "file": "model.py",
        "line": 123,
        "cumulative_time_ms": 12.75,
        "total_time_ms": 12.70,
        "calls": 1
      }
    ]
  }
}
```

**Description des champs :**
- `inference_time_ms` : Temps total d'exécution de la prédiction
- `cpu_time_ms` : Temps CPU consommé
- `memory_mb` : Utilisation mémoire totale
- `memory_delta_mb` : Variation de mémoire pendant l'inférence
- `function_calls` : Nombre total d'appels de fonction
- `latency_ms` : Latence (équivalent à inference_time_ms)
- `top_functions` : Liste des fonctions les plus coûteuses avec :
  - `function` : Nom de la fonction
  - `file` : Fichier source
  - `line` : Numéro de ligne
  - `cumulative_time_ms` : Temps cumulatif (incluant les sous-appels)
  - `total_time_ms` : Temps propre de la fonction
  - `calls` : Nombre d'appels

### Analyse des logs

Les logs de performance peuvent être consultés via :

1. **Endpoint `/logs`** de l'API
2. **Redis** (si configuré)
3. **stdout** (logs console)
4. **Elasticsearch** (si le pipeline de logs est actif)

## Tests

### Script de test standalone

```bash
# Lancer le script de test complet
python scripts/test_performance_monitoring.py

# Ou via Makefile
make test-performance
```

### Tests unitaires

```bash
# Lancer les tests unitaires
pytest tests/api/test_performance_monitoring.py -v
```

### Tests d'intégration

```bash
# Lancer tous les tests
pytest tests/ -v
```

## Architecture

### Module principal

Le monitoring est implémenté dans `src/api/performance_monitor.py` :

```python
from src.api.performance_monitor import performance_monitor

# Utilisation
with performance_monitor.profile():
    result = model.predict(data)

metrics = performance_monitor.get_metrics()
performance_monitor.log_metrics(metrics)
```

### Intégration API

L'intégration dans l'API se fait via un context manager :

```python
# Dans les endpoints /predict et /predict_proba
with performance_monitor.profile():
    prediction = predictor.predict(patient_dict)
    # ... autres opérations

metrics = performance_monitor.get_metrics()
if metrics:
    performance_monitor.log_metrics(metrics)
```

## Exemple de sortie

### Monitoring activé

Log JSON complet :

```json
{
  "performance_metrics": {
    "inference_time_ms": 23.55,
    "cpu_time_ms": 23.46,
    "memory_mb": 232.41,
    "memory_delta_mb": 1.84,
    "function_calls": 26025,
    "latency_ms": 23.55,
    "top_functions": [
      {
        "function": "predict",
        "file": "predictor.py",
        "line": 45,
        "cumulative_time_ms": 23.36,
        "total_time_ms": 10.46,
        "calls": 1
      },
      {
        "function": "predict",
        "file": "model_loader.py",
        "line": 78,
        "cumulative_time_ms": 12.90,
        "total_time_ms": 12.80,
        "calls": 1
      },
      {
        "function": "engineer_features",
        "file": "feature_engineering.py",
        "line": 34,
        "cumulative_time_ms": 10.82,
        "total_time_ms": 3.25,
        "calls": 1
      }
    ]
  }
}
```

Ce log est envoyé au système de logging configuré (Redis, Elasticsearch, ou stdout).

### Monitoring désactivé

Aucun log de performance n'est généré.

## Dépannage

### Le monitoring ne s'active pas

1. Vérifiez la variable d'environnement :
   ```bash
   echo $ENABLE_PERFORMANCE_MONITORING
   # Doit afficher "true"
   ```

2. Rechargez la configuration :
   ```bash
   # Redémarrez l'API
   make run-api
   ```

### Performances dégradées

Si les performances sont dégradées avec le monitoring activé :

1. C'est normal - overhead de 5-10%
2. Désactivez le monitoring en production
3. Utilisez-le uniquement pour le débogage

### Logs non visibles

1. Vérifiez le niveau de log : `LOG_LEVEL=INFO` dans `.env`
2. Vérifiez que Redis est démarré si `LOGGING_HANDLER=redis`
3. Consultez les logs via l'endpoint `/logs`

## Références

- [cProfile Documentation](https://docs.python.org/3/library/profile.html)
- [psutil Documentation](https://psutil.readthedocs.io/)
- [FastAPI Performance](https://fastapi.tiangolo.com/advanced/performance/)
