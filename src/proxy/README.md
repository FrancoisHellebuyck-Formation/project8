# Package Proxy Gradio ↔ FastAPI

## 📋 Vue d'ensemble

Ce package fournit un proxy complet entre Gradio (port 7860) et FastAPI (port 8000), exposant tous les endpoints de l'API via une interface Gradio interactive.

## 🚀 Démarrage rapide

### Lancer l'interface proxy

```bash
# Méthode 1: Via Makefile (recommandé)
make run-proxy

# Méthode 2: Via script Python
python run_proxy.py

# Méthode 3: Via module Python
python -m src.proxy.gradio_app
```

### Accéder à l'interface

- **Local**: http://localhost:7860
- **Réseau**: http://0.0.0.0:7860

## 📦 Modules

### `client.py` - Client API
Client Python pour interagir avec l'API FastAPI de manière programmatique.

```python
from src.proxy import APIProxyClient

client = APIProxyClient()
response, status = client.get_health()
print(response)
```

### `gradio_app.py` - Interface Gradio
Interface web interactive exposant tous les endpoints.

```python
from src.proxy import launch_proxy

launch_proxy(api_url="http://localhost:8000")
```

## 🔌 Endpoints disponibles

✅ **GET /** - Informations API
✅ **GET /health** - Health check
✅ **POST /predict** - Prédiction ML
✅ **POST /predict_proba** - Probabilités détaillées
✅ **GET /logs** - Récupérer les logs (avec pagination)
✅ **DELETE /logs** - Vider le cache Redis

## 🧪 Tests

```bash
# Tous les tests du proxy
make test-proxy

# Ou avec pytest directement
uv run pytest tests/test_proxy.py -v
```

**Couverture**: ~95%

## 📚 Documentation complète

Voir [docs/PROXY_DOCUMENTATION.md](../../docs/PROXY_DOCUMENTATION.md) pour:
- Guide d'utilisation complet
- API Reference
- Exemples de code
- Dépannage
- Architecture détaillée

## 🛠️ Utilisation programmatique

### Exemple 1: Monitoring

```python
from src.proxy import APIProxyClient

client = APIProxyClient()

# Vérifier la connexion
if client.check_connection():
    health, status = client.get_health()
    print(f"✅ API healthy: {health}")
```

### Exemple 2: Prédiction

```python
patient = {
    "AGE": 65,
    "GENDER": 1,
    "SMOKING": 1,
    # ... autres features
}

response, status = client.post_predict(patient)
if status == 200:
    print(f"Prédiction: {response['prediction']}")
    print(f"Probabilité: {response['probability']}")
```

### Exemple 3: Gestion des logs

```python
# Récupérer les logs
logs, status = client.get_logs(limit=50, offset=0)
print(f"Total: {logs['total']} logs")

# Vider les logs
result, status = client.delete_logs()
print(result['message'])
```

## 🔧 Configuration

Le proxy utilise la configuration depuis `src/config.py`:

- **API_URL**: URL de l'API FastAPI (défaut: http://localhost:8000)
- **API_HOST**: Hôte de l'API (défaut: 0.0.0.0)
- **API_PORT**: Port de l'API (défaut: 8000)

## 📝 Structure

```
src/proxy/
├── __init__.py          # Exports du package
├── client.py            # Client proxy API (270 lignes)
├── gradio_app.py        # Interface Gradio (450 lignes)
└── README.md            # Ce fichier
```

## 🤝 Contribution

Lors de l'ajout de fonctionnalités:

1. Ajouter la méthode dans `client.py`
2. Ajouter l'interface dans `gradio_app.py`
3. Ajouter les tests dans `tests/test_proxy.py`
4. Mettre à jour la documentation

## 📄 Licence

Projet 8 - MLOps (OpenClassrooms)
