# 📝 Changelog - Package Proxy

## [1.1.0] - 2025-01-21

### ✨ Nouvelles fonctionnalités

#### Utilisation automatique sur HuggingFace Spaces

Le package proxy est maintenant **utilisé automatiquement** sur HuggingFace Spaces via détection de l'environnement.

**Avant** :
- Interface UI utilisait des fonctions proxy simples partout
- Package proxy disponible mais non utilisé

**Après** :
- Sur HF : Interface UI utilise automatiquement `APIProxyClient`
- En local : Interface UI utilise les fonctions proxy simples (légères)
- Détection via variable d'environnement `SPACE_ID`

### 🔧 Modifications

#### src/ui/app.py

**Ajouts** (lignes 21-38) :
```python
# Détecter si on est sur HuggingFace Spaces
IS_HUGGINGFACE_SPACE = os.getenv("SPACE_ID") is not None

# Import conditionnel du package proxy pour HuggingFace
if IS_HUGGINGFACE_SPACE:
    from ..proxy import APIProxyClient
    proxy_client = APIProxyClient()
    logger.info("✅ Package proxy chargé pour HuggingFace Spaces")
else:
    proxy_client = None
    logger.info("ℹ️  Environnement local détecté")
```

**Modifications** :
- `api_health_proxy()` - Utilise proxy_client sur HF
- `api_predict_proxy()` - Utilise proxy_client sur HF
- `api_predict_proba_proxy()` - Utilise proxy_client sur HF
- `api_logs_proxy()` - Utilise proxy_client sur HF
- `api_clear_logs_proxy()` - Utilise proxy_client sur HF

**Pattern utilisé** :
```python
def api_health_proxy():
    if IS_HUGGINGFACE_SPACE and proxy_client:
        return proxy_client.get_health()  # Sur HF
    else:
        # Fonction simple en local
        response = requests.get(f"{settings.API_URL}/health")
        return response.json(), response.status_code
```

### 📚 Documentation

**Nouveaux fichiers** :
- `PROXY_USAGE_SUMMARY.md` (360 lignes) - Documentation complète du comportement automatique

**Fichiers mis à jour** :
- `docs/PROXY_DEPLOYMENT_HF.md` - Section "Utilisation sur HF" mise à jour

### 🧪 Tests

**Nouveaux tests effectués** :
- ✅ Test mode local (sans SPACE_ID) → Fonctions simples utilisées
- ✅ Test mode HuggingFace (avec SPACE_ID) → APIProxyClient chargé

**Résultats** :
```
Mode local:
  IS_HUGGINGFACE_SPACE: False
  proxy_client: None
  ✅ SUCCÈS

Mode HuggingFace:
  IS_HUGGINGFACE_SPACE: True
  proxy_client: APIProxyClient
  ✅ SUCCÈS
```

### ✅ Vérifications

- ✅ Flake8 compliant (0 erreur)
- ✅ Pas de régression fonctionnelle
- ✅ Fallback gracieux en cas d'erreur
- ✅ Logging informatif des deux modes
- ✅ Import conditionnel (pas d'overhead en local)

### 🎯 Avantages

**Sur HuggingFace Spaces** :
- ✅ Gestion d'erreurs robuste (timeout, connexion, JSON)
- ✅ Logging structuré
- ✅ Code testé (15 tests, 100% réussite)
- ✅ Évolutivité (retry, cache, métriques)

**En développement local** :
- ✅ Léger (pas d'import supplémentaire)
- ✅ Rapide (démarrage instantané)
- ✅ Simple (code direct)
- ✅ Suffisant (environnement contrôlé)

---

## [1.0.0] - 2025-01-21

### ✨ Création initiale du package proxy

#### Nouveau package : `src/proxy/`

**Fichiers créés** :
- `src/proxy/__init__.py` - Exports du package
- `src/proxy/client.py` (240 lignes) - Client API complet
- `src/proxy/gradio_app.py` (453 lignes) - Interface Gradio
- `src/proxy/README.md` - Documentation du package

#### Client API (`APIProxyClient`)

**Méthodes disponibles** :
- `get_root()` - GET /
- `get_health()` - GET /health
- `post_predict()` - POST /predict
- `post_predict_proba()` - POST /predict_proba
- `get_logs()` - GET /logs
- `delete_logs()` - DELETE /logs
- `batch_predict()` - Prédictions en batch
- `check_connection()` - Vérification connexion

**Fonctionnalités** :
- ✅ Gestion uniforme des erreurs (timeout, connexion, JSON)
- ✅ Timeouts configurables (défaut: 30s)
- ✅ Type hints complets
- ✅ Logging structuré

#### Interface Gradio

**6 sections** :
1. Vérification de connexion
2. Informations API (GET /)
3. Health check (GET /health)
4. Prédiction ML (POST /predict)
5. Probabilités (POST /predict_proba)
6. Gestion des logs (GET + DELETE /logs)

**Fonctionnalités** :
- ✅ Interface complète pour tous les endpoints
- ✅ Format JSON brut pour développeurs
- ✅ Pagination des logs
- ✅ Gestion des erreurs

#### Tests

**Fichier** : `tests/test_proxy.py` (228 lignes)

**15 tests unitaires** :
- test_init - Initialisation du client
- test_init_default_url - URL par défaut
- test_get_root_success - GET /
- test_get_health_success - GET /health
- test_post_predict_success - POST /predict
- test_post_predict_proba_success - POST /predict_proba
- test_get_logs_success - GET /logs
- test_delete_logs_success - DELETE /logs
- test_handle_timeout - Gestion timeout
- test_handle_connection_error - Erreur connexion
- test_handle_invalid_json - JSON invalide
- test_check_connection_success - Vérification connexion OK
- test_check_connection_failure - Vérification connexion KO
- test_batch_predict - Batch predictions
- test_get_api_info - Informations API

**Résultats** : 15/15 tests passent (100%)
**Couverture** : ~95%

#### Scripts

**Fichiers créés** :
- `run_proxy.py` (90 lignes) - Script CLI de lancement
- `example_proxy_usage.py` (130 lignes) - Exemple d'utilisation

**Commandes** :
```bash
python run_proxy.py --port 7860
python example_proxy_usage.py
```

#### Makefile

**Nouvelles commandes** :
- `make run-proxy` - Lance l'interface proxy
- `make test-proxy` - Lance les tests du proxy

#### Documentation

**Fichiers créés** :
- `docs/PROXY_DOCUMENTATION.md` (703 lignes) - Documentation complète
  - Architecture et diagrammes
  - Guide d'utilisation
  - API Reference
  - 4 exemples de code
  - Section dépannage

- `docs/PROXY_DEPLOYMENT_HF.md` (292 lignes) - Déploiement HF
  - Vérification du déploiement
  - Structure sur HF
  - Comparaison des interfaces
  - Cas d'usage

- `PROXY_QUICKSTART.md` (180 lignes) - Guide rapide
  - Démarrage en 30 secondes
  - Exemples minimaux
  - Commandes Make

**Fichiers mis à jour** :
- `README.md` - Ajout du package proxy
- `docs/MAKEFILE_GUIDE.md` - Documentation des commandes proxy
- `Makefile` - Aide mise à jour

#### Qualité du code

- ✅ Flake8 compliant (88 caractères max)
- ✅ Type hints complets
- ✅ Docstrings pour toutes les fonctions
- ✅ Pas de dépendances supplémentaires requises

#### Déploiement

**HuggingFace Spaces** :
- ✅ Package déployé dans `/app/src/proxy/`
- ✅ Dépendances satisfaites (gradio, requests)
- ✅ Dockerfile HF copie `src/`
- ✅ Workflow CI/CD conserve `src/`

---

## 📊 Statistiques

### Version 1.1.0 (actuelle)

**Code** :
- 1 fichier modifié : `src/ui/app.py`
- ~40 lignes ajoutées (détection + import)
- 5 fonctions modifiées (fallback conditionnel)

**Documentation** :
- 1 nouveau fichier : `PROXY_USAGE_SUMMARY.md` (360 lignes)
- 1 fichier mis à jour : `docs/PROXY_DEPLOYMENT_HF.md`

**Tests** :
- 2 nouveaux tests (mode local + mode HF)
- 100% de réussite maintenu

### Version 1.0.0

**Code total** :
- 693 lignes de code proxy (client + interface)
- 228 lignes de tests (15 tests)
- 90 lignes de scripts

**Documentation totale** :
- 1175 lignes de documentation (3 fichiers)
- 130 lignes d'exemples

**Total projet proxy** :
- ~2316 lignes (code + tests + docs + exemples)

---

## 🚀 Migration

### Pour utiliser le package proxy sur HF

**Aucune action requise !**

Le package est maintenant utilisé automatiquement sur HuggingFace Spaces.

### Pour tester en mode HF localement

```bash
SPACE_ID=test-space make run-ui
```

### Pour forcer le mode local

```bash
unset SPACE_ID
make run-ui
```

---

## 🔗 Liens

- [Documentation complète](docs/PROXY_DOCUMENTATION.md)
- [Guide de démarrage](PROXY_QUICKSTART.md)
- [Utilisation automatique](PROXY_USAGE_SUMMARY.md)
- [Déploiement HF](docs/PROXY_DEPLOYMENT_HF.md)

---

**Auteur** : OpenClassrooms - Projet 8
**Date** : 2025-01-21
