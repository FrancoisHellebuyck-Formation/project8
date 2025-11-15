# Simulateur d'Utilisateurs - API de Prédiction ML

Outil de simulation de charge pour tester les performances et la robustesse de l'API FastAPI et Gradio.

## 🎯 Fonctionnalités

- **Génération de données aléatoires** : Crée automatiquement des données de patients valides
- **Requêtes concurrentes** : Simule plusieurs utilisateurs simultanés
- **Métriques détaillées** : Temps de réponse, taux de succès, requêtes/seconde
- **Modes de test** : `/predict` et `/predict_proba`
- **Configuration flexible** : Paramètres personnalisables via CLI
- **Rapports visuels** : Affichage formaté des résultats
- **🆕 Simulation de data drift** : Génère un drift progressif sur l'âge des patients pour tester la robustesse du modèle
- **🔌 Mode Gradio** : Supporte les API Gradio (local et HuggingFace Spaces)

## 📋 Prérequis

Le simulateur utilise :
- `httpx` pour les requêtes HTTP asynchrones (mode FastAPI)
- `gradio_client` pour les requêtes Gradio (mode Gradio)

Ces dépendances sont déjà incluses dans le projet.

## ⚙️ Configuration

Le simulateur peut être configuré via des variables d'environnement dans le fichier `.env`. Les valeurs par défaut peuvent être modifiées sans avoir à spécifier les arguments en ligne de commande.

### Variables d'environnement disponibles

```bash
# Configuration du Simulateur
SIMULATOR_API_URL=http://localhost:8000      # URL de l'API
SIMULATOR_NUM_REQUESTS=100                    # Nombre de requêtes
SIMULATOR_CONCURRENT_USERS=10                 # Utilisateurs concurrents
SIMULATOR_DELAY=0.0                           # Délai entre requêtes (s)
SIMULATOR_TIMEOUT=30.0                        # Timeout par requête (s)
SIMULATOR_ENDPOINT=/predict                   # Endpoint à tester
SIMULATOR_VERBOSE=false                       # Mode verbeux

# Configuration du Data Drift
SIMULATOR_ENABLE_AGE_DRIFT=false              # Activer le drift
SIMULATOR_AGE_DRIFT_TARGET=70.0               # Âge cible du drift
SIMULATOR_AGE_DRIFT_START=0.0                 # Début du drift (%)
SIMULATOR_AGE_DRIFT_END=100.0                 # Fin du drift (%)
```

**Note** : Les arguments de la ligne de commande ont priorité sur les variables d'environnement.

## 🚀 Usage

### Mode FastAPI (par défaut)

```bash
# Simulation avec la configuration du .env
python -m src.simulator

# Ou utiliser la commande Makefile
make simulate

# Spécifier le nombre de requêtes et d'utilisateurs (override .env)
python -m src.simulator --requests 200 --users 20

# Version courte
python -m src.simulator -r 500 -u 50

# API distante
python -m src.simulator --url http://api.example.com:8000 -r 100 -u 10

# Avec délai entre les requêtes (en secondes)
python -m src.simulator -r 100 -u 10 --delay 0.1

# Tester l'endpoint predict_proba
python -m src.simulator --endpoint /predict_proba -r 50 -u 5

# Mode verbose (affiche chaque requête)
python -m src.simulator -r 50 -u 5 -v

# Test de charge intensif
python -m src.simulator -r 1000 -u 100 --timeout 60
```

### 🔌 Mode Gradio

Le simulateur peut cibler l'API Gradio au lieu de l'API FastAPI directe. Ce mode est compatible avec HuggingFace Spaces.

```bash
# Simulation via Gradio en local
python -m src.simulator --use-gradio --gradio-url http://localhost:7860 -r 50 -u 5

# Ou utiliser le Makefile
make simulate-gradio-local

# Simulation via HuggingFace Spaces (Space public)
python -m src.simulator --use-gradio \
    --gradio-url https://francoisformation-oc-project8.hf.space \
    -r 50 -u 5

# Simulation via HuggingFace Spaces (Space privé avec token)
python -m src.simulator --use-gradio \
    --gradio-url https://francoisformation-oc-project8.hf.space \
    --hf-token hf_xxxxxxxxxxxxxxxxxxxxx \
    -r 50 -u 5

# Ou utiliser le Makefile (charge automatiquement HF_TOKEN depuis .env)
make simulate-gradio-hf

# Mode verbose pour voir chaque requête Gradio
python -m src.simulator --use-gradio --gradio-url http://localhost:7860 -r 20 -u 3 -v
```

**Notes sur le mode Gradio :**
- Le mode Gradio utilise `gradio_client` pour communiquer avec l'API Gradio
- Compatible avec HuggingFace Spaces (public et privé avec token)
- Les endpoints sont mappés automatiquement : `/predict` → `/predict_api`, `/predict_proba` → `/predict_proba_api`
- Les requêtes sont exécutées de manière concurrente via `ThreadPoolExecutor`

### 🔌🔄 Mode Gradio avec Data Drift

Vous pouvez combiner le mode Gradio avec la simulation de data drift pour tester la robustesse du modèle déployé sur HuggingFace Spaces.

```bash
# Drift via Gradio local (vers 75 ans)
python -m src.simulator --use-gradio --gradio-url http://localhost:7860 \
    -r 200 -u 10 --enable-age-drift --age-drift-target 75 -v

# Ou utiliser le Makefile
make simulate-gradio-drift-local

# Drift via HuggingFace Spaces (vers 75 ans)
python -m src.simulator --use-gradio \
    --gradio-url https://francoisformation-oc-project8.hf.space \
    --hf-token hf_xxxxxxxxxxxxxxxxxxxxx \
    -r 200 -u 10 --enable-age-drift --age-drift-target 75 -v

# Ou utiliser le Makefile (charge HF_TOKEN depuis .env)
make simulate-gradio-drift-hf

# Drift progressif via HuggingFace Spaces (50% à 100%)
python -m src.simulator --use-gradio \
    --gradio-url https://francoisformation-oc-project8.hf.space \
    --hf-token hf_xxxxxxxxxxxxxxxxxxxxx \
    -r 300 -u 15 --enable-age-drift \
    --age-drift-target 80 --age-drift-start 50 --age-drift-end 100 -v

# Ou utiliser le Makefile
make simulate-gradio-drift-progressive-hf
```

**Cas d'usage :**
- Tester la robustesse du modèle en production (HF Spaces) face au data drift
- Valider que le modèle déployé gère bien les changements de distribution
- Comparer les performances du modèle en local vs déployé avec drift

### 🔄 Simulation de Data Drift

Le simulateur peut générer un data drift progressif sur l'âge des patients pour tester la robustesse du modèle face aux changements de distribution des données.

```bash
# Activer le drift sur l'âge (vers 75 ans)
python -m src.simulator -r 200 -u 10 --enable-age-drift --age-drift-target 75

# Drift progressif entre 50% et 100% de la simulation
python -m src.simulator -r 500 -u 20 --enable-age-drift \
    --age-drift-target 80 --age-drift-start 50 --age-drift-end 100

# Drift immédiat vers une population âgée (85 ans)
python -m src.simulator -r 300 -u 15 --enable-age-drift --age-drift-target 85
```

**Comment fonctionne le drift ?**

Le drift évolue **linéairement** entre `--age-drift-start` et `--age-drift-end` :
- **Avant le début** : Distribution uniforme normale (20-90 ans)
- **Pendant le drift** : Transition progressive vers une distribution gaussienne centrée sur `--age-drift-target`
- **Après la fin** : Distribution gaussienne complète (moyenne = target, écart-type = 10)

**Analyser le drift :**

```bash
# Lancer l'analyseur de drift
python -m src.simulator.drift_analyzer
```

Cet outil affiche des statistiques par fenêtre pour visualiser l'évolution de l'âge moyen au cours de la simulation.

### Options disponibles

| Option | Court | Description | Défaut |
|--------|-------|-------------|--------|
| **Mode de simulation** | | | |
| `--use-gradio` | - | Utilise l'API Gradio au lieu de FastAPI | `False` |
| `--gradio-url` | - | URL Gradio (local ou HF Spaces) | `http://localhost:7860` |
| `--hf-token` | - | Token HuggingFace pour Spaces privés | `None` |
| **Configuration générale** | | | |
| `--url` | - | URL de base de l'API FastAPI | `http://localhost:8000` |
| `--requests` | `-r` | Nombre total de requêtes | `100` |
| `--users` | `-u` | Utilisateurs concurrents | `10` |
| `--delay` | `-d` | Délai entre requêtes (s) | `0.0` |
| `--timeout` | `-t` | Timeout par requête (s) | `30.0` |
| `--endpoint` | `-e` | Endpoint à tester | `/predict` |
| `--verbose` | `-v` | Mode verbeux | `False` |
| **Data Drift** | | | |
| `--enable-age-drift` | - | Active le data drift sur l'âge | `False` |
| `--age-drift-target` | - | Âge moyen cible du drift | `70.0` |
| `--age-drift-start` | - | Début du drift (%) | `0.0` |
| `--age-drift-end` | - | Fin du drift (%) | `100.0` |

## 📊 Exemple de sortie

```
🚀 Démarrage de la simulation...
   API: http://localhost:8000/predict
   Requêtes: 100
   Utilisateurs concurrents: 10

   Progression: 100.0%

╔══════════════════════════════════════════════════════════╗
║           RÉSULTATS DE LA SIMULATION                     ║
╠══════════════════════════════════════════════════════════╣
║ Requêtes totales      :        100            ║
║ Requêtes réussies     :        100            ║
║ Requêtes échouées     :          0            ║
║                                                          ║
║ Durée totale          :       5.23 s         ║
║ Temps de réponse moy. :      45.67 ms        ║
║ Temps de réponse min  :      23.12 ms        ║
║ Temps de réponse max  :      89.45 ms        ║
║                                                          ║
║ Requêtes par seconde  :      19.12 req/s     ║
╚══════════════════════════════════════════════════════════╝

Status codes:
  200: 100

Erreurs: 0

✅ Simulation terminée avec succès!
```

## 🔧 Usage programmatique

### Mode FastAPI

Vous pouvez utiliser le simulateur dans votre code Python :

```python
from src.simulator import UserSimulator, SimulationConfig

# Configuration personnalisée
config = SimulationConfig(
    api_url="http://localhost:8000",
    num_requests=50,
    concurrent_users=5,
    endpoint="/predict",
    verbose=True
)

# Lancer la simulation
simulator = UserSimulator(config)
result = simulator.run()

# Accéder aux résultats
print(f"Succès: {result.successful_requests}/{result.total_requests}")
print(f"Temps moyen: {result.avg_response_time:.2f}ms")
print(f"RPS: {result.requests_per_second:.2f}")
```

### Mode Gradio

```python
from src.simulator import UserSimulator, SimulationConfig

# Configuration pour Gradio local
config = SimulationConfig(
    use_gradio=True,
    gradio_url="http://localhost:7860",
    num_requests=50,
    concurrent_users=5,
    endpoint="/predict",
    verbose=True
)

# Configuration pour HuggingFace Spaces (privé)
config_hf = SimulationConfig(
    use_gradio=True,
    gradio_url="https://francoisformation-oc-project8.hf.space",
    hf_token="hf_xxxxxxxxxxxxxxxxxxxxx",
    num_requests=50,
    concurrent_users=5,
    endpoint="/predict_proba"
)

# Lancer la simulation
simulator = UserSimulator(config)
result = simulator.run()
print(result)
```

### Utilisation asynchrone (FastAPI uniquement)

```python
import asyncio
from src.simulator import UserSimulator, SimulationConfig

async def main():
    config = SimulationConfig(num_requests=100, concurrent_users=10)
    simulator = UserSimulator(config)
    result = await simulator.run_simulation()
    print(result)

asyncio.run(main())
```

**Note :** Le mode Gradio utilise `run_simulation_gradio()` qui est synchrone. Pour le mode Gradio, utilisez directement `simulator.run()`.

## 📈 Cas d'usage

### Mode FastAPI (local)

#### 1. Test de charge basique
Vérifier que l'API peut gérer un nombre modéré de requêtes :
```bash
python -m src.simulator -r 100 -u 10
```

#### 2. Test de performance
Mesurer les temps de réponse sous charge :
```bash
python -m src.simulator -r 500 -u 50 -v
```

#### 3. Test de stress
Tester les limites de l'API :
```bash
python -m src.simulator -r 2000 -u 200 --timeout 120
```

#### 4. Test de stabilité
Vérifier la stabilité sur une longue période avec délai :
```bash
python -m src.simulator -r 1000 -u 5 --delay 0.5
```

#### 5. Comparaison des endpoints
Comparer les performances de `/predict` et `/predict_proba` :
```bash
python -m src.simulator -r 100 -u 10 -e /predict
python -m src.simulator -r 100 -u 10 -e /predict_proba
```

### Mode Gradio (production)

#### 6. Test de production HuggingFace Spaces
Tester le modèle déployé en production :
```bash
make simulate-gradio-hf
# ou
python -m src.simulator --use-gradio \
    --gradio-url https://francoisformation-oc-project8.hf.space \
    --hf-token hf_xxx -r 100 -u 10 -v
```

#### 7. Test de robustesse avec drift
Tester la robustesse du modèle face au data drift en production :
```bash
make simulate-gradio-drift-hf
# ou
python -m src.simulator --use-gradio \
    --gradio-url https://francoisformation-oc-project8.hf.space \
    --hf-token hf_xxx -r 200 -u 10 --enable-age-drift --age-drift-target 75 -v
```

#### 8. Validation de déploiement
Valider qu'un nouveau déploiement fonctionne correctement :
```bash
# Test rapide (50 requêtes)
make simulate-gradio-hf

# Test approfondi avec drift progressif (300 requêtes)
make simulate-gradio-drift-progressive-hf
```

#### 9. Comparaison local vs production
Comparer les performances entre local et production :
```bash
# Local
python -m src.simulator -r 100 -u 10 -e /predict_proba

# Production (HF Spaces)
python -m src.simulator --use-gradio \
    --gradio-url https://francoisformation-oc-project8.hf.space \
    --hf-token hf_xxx -r 100 -u 10 -e /predict_proba
```

## 🧪 Tests avec l'API locale

Assurez-vous que l'API est en cours d'exécution avant de lancer le simulateur :

```bash
# Terminal 1 : Lancer l'API
make run-api

# Terminal 2 : Lancer le simulateur
python -m src.simulator -r 50 -u 5
```

## 📊 Métriques collectées

Le simulateur collecte et affiche les métriques suivantes :

- **Requêtes totales** : Nombre total de requêtes envoyées
- **Requêtes réussies** : Nombre de requêtes avec status 200
- **Requêtes échouées** : Nombre de requêtes en erreur
- **Durée totale** : Temps total de la simulation
- **Temps de réponse moyen** : Moyenne des temps de réponse
- **Temps de réponse min/max** : Plus rapide et plus lent
- **Requêtes par seconde** : Throughput de l'API
- **Distribution des status codes** : Répartition des codes HTTP
- **Liste des erreurs** : Détail des erreurs rencontrées

## 🎨 Données générées

Le simulateur génère automatiquement des données de patients aléatoires avec :
- **AGE** : Entre 20 et 90 ans
- **GENDER** : 0 (femme) ou 1 (homme)
- **Symptômes binaires** : 0 (non) ou 1 (oui) pour chaque symptôme
  - SMOKING, ALCOHOL CONSUMING, PEER_PRESSURE
  - YELLOW_FINGERS, ANXIETY, FATIGUE, ALLERGY
  - WHEEZING, COUGHING, SHORTNESS OF BREATH
  - SWALLOWING DIFFICULTY, CHEST PAIN, CHRONIC DISEASE

## ⚠️ Notes importantes

- **API démarrée** : L'API doit être en cours d'exécution avant de lancer le simulateur
- **Limites** : Respectez les limites de votre infrastructure (CPU, RAM, connexions)
- **Timeout** : Augmentez le timeout pour des charges très élevées
- **Production** : N'utilisez pas ce simulateur sur une API de production sans autorisation

## 🐛 Dépannage

### L'API ne répond pas
```bash
# Vérifier que l'API est accessible
curl http://localhost:8000/health

# Vérifier les logs de l'API
make docker-logs-api
```

### Trop d'erreurs de timeout
```bash
# Augmenter le timeout et réduire la charge
python -m src.simulator -r 100 -u 5 --timeout 60
```

### Erreurs de connexion
```bash
# Vérifier l'URL de l'API
python -m src.simulator --url http://localhost:8000 -r 10 -u 1 -v
```

## 📚 Ressources

- [httpx Documentation](https://www.python-httpx.org/)
- [asyncio Documentation](https://docs.python.org/3/library/asyncio.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
