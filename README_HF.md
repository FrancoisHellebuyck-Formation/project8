---
title: Lung Cancer Prediction
emoji: 🫁
colorFrom: green
colorTo: red
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# 🫁 Lung Cancer Prediction - MLOps Project

Application de prédiction de cancer du poumon avec interface Gradio et API FastAPI.

## 🎯 Fonctionnalités

- **🎨 Interface Gradio** : Interface utilisateur intuitive avec barre de progression colorée
- **📊 API REST FastAPI** : Endpoints `/predict`, `/predict_proba`, `/health`, `/logs`
- **🤖 Modèle ML LightGBM** : Modèle optimisé avec feature engineering automatique
- **📈 Feature Engineering** : 15 features d'entrée → 29 features totales (14 dérivées)
- **📝 Logs Redis** : Système de logging persistant avec Redis in-memory (256MB)

## 🚀 Utilisation

### Interface Gradio (Port 7860)

L'interface Gradio est accessible directement sur le port principal. Elle permet de :
- Saisir les informations du patient (âge, genre, symptômes)
- Obtenir une prédiction visuelle avec barre de probabilité
- Visualiser le risque : FAIBLE 🟢 / MODÉRÉ 🟠 / ÉLEVÉ 🔴

### API REST (Port 8000)

L'API FastAPI tourne en arrière-plan et peut être appelée directement :

**Endpoints disponibles :**
- `GET /` : Informations sur l'API
- `GET /health` : État de santé de l'API
- `POST /predict` : Prédiction binaire (0 ou 1)
- `POST /predict_proba` : Prédiction avec probabilités
- `GET /logs` : Récupérer les logs (limite configurable)
- `DELETE /logs` : Supprimer les logs

**Exemple de requête :**
```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
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
    "CHRONIC DISEASE": 0
  }'
```

## 📋 Features du modèle

**15 features d'entrée :**
- AGE, GENDER, SMOKING, ALCOHOL CONSUMING, PEER_PRESSURE
- YELLOW_FINGERS, ANXIETY, FATIGUE, ALLERGY
- WHEEZING, COUGHING, SHORTNESS OF BREATH
- SWALLOWING DIFFICULTY, CHEST PAIN, CHRONIC DISEASE

**14 features dérivées (automatiques) :**
- HIGH_RISK_PROFILE, AGE_SQUARED, TOTAL_SYMPTOMS
- RESPIRATORY_SYMPTOMS, CANCER_TRIAD, SMOKER_WITH_RESP_SYMPTOMS
- ADVANCED_SYMPTOMS, SYMPTOMS_PER_AGE, AGE_RISK_INTERACTION
- MALE_SMOKER, SYMPTOM_INTENSITY, RESPIRATORY_DISTRESS
- CHRONIC_SMOKER_SYMPTOMS, SYMPTOM_DIVERSITY

## ⚙️ Architecture

```
┌────────────────────────────────────────┐
│   Hugging Face Space Container         │
│                                        │
│  ┌──────────────────────────────┐     │
│  │   Gradio UI (Port 7860)      │◄────┼─── Interface publique
│  │   (Frontend)                 │     │
│  └────────────┬─────────────────┘     │
│               │ localhost HTTP        │
│               ↓                        │
│  ┌──────────────────────────────┐     │
│  │   FastAPI (Port 8000)        │     │
│  │   (Backend)                  │     │
│  └────────────┬─────────────────┘     │
│               │                        │
│               ↓                        │
│  ┌──────────────────────────────┐     │
│  │   Redis (Port 6379)          │     │
│  │   (In-Memory Logs)           │     │
│  └──────────────────────────────┘     │
│               ↑                        │
│  ┌────────────┴─────────────────┐     │
│  │   LightGBM Model             │     │
│  │   (ML Engine)                │     │
│  └──────────────────────────────┘     │
└────────────────────────────────────────┘
```

## 🏗️ Technologies

- **Python 3.13+** : Langage principal
- **FastAPI** : Framework API REST
- **Gradio** : Interface utilisateur interactive
- **LightGBM** : Algorithme de machine learning
- **Redis** : Base de données in-memory pour les logs
- **Pydantic v2** : Validation des données
- **Scikit-learn** : Pipeline ML
- **Docker** : Containerisation
- **pytest** : Tests unitaires (83% coverage)

## 📚 Documentation

- **Documentation API** : Disponible via `/docs` (Swagger UI)
- **Tests** : 126 tests unitaires avec 83% de couverture
- **CI/CD** : GitHub Actions avec tests automatiques
- **Code Quality** : Flake8 compliant (88 char max)

## ⚠️ Avertissement

Cette application est à **but éducatif uniquement** et ne remplace pas un diagnostic médical professionnel. Les prédictions doivent être interprétées par un professionnel de santé qualifié.

## 📄 Licence

MIT License - Projet OpenClassrooms MLOps (Partie 2/2)

---

**Développé avec ❤️ dans le cadre du parcours MLOps OpenClassrooms**
