# Tests de charge JMeter - ML API

Ce dossier contient les plans de test JMeter pour les tests de charge des endpoints `/api/predict` et `/api/predict_proba`.

## 📋 Contenu

- `API_Load_Test.jmx` - Plan de test JMeter complet
- `README.md` - Ce fichier (documentation)

## 🎯 Objectifs

Les tests de charge permettent de:

- ✅ Mesurer les performances sous charge des endpoints ML
- ✅ Identifier les goulots d'étranglement
- ✅ Vérifier la stabilité de l'API sous charge
- ✅ Tester la montée en charge (ramp-up)
- ✅ Valider les temps de réponse (SLA)
- ✅ Détecter les fuites mémoire

## 📦 Prérequis

### Installation de JMeter

#### macOS
```bash
# Via Homebrew
brew install jmeter

# Vérifier l'installation
jmeter --version
```

#### Linux
```bash
# Télécharger JMeter
wget https://dlcdn.apache.org//jmeter/binaries/apache-jmeter-5.6.3.tgz
tar -xzf apache-jmeter-5.6.3.tgz
cd apache-jmeter-5.6.3/bin

# Ajouter au PATH
export PATH=$PATH:$(pwd)
```

#### Windows
1. Télécharger depuis https://jmeter.apache.org/download_jmeter.cgi
2. Extraire l'archive
3. Ajouter `bin/` au PATH système

### API en cours d'exécution

Avant de lancer les tests, assurez-vous que l'API est démarrée:

```bash
# Méthode 1: Lancer l'API backend + UI hybride
make run-api          # Terminal 1 (port 8000)
make run-ui-fastapi   # Terminal 2 (port 7860)

# Méthode 2: Docker Compose
docker-compose up

# Vérifier que l'API répond
curl http://localhost:7860/api/health
```

## 🚀 Utilisation

### Mode GUI (Interface graphique)

Idéal pour créer/modifier les tests et visualiser les résultats en temps réel.

```bash
# Ouvrir JMeter avec le plan de test
jmeter -t jmeter/API_Load_Test.jmx

# Ou ouvrir JMeter puis charger le fichier
jmeter
```

**Dans l'interface JMeter**:
1. Cliquez sur "▶️ Start" (flèche verte) pour lancer le test
2. Consultez les résultats dans:
   - **View Results Tree** - Détails de chaque requête
   - **Summary Report** - Statistiques globales
   - **Graph Results** - Graphiques de performance
   - **View Results in Table** - Tableau détaillé

### Mode CLI (Ligne de commande)

Recommandé pour les tests automatisés et CI/CD.

#### Test avec paramètres par défaut

```bash
jmeter -n -t jmeter/API_Load_Test.jmx \
  -l jmeter/results.jtl \
  -e -o jmeter/report
```

#### Test avec paramètres personnalisés

```bash
# Test avec 50 utilisateurs pendant 2 minutes
jmeter -n -t jmeter/API_Load_Test.jmx \
  -Jusers=50 \
  -Jrampup=10 \
  -Jduration=120 \
  -l jmeter/results_50users.jtl \
  -e -o jmeter/report_50users
```

#### Test sur environnement distant (HuggingFace Spaces)

```bash
jmeter -n -t jmeter/API_Load_Test.jmx \
  -Jhost=francoisformation-oc-project8.hf.space \
  -Jport=443 \
  -Jprotocol=https \
  -Jusers=20 \
  -Jduration=60 \
  -l jmeter/results_hf.jtl \
  -e -o jmeter/report_hf
```

### Paramètres configurables

| Paramètre | Description | Défaut | Exemple |
|-----------|-------------|--------|---------|
| `host` | Hôte de l'API | `localhost` | `francoisformation-oc-project8.hf.space` |
| `port` | Port de l'API | `7860` | `443` (HTTPS) |
| `protocol` | Protocole | `http` | `https` |
| `users` | Nombre d'utilisateurs virtuels | `10` | `50` |
| `rampup` | Temps de montée en charge (secondes) | `5` | `30` |
| `duration` | Durée du test (secondes) | `60` | `300` |

## 📊 Scénarios de test

### Scénario 1: Test de base (10 users, 1 min)
```bash
jmeter -n -t jmeter/API_Load_Test.jmx \
  -l jmeter/results_basic.jtl \
  -e -o jmeter/report_basic
```

**Attendu**:
- Temps de réponse moyen: < 200ms
- Taux d'erreur: 0%
- Débit: ~600 req/min

### Scénario 2: Test de charge (50 users, 5 min)
```bash
jmeter -n -t jmeter/API_Load_Test.jmx \
  -Jusers=50 \
  -Jrampup=30 \
  -Jduration=300 \
  -l jmeter/results_load.jtl \
  -e -o jmeter/report_load
```

**Attendu**:
- Temps de réponse moyen: < 500ms
- Taux d'erreur: < 1%
- Débit: ~3000 req/min

### Scénario 3: Test de stress (100 users, 10 min)
```bash
jmeter -n -t jmeter/API_Load_Test.jmx \
  -Jusers=100 \
  -Jrampup=60 \
  -Jduration=600 \
  -l jmeter/results_stress.jtl \
  -e -o jmeter/report_stress
```

**Attendu**:
- Temps de réponse moyen: < 1000ms
- Taux d'erreur: < 5%
- Identifier les limites du système

### Scénario 4: Test d'endurance (20 users, 1 heure)
```bash
jmeter -n -t jmeter/API_Load_Test.jmx \
  -Jusers=20 \
  -Jrampup=60 \
  -Jduration=3600 \
  -l jmeter/results_endurance.jtl \
  -e -o jmeter/report_endurance
```

**Objectif**: Détecter les fuites mémoire et dégradations progressives

## 📈 Analyse des résultats

### Rapport HTML

Après l'exécution, un rapport HTML est généré dans `jmeter/report/`:

```bash
# Ouvrir le rapport dans le navigateur
open jmeter/report/index.html  # macOS
xdg-open jmeter/report/index.html  # Linux
start jmeter/report/index.html  # Windows
```

Le rapport contient:
- **Dashboard** - Vue d'ensemble
- **Response Times** - Temps de réponse (percentiles)
- **Throughput** - Débit (req/s)
- **Errors** - Taux d'erreur par endpoint
- **Top 5 Errors** - Erreurs les plus fréquentes

### Fichier JTL

Le fichier `.jtl` contient les résultats bruts:

```bash
# Voir les 10 premières lignes
head -n 10 jmeter/results.jtl

# Compter le nombre de requêtes
wc -l jmeter/results.jtl

# Filtrer les erreurs
grep "false" jmeter/results.jtl
```

### Métriques clés

| Métrique | Description | Seuil acceptable |
|----------|-------------|------------------|
| **Average** | Temps de réponse moyen | < 500ms |
| **Median** | Temps de réponse médian (50e percentile) | < 300ms |
| **90% Line** | 90e percentile | < 800ms |
| **95% Line** | 95e percentile | < 1000ms |
| **99% Line** | 99e percentile | < 2000ms |
| **Min** | Temps de réponse minimum | < 50ms |
| **Max** | Temps de réponse maximum | < 5000ms |
| **Error %** | Taux d'erreur | < 1% |
| **Throughput** | Débit (req/s) | > 10 req/s |

## 🔍 Détails du plan de test

### Configuration HTTP

- **Host**: Configurable via `-Jhost` (défaut: localhost)
- **Port**: Configurable via `-Jport` (défaut: 7860)
- **Protocol**: Configurable via `-Jprotocol` (défaut: http)
- **Timeout connexion**: 10 secondes
- **Timeout réponse**: 30 secondes
- **Keep-Alive**: Activé
- **Content-Type**: application/json

### Thread Groups

Le plan de test contient **2 Thread Groups**:

#### 1. Load Test - Predict Endpoint

**Configuration**:
- Endpoint: `POST /api/predict`
- Threads: Configurable (défaut: 10)
- Ramp-up: Configurable (défaut: 5s)
- Loop: Infini (limité par la durée)
- Throughput: 600 req/min par thread

**Données de test**:
- Âge: Aléatoire entre 30 et 80 ans
- Genre: Aléatoire (1=Homme, 2=Femme)
- 13 features binaires: Aléatoires (0 ou 1)

**Assertions**:
- ✅ Code HTTP 200
- ✅ Champ `prediction` présent dans la réponse JSON
- ✅ Champ `probability` présent dans la réponse JSON
- ✅ Temps de réponse < 1000ms

#### 2. Load Test - Predict Proba Endpoint

**Configuration**:
- Endpoint: `POST /api/predict_proba`
- Identique à Predict Endpoint

**Assertions**:
- ✅ Code HTTP 200
- ✅ Champ `probabilities` présent dans la réponse JSON
- ✅ Champ `prediction` présent dans la réponse JSON
- ✅ Temps de réponse < 1000ms

### Listeners (Rapports)

Le plan inclut 4 listeners:

1. **View Results Tree** - Détails de chaque requête
2. **Summary Report** - Statistiques globales
3. **Graph Results** - Graphiques temps réel
4. **View Results in Table** - Tableau détaillé

## 🐛 Dépannage

### Erreur: "Connection refused"

**Problème**: L'API n'est pas accessible

**Solutions**:
```bash
# Vérifier que l'API est démarrée
curl http://localhost:7860/api/health

# Vérifier les ports utilisés
lsof -i :7860
lsof -i :8000

# Redémarrer l'API
make run-ui-fastapi
```

### Erreur: "Out of memory"

**Problème**: JMeter manque de mémoire pour générer la charge

**Solution**: Augmenter la heap Java
```bash
# Éditer jmeter (Linux/macOS)
export HEAP="-Xms1g -Xmx4g"
jmeter -n -t jmeter/API_Load_Test.jmx ...

# Ou créer un fichier jmeter.properties
echo "heap=-Xms1g -Xmx4g" > jmeter.properties
```

### Erreur: "Too many open files"

**Problème**: Limite OS dépassée

**Solution**: Augmenter la limite
```bash
# Linux/macOS
ulimit -n 10000

# Vérifier
ulimit -n
```

### Résultats incohérents

**Problème**: Résultats varient beaucoup entre les runs

**Solutions**:
1. **Warmup**: Lancer un test court avant le test principal
2. **Isolation**: Désactiver autres applications
3. **Monitoring**: Surveiller CPU/RAM pendant le test
4. **Répétition**: Lancer le test 3 fois et moyenner

## 📚 Ressources

### Documentation JMeter

- **Site officiel**: https://jmeter.apache.org/
- **User Manual**: https://jmeter.apache.org/usermanual/index.html
- **Best Practices**: https://jmeter.apache.org/usermanual/best-practices.html

### Documentation projet

- [ARCHITECTURE.md](../docs/ARCHITECTURE.md) - Architecture technique
- [DIRECT_HTTP_ACCESS.md](../docs/DIRECT_HTTP_ACCESS.md) - Accès HTTP
- [PERFORMANCE_METRICS.md](../docs/PERFORMANCE_METRICS.md) - Métriques

### Tutoriels

- **JMeter CLI**: https://jmeter.apache.org/usermanual/get-started.html#non_gui
- **Assertions**: https://jmeter.apache.org/usermanual/component_reference.html#assertions
- **Distributed Testing**: https://jmeter.apache.org/usermanual/jmeter_distributed_testing_step_by_step.html

## 🔄 Intégration CI/CD

### GitHub Actions

Exemple de workflow pour exécuter les tests JMeter dans CI/CD:

```yaml
name: JMeter Load Test

on:
  schedule:
    - cron: '0 2 * * 1'  # Tous les lundis à 2h
  workflow_dispatch:      # Exécution manuelle

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install JMeter
        run: |
          wget https://dlcdn.apache.org//jmeter/binaries/apache-jmeter-5.6.3.tgz
          tar -xzf apache-jmeter-5.6.3.tgz
          echo "$(pwd)/apache-jmeter-5.6.3/bin" >> $GITHUB_PATH

      - name: Start API
        run: |
          docker-compose up -d
          sleep 30  # Attendre que l'API soit prête

      - name: Run JMeter Test
        run: |
          jmeter -n -t jmeter/API_Load_Test.jmx \
            -Jusers=20 \
            -Jduration=120 \
            -l jmeter/results.jtl \
            -e -o jmeter/report

      - name: Upload Results
        uses: actions/upload-artifact@v3
        with:
          name: jmeter-report
          path: jmeter/report/

      - name: Check Thresholds
        run: |
          # Vérifier que le taux d'erreur < 1%
          ERROR_RATE=$(awk -F',' 'NR>1 {sum+=$8} END {print sum/NR*100}' jmeter/results.jtl)
          if (( $(echo "$ERROR_RATE > 1" | bc -l) )); then
            echo "Error rate too high: $ERROR_RATE%"
            exit 1
          fi
```

## 📝 Notes

- Les tests génèrent des données aléatoires pour simuler des patients réalistes
- Le Constant Throughput Timer limite à 600 req/min par thread (10 req/s)
- Les assertions vérifient la structure JSON et les codes HTTP
- Les résultats sont sauvegardés dans des fichiers `.jtl` et des rapports HTML

---

**Version**: 1.0.0
**Dernière mise à jour**: 21 janvier 2025
**Auteur**: Project8 Team
