#!/usr/bin/env python3
"""
Script de test pour vérifier les endpoints API proxy sur Hugging Face Spaces.

Space URL: https://huggingface.co/spaces/FrancoisFormation/oc-project8
"""

import json

import requests

# Configuration - URL du Space Hugging Face
HF_SPACE_URL = "https://francoisformation-oc-project8.hf.space"

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
        url = f"{HF_SPACE_URL}/api/health"
        print(f"URL: {url}")
        response = requests.get(url, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de requête: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def test_predict():
    """Test de l'endpoint /api/predict."""
    print("\n" + "=" * 60)
    print("TEST: POST /api/predict")
    print("=" * 60)

    try:
        url = f"{HF_SPACE_URL}/api/predict"
        print(f"URL: {url}")
        print(f"Payload: {json.dumps(test_payload, indent=2)}")
        response = requests.post(url, json=test_payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de requête: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def test_predict_proba():
    """Test de l'endpoint /api/predict_proba."""
    print("\n" + "=" * 60)
    print("TEST: POST /api/predict_proba")
    print("=" * 60)

    try:
        url = f"{HF_SPACE_URL}/api/predict_proba"
        print(f"URL: {url}")
        response = requests.post(url, json=test_payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de requête: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def test_logs():
    """Test de l'endpoint /api/logs."""
    print("\n" + "=" * 60)
    print("TEST: GET /api/logs?limit=10")
    print("=" * 60)

    try:
        url = f"{HF_SPACE_URL}/api/logs?limit=10"
        print(f"URL: {url}")
        response = requests.get(url, timeout=30)
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Nombre de logs: {len(data.get('logs', []))}")
        print(f"Response (extrait): {json.dumps(data, indent=2)[:500]}...")
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de requête: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def test_gradio_interface():
    """Test de l'interface Gradio principale."""
    print("\n" + "=" * 60)
    print("TEST: GET / (Interface Gradio)")
    print("=" * 60)

    try:
        url = HF_SPACE_URL
        print(f"URL: {url}")
        response = requests.get(url, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        if response.status_code == 200:
            print("✅ Interface Gradio accessible")
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de requête: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def main():
    """Exécute tous les tests."""
    print("\n🧪 Tests des endpoints API proxy sur Hugging Face Spaces")
    print(f"Space URL: {HF_SPACE_URL}")
    print(f"Space Page: https://huggingface.co/spaces/FrancoisFormation/oc-project8")
    print("\n⚠️ Note: Le Space doit être en état 'Running' pour que les tests réussissent")

    results = {
        "Interface Gradio": test_gradio_interface(),
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
        print(f"\n📍 Votre Space est accessible à: {HF_SPACE_URL}")
        return 0
    else:
        print("\n⚠️ Certains tests ont échoué")
        print("\nVérifiez que:")
        print("1. Le Space est en état 'Running'")
        print("2. L'API FastAPI est démarrée (port 8000)")
        print("3. Redis est accessible")
        print("4. Les endpoints proxy sont bien configurés dans Gradio")
        return 1


if __name__ == "__main__":
    exit(main())
