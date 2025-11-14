"""
Simulateur d'utilisateurs pour l'API de prédiction.

Ce module permet de simuler des requêtes utilisateurs vers l'API
pour tester la charge et les performances.
"""

from .simulator import UserSimulator, SimulationConfig, SimulationResult

__all__ = ["UserSimulator", "SimulationConfig", "SimulationResult"]
