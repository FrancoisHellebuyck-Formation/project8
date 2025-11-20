"""Tests pour le monitoring de performance dans l'API."""

import os
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def enable_performance_monitoring():
    """Active temporairement le monitoring de performance."""
    original_value = os.environ.get('ENABLE_PERFORMANCE_MONITORING')
    os.environ['ENABLE_PERFORMANCE_MONITORING'] = 'true'
    yield
    if original_value is None:
        os.environ.pop('ENABLE_PERFORMANCE_MONITORING', None)
    else:
        os.environ['ENABLE_PERFORMANCE_MONITORING'] = original_value


@pytest.fixture
def disable_performance_monitoring():
    """Désactive temporairement le monitoring de performance."""
    original_value = os.environ.get('ENABLE_PERFORMANCE_MONITORING')
    os.environ['ENABLE_PERFORMANCE_MONITORING'] = 'false'
    yield
    if original_value is None:
        os.environ.pop('ENABLE_PERFORMANCE_MONITORING', None)
    else:
        os.environ['ENABLE_PERFORMANCE_MONITORING'] = original_value


def test_performance_monitor_module_import():
    """Vérifie que le module de performance monitoring peut être importé."""
    from src.api.performance_monitor import (
        PerformanceMonitor,
        PerformanceMetrics,
        performance_monitor
    )

    assert PerformanceMonitor is not None
    assert PerformanceMetrics is not None
    assert performance_monitor is not None


def test_performance_monitor_disabled(disable_performance_monitoring):
    """Vérifie que le monitoring est désactivé par défaut."""
    # Recharger pour prendre en compte la variable d'environnement
    from importlib import reload
    from src import config
    reload(config)

    from src.config import settings
    assert settings.ENABLE_PERFORMANCE_MONITORING is False


def test_performance_monitor_enabled(enable_performance_monitoring):
    """Vérifie que le monitoring peut être activé."""
    # Recharger pour prendre en compte la variable d'environnement
    from importlib import reload
    from src import config
    reload(config)

    from src.config import settings
    assert settings.ENABLE_PERFORMANCE_MONITORING is True


def test_performance_monitor_context_manager_disabled(
    disable_performance_monitoring
):
    """Teste le context manager avec monitoring désactivé."""
    from importlib import reload
    from src import config
    reload(config)
    from src.api import performance_monitor
    reload(performance_monitor)

    monitor = performance_monitor.PerformanceMonitor()
    assert monitor.enabled is False

    with monitor.profile():
        _ = sum(range(1000))

    metrics = monitor.get_metrics()
    assert metrics is None


def test_performance_monitor_context_manager_enabled(
    enable_performance_monitoring
):
    """Teste le context manager avec monitoring activé."""
    from importlib import reload
    from src import config
    reload(config)
    from src.api import performance_monitor
    reload(performance_monitor)

    monitor = performance_monitor.PerformanceMonitor()
    assert monitor.enabled is True

    with monitor.profile():
        _ = sum(range(1000))

    metrics = monitor.get_metrics()
    assert metrics is not None
    assert metrics.inference_time_ms > 0
    assert metrics.cpu_time_ms > 0
    assert metrics.memory_mb > 0
    assert metrics.function_calls > 0


def test_performance_metrics_format(enable_performance_monitoring):
    """Teste le formatage des métriques en dictionnaire."""
    from importlib import reload
    from src import config
    reload(config)
    from src.api import performance_monitor
    reload(performance_monitor)

    monitor = performance_monitor.PerformanceMonitor()

    with monitor.profile():
        _ = sum(range(1000))

    metrics = monitor.get_metrics()
    perf_dict = monitor.format_metrics_dict(metrics)

    assert 'performance' in perf_dict
    assert 'inference_time_ms' in perf_dict['performance']
    assert 'cpu_time_ms' in perf_dict['performance']
    assert 'memory_mb' in perf_dict['performance']
    assert 'memory_delta_mb' in perf_dict['performance']
    assert 'function_calls' in perf_dict['performance']
    assert 'top_functions' in perf_dict['performance']


def test_performance_metrics_json_format(enable_performance_monitoring):
    """Teste le format JSON des métriques loggées."""
    import json
    from importlib import reload
    from src import config
    reload(config)
    from src.api import performance_monitor
    reload(performance_monitor)

    monitor = performance_monitor.PerformanceMonitor()

    with monitor.profile():
        _ = sum(range(1000))

    metrics = monitor.get_metrics()

    # Simuler ce qui est loggé
    metrics_dict = {
        'performance_metrics': {
            'inference_time_ms': round(metrics.inference_time_ms, 2),
            'cpu_time_ms': round(metrics.cpu_time_ms, 2),
            'memory_mb': round(metrics.memory_mb, 2),
            'memory_delta_mb': round(metrics.memory_delta_mb, 2),
            'function_calls': metrics.function_calls,
            'latency_ms': round(metrics.inference_time_ms, 2),
            'top_functions': [
                {
                    'function': f['function'],
                    'file': f['file'],
                    'line': f['line'],
                    'cumulative_time_ms': round(f['cumulative_time_ms'], 2),
                    'total_time_ms': round(f['total_time_ms'], 2),
                    'calls': f['calls']
                }
                for f in metrics.top_functions
            ]
        }
    }

    # Vérifier que le JSON est valide
    json_string = json.dumps(metrics_dict)
    assert json_string is not None
    assert len(json_string) > 0

    # Vérifier qu'on peut le parser
    parsed = json.loads(json_string)
    assert 'performance_metrics' in parsed
    assert 'inference_time_ms' in parsed['performance_metrics']
    assert 'latency_ms' in parsed['performance_metrics']
    assert 'top_functions' in parsed['performance_metrics']
    assert isinstance(parsed['performance_metrics']['top_functions'], list)

    # Vérifier la structure des top_functions
    if parsed['performance_metrics']['top_functions']:
        func = parsed['performance_metrics']['top_functions'][0]
        assert 'function' in func
        assert 'file' in func
        assert 'line' in func
        assert 'cumulative_time_ms' in func
        assert 'total_time_ms' in func
        assert 'calls' in func


def test_api_prediction_with_monitoring(
    api_client: TestClient,
    enable_performance_monitoring
):
    """Teste une prédiction avec monitoring activé."""
    # Recharger la config
    from importlib import reload
    from src import config
    reload(config)

    patient_data = {
        "GENDER": 1,
        "AGE": 65,
        "SMOKING": 1,
        "YELLOW_FINGERS": 1,
        "ANXIETY": 0,
        "PEER_PRESSURE": 0,
        "CHRONIC DISEASE": 1,
        "FATIGUE": 1,
        "ALLERGY": 0,
        "WHEEZING": 1,
        "ALCOHOL CONSUMING": 0,
        "COUGHING": 1,
        "SHORTNESS OF BREATH": 1,
        "SWALLOWING DIFFICULTY": 0,
        "CHEST PAIN": 1
    }

    response = api_client.post("/predict", json=patient_data)
    assert response.status_code == 200

    data = response.json()
    assert "prediction" in data
    assert "probability" in data
    assert "message" in data


def test_api_predict_proba_with_monitoring(
    api_client: TestClient,
    enable_performance_monitoring
):
    """Teste une prédiction avec probabilités et monitoring activé."""
    # Recharger la config
    from importlib import reload
    from src import config
    reload(config)

    patient_data = {
        "GENDER": 1,
        "AGE": 65,
        "SMOKING": 1,
        "YELLOW_FINGERS": 1,
        "ANXIETY": 0,
        "PEER_PRESSURE": 0,
        "CHRONIC DISEASE": 1,
        "FATIGUE": 1,
        "ALLERGY": 0,
        "WHEEZING": 1,
        "ALCOHOL CONSUMING": 0,
        "COUGHING": 1,
        "SHORTNESS OF BREATH": 1,
        "SWALLOWING DIFFICULTY": 0,
        "CHEST PAIN": 1
    }

    response = api_client.post("/predict_proba", json=patient_data)
    assert response.status_code == 200

    data = response.json()
    assert "prediction" in data
    assert "probabilities" in data
    assert "message" in data
    assert len(data["probabilities"]) == 2


def test_performance_monitor_uses_api_logger():
    """
    Vérifie que le performance monitor utilise le logger 'api'
    qui est configuré avec Redis/stdout.
    """
    from src.api import performance_monitor
    import logging

    # Vérifier que le logger utilisé est bien "api"
    assert performance_monitor.logger.name == "api"

    # Vérifier que c'est le même logger que celui configuré
    api_logger = logging.getLogger("api")
    assert performance_monitor.logger is api_logger


def test_performance_metrics_include_transaction_id(
    caplog,
    enable_performance_monitoring
):
    """
    Vérifie que les métriques de performance incluent un transaction_id
    quand il est fourni.
    """
    import json
    import logging
    from importlib import reload
    from src import config
    reload(config)
    from src.api import performance_monitor
    reload(performance_monitor)

    # Configurer caplog pour capturer les logs "api"
    caplog.set_level(logging.INFO, logger="api")

    monitor = performance_monitor.PerformanceMonitor()

    # Créer des métriques de test
    metrics = performance_monitor.PerformanceMetrics(
        inference_time_ms=25.5,
        cpu_time_ms=24.8,
        memory_mb=256.0,
        memory_delta_mb=2.5,
        function_calls=1000,
        top_functions=[
            {
                'function': 'test_func',
                'file': 'test.py',
                'line': 10,
                'calls': 1,
                'total_time_ms': 10.0,
                'cumulative_time_ms': 20.0
            }
        ]
    )

    # Logger avec un transaction_id
    test_transaction_id = "test-uuid-12345"
    monitor.log_metrics(metrics, test_transaction_id)

    # Vérifier que le log contient le transaction_id
    assert len(caplog.records) > 0
    log_message = caplog.records[-1].message

    # Parser le JSON
    log_data = json.loads(log_message)
    assert "performance_metrics" in log_data
    assert "transaction_id" in log_data["performance_metrics"]
    assert log_data["performance_metrics"]["transaction_id"] == (
        test_transaction_id
    )


def test_performance_metrics_without_transaction_id(
    caplog,
    enable_performance_monitoring
):
    """
    Vérifie que les métriques de performance fonctionnent sans
    transaction_id.
    """
    import json
    import logging
    from importlib import reload
    from src import config
    reload(config)
    from src.api import performance_monitor
    reload(performance_monitor)

    # Configurer caplog pour capturer les logs "api"
    caplog.set_level(logging.INFO, logger="api")

    monitor = performance_monitor.PerformanceMonitor()

    # Créer des métriques de test
    metrics = performance_monitor.PerformanceMetrics(
        inference_time_ms=25.5,
        cpu_time_ms=24.8,
        memory_mb=256.0,
        memory_delta_mb=2.5,
        function_calls=1000,
        top_functions=[
            {
                'function': 'test_func',
                'file': 'test.py',
                'line': 10,
                'calls': 1,
                'total_time_ms': 10.0,
                'cumulative_time_ms': 20.0
            }
        ]
    )

    # Logger sans transaction_id
    monitor.log_metrics(metrics)

    # Vérifier que le log ne contient pas de transaction_id
    assert len(caplog.records) > 0
    log_message = caplog.records[-1].message

    # Parser le JSON
    log_data = json.loads(log_message)
    assert "performance_metrics" in log_data
    assert "transaction_id" not in log_data["performance_metrics"]
