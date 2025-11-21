#!/usr/bin/env python3
"""
Exemple d'utilisation du package proxy.

Ce script démontre comment utiliser le client proxy pour
interagir avec l'API FastAPI de manière programmatique.
"""

from src.proxy import APIProxyClient


def main():
    """Démontre l'utilisation du client proxy."""
    print("=" * 60)
    print("📦 Exemple d'utilisation du package proxy")
    print("=" * 60)
    print()

    # Initialiser le client
    client = APIProxyClient()
    print(f"🔗 Client initialisé: {client.api_url}")
    print()

    # 1. Vérifier la connexion
    print("1️⃣  Vérification de la connexion...")
    if client.check_connection():
        print("   ✅ API accessible")
    else:
        print("   ❌ API inaccessible - Assurez-vous que l'API est lancée")
        print("   Lancez l'API avec: make run-api")
        return
    print()

    # 2. Health check
    print("2️⃣  Health check...")
    response, status = client.get_health()
    if status == 200:
        print(f"   ✅ Status: {response.get('status')}")
        print(f"   📊 Modèle chargé: {response.get('model_loaded')}")
        print(f"   📊 Redis connecté: {response.get('redis_connected')}")
    else:
        print(f"   ❌ Erreur {status}: {response}")
    print()

    # 3. Informations API
    print("3️⃣  Informations de l'API...")
    response, status = client.get_root()
    if status == 200:
        print(f"   📝 Message: {response.get('message')}")
        print(f"   🔢 Version: {response.get('version')}")
        print(f"   🔌 Endpoints: {len(response.get('endpoints', {}))} disponibles")  # noqa: E501
    print()

    # 4. Prédiction
    print("4️⃣  Effectuer une prédiction...")
    patient_data = {
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

    response, status = client.post_predict(patient_data)
    if status == 200:
        print(f"   🔮 Prédiction: {response.get('prediction')}")
        print(f"   📊 Probabilité: {response.get('probability'):.2%}")
        print(f"   💬 Message: {response.get('message')}")
    else:
        print(f"   ❌ Erreur {status}: {response}")
    print()

    # 5. Probabilités détaillées
    print("5️⃣  Probabilités détaillées...")
    response, status = client.post_predict_proba(patient_data)
    if status == 200:
        probs = response.get('probabilities', [])
        print(f"   📊 Classe 0 (sain): {probs[0]:.2%}")
        print(f"   📊 Classe 1 (malade): {probs[1]:.2%}")
    print()

    # 6. Récupérer les logs
    print("6️⃣  Récupérer les derniers logs...")
    response, status = client.get_logs(limit=5, offset=0)
    if status == 200:
        total = response.get('total', 0)
        logs = response.get('logs', [])
        print(f"   📋 Total de logs: {total}")
        print(f"   📋 Logs récupérés: {len(logs)}")
        if logs:
            print(f"   📋 Premier log: {logs[0].get('level')} - "
                  f"{logs[0].get('message')[:50]}...")
    print()

    # 7. Prédictions en batch
    print("7️⃣  Prédictions en batch...")
    patients = [
        {**patient_data, "AGE": 50},
        {**patient_data, "AGE": 60},
        {**patient_data, "AGE": 70}
    ]

    results = client.batch_predict(patients)
    print(f"   📊 {len(results)} prédictions effectuées")
    for i, (response, status) in enumerate(results, 1):
        if status == 200:
            print(f"   📊 Patient {i}: Prédiction = "
                  f"{response.get('prediction')}, "
                  f"Probabilité = {response.get('probability'):.2%}")
    print()

    print("=" * 60)
    print("✅ Exemple terminé avec succès!")
    print("=" * 60)
    print()
    print("📚 Pour plus d'informations:")
    print("   - Documentation: docs/PROXY_DOCUMENTATION.md")
    print("   - Interface Gradio: make run-proxy")
    print("   - Tests: make test-proxy")


if __name__ == "__main__":
    main()
