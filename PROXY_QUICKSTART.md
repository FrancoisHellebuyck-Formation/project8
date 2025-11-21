# 🚀 Proxy Quickstart

Guide rapide pour utiliser le package proxy Gradio ↔ FastAPI.

## ⚡ Démarrage en 30 secondes

### 1. Prérequis

```bash
# L'API FastAPI doit être en cours d'exécution
make run-api
```

### 2. Lancer le proxy

```bash
# Dans un autre terminal
make run-proxy
```

### 3. Accéder à l'interface

Ouvrir votre navigateur : **http://localhost:7860**

## 🎯 Utilisation programmatique

### Exemple minimal

```python
from src.proxy import APIProxyClient

# Créer le client
client = APIProxyClient()

# Vérifier la connexion
if client.check_connection():
    print("✅ Connecté à l'API")

# Health check
response, status = client.get_health()
print(response)

# Prédiction
patient = {
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
    "CHEST PAIN": 1,
    "CHRONIC DISEASE": 1
}

response, status = client.post_predict(patient)
print(f"Prédiction: {response['prediction']}")
print(f"Probabilité: {response['probability']}")
```

## 📚 Endpoints disponibles

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | / | Informations API |
| GET | /health | Health check |
| POST | /predict | Prédiction ML |
| POST | /predict_proba | Probabilités détaillées |
| GET | /logs | Récupérer les logs |
| DELETE | /logs | Vider le cache Redis |

## 🧪 Tester

```bash
# Lancer les tests du proxy
make test-proxy

# Exemple d'utilisation
python example_proxy_usage.py
```

## 📖 Documentation complète

- **Documentation complète** : [docs/PROXY_DOCUMENTATION.md](docs/PROXY_DOCUMENTATION.md)
- **Code source** : [src/proxy/](src/proxy/)
- **Tests** : [tests/test_proxy.py](tests/test_proxy.py)

## 🔧 Configuration

Le proxy utilise automatiquement la configuration depuis `src/config.py` :

```python
# Changer l'URL de l'API
client = APIProxyClient(api_url="http://localhost:8000")
```

## 💡 Cas d'usage

### 1. Monitoring

```python
# Vérifier régulièrement la santé de l'API
import time

while True:
    if client.check_connection():
        health, _ = client.get_health()
        print(f"✅ {health['status']}")
    else:
        print("❌ API inaccessible")
    time.sleep(60)
```

### 2. Batch predictions

```python
# Prédictions pour plusieurs patients
patients = [patient1, patient2, patient3]
results = client.batch_predict(patients)

for response, status in results:
    print(f"Prédiction: {response['prediction']}")
```

### 3. Gestion des logs

```python
# Récupérer les logs avec pagination
logs, _ = client.get_logs(limit=50, offset=0)
print(f"Total: {logs['total']} logs")

# Vider le cache
result, _ = client.delete_logs()
print(result['message'])
```

## ⚙️ Commandes Make

```bash
make run-proxy          # Lancer l'interface proxy
make test-proxy         # Lancer les tests
make run-api            # Lancer l'API (prérequis)
```

## 🐛 Dépannage

### API inaccessible

```bash
# Vérifier que l'API est lancée
curl http://localhost:8000/health

# Si non, lancer l'API
make run-api
```

### Port déjà utilisé

```bash
# Utiliser un autre port
python run_proxy.py --port 7861
```

### Timeout

```python
# Augmenter le timeout
client = APIProxyClient()
client.timeout = 60  # 60 secondes
```

---

**Prochaines étapes** : Consultez [docs/PROXY_DOCUMENTATION.md](docs/PROXY_DOCUMENTATION.md) pour une documentation complète avec exemples avancés.
