# Règles de développement pour Claude

## Architecture du projet

Ce projet est structuré en 3 parties distinctes :

### 1. Modèle ML (`./model`)
- Contient le modèle de machine learning entraîné
- Fichiers : `model.pkl`, `MLmodel`, `requirements.txt`, etc.
- Le modèle est chargé une seule fois (pattern Singleton) lors du démarrage de l'API

### 2. API FastAPI (`./src`)
- API REST permettant d'interroger le modèle ML
- **Toutes les sources Python doivent être placées dans le répertoire `./src`**
- Endpoints pour faire des prédictions via le modèle
- **Gestion des logs** : Les logs de l'API sont stockés dans un cache Redis et accessibles via l'endpoint `/logs`

### 3. Front-end Gradio (`./src`)
- Interface utilisateur basée sur Gradio
- Communique avec l'API FastAPI pour effectuer les prédictions
- Interface intuitive pour les utilisateurs finaux

## Déploiement Docker

Le projet utilise plusieurs conteneurs Docker :

### Docker 1 : API + Modèle
- Contient l'API FastAPI et le modèle ML
- **Le modèle est chargé une seule fois au démarrage (pattern Singleton)**
- Expose l'API REST pour les prédictions
- Connexion au cache Redis pour la gestion des logs

### Docker 2 : UI Gradio
- Contient l'interface utilisateur Gradio
- Communique avec le conteneur API via HTTP
- Interface séparée pour une meilleure scalabilité

### Redis (Cache)
- Cache Redis pour le stockage des logs de l'API
- Les logs sont consultables via l'endpoint `/logs` de l'API

## CI/CD

Le projet utilise **GitHub Actions** pour l'intégration et le déploiement continus :

- Automatisation des tests
- Validation du code (linting avec flake8)
- Build des images Docker
- Déploiement automatisé des conteneurs

## Standards de codage Python

Ce projet suit les règles de codage définies dans le fichier `.flake8`. Veuillez respecter les directives suivantes :

### Configuration Flake8

- **Longueur maximale de ligne** : 88 caractères
- **Erreurs ignorées** :
  - `E203` : Espaces avant ':'
  - `W503` : Saut de ligne avant opérateur binaire
  - `E402` : Imports de module pas en haut du fichier
  - `E501` : Ligne trop longue (déjà géré par max-line-length)

### Exclusions

Les répertoires suivants sont exclus de la vérification :
- `.git`
- `__pycache__`
- `.venv` / `venv`
- `.jupyter`
- `.ipynb_checkpoints`

### Règles spécifiques aux notebooks

Pour les fichiers `*.ipynb`, les erreurs suivantes sont ignorées :
- `E402` : Imports de module pas en haut du fichier
- `E501` : Ligne trop longue

## Instructions générales

Lors de l'écriture ou de la modification de code Python, assurez-vous de :

1. **Placer toutes les sources Python dans `./src`**
2. Respecter la limite de 88 caractères par ligne
3. Suivre les conventions PEP 8 (sauf les exceptions listées ci-dessus)
4. Maintenir un code propre et lisible
5. Vérifier la conformité avec `flake8` avant de commiter
6. Respecter l'architecture en 3 parties du projet
7. Utiliser le pattern Singleton pour le chargement du modèle ML

## Conventions Git

- **Ne pas ajouter de co-auteur** : Ne pas ajouter Claude comme co-auteur dans les commits Git
- Les commits doivent uniquement refléter l'auteur principal du projet
