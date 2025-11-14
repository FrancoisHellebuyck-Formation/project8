#!/usr/bin/env python3
"""
Script de test pour vérifier les endpoints API proxy de Gradio.

Ce script teste les endpoints suivants:
- GET  /api/health
- POST /api/predict
- POST /api/predict_proba
- GET  /api/logs
"""

import json

import requests

# Configuration
GRADIO_URL = "http://localhost:7860"

# Payload de test
test_payload = {
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
    "CHRONIC DISEASE": 0,
}


def test_health():
    """Test de l'endpoint /api/health."""
    print("\n" + "=" * 60)
    print("TEST: GET /api/health")
    print("=" * 60)

    try:
        response = requests.get(f"{GRADIO_URL}/api/health", timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def test_predict():
    """Test de l'endpoint /api/predict."""
    print("\n" + "=" * 60)
    print("TEST: POST /api/predict")
    print("=" * 60)

    try:
        response = requests.post(
            f"{GRADIO_URL}/api/predict", json=test_payload, timeout=10
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def test_predict_proba():
    """Test de l'endpoint /api/predict_proba."""
    print("\n" + "=" * 60)
    print("TEST: POST /api/predict_proba")
    print("=" * 60)

    try:
        response = requests.post(
            f"{GRADIO_URL}/api/predict_proba", json=test_payload, timeout=10
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def test_logs():
    """Test de l'endpoint /api/logs."""
    print("\n" + "=" * 60)
    print("TEST: GET /api/logs?limit=10")
    print("=" * 60)

    try:
        response = requests.get(
            f"{GRADIO_URL}/api/logs?limit=10", timeout=10
        )
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Nombre de logs: {len(data.get('logs', []))}")
        print(f"Response (extrait): {json.dumps(data, indent=2)[:500]}...")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def main():
    """Exécute tous les tests."""
    print("\n🧪 Tests des endpoints API proxy de Gradio")
    print(f"URL Gradio: {GRADIO_URL}")
    print("\nAssurez-vous que:")
    print("1. L'API FastAPI tourne sur http://localhost:8000")
    print("2. L'interface Gradio tourne sur http://localhost:7860")
    print("3. Redis est accessible")

    results = {
        "Health": test_health(),
        "Predict": test_predict(),
        "Predict Proba": test_predict_proba(),
        "Logs": test_logs(),
    }

    # Résumé
    print("\n" + "=" * 60)
    print("RÉSUMÉ DES TESTS")
    print("=" * 60)

    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:20} : {status}")

    total = len(results)
    passed = sum(results.values())
    print(f"\nRésultat: {passed}/{total} tests réussis")

    if passed == total:
        print("\n🎉 Tous les tests ont réussi !")
        return 0
    else:
        print("\n⚠️ Certains tests ont échoué")
        return 1


if __name__ == "__main__":
    exit(main())
