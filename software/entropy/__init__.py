"""
J'expose ici les composants publics de la couche SRC.

Cette couche me sert à :
- collecter l'entropie brute,
- estimer prudemment la qualité des échantillons,
- accumuler un matériau exploitable par le conditionneur.
"""

from .models import EntropyChunk, HealthReport, PoolSnapshot, SensorFrame
from .cpu_jitter import CPUJitterSource
from .sensor_entropy import SensorEntropySource
from .health_estimator import HealthEstimator
from .entropy_pool import EntropyPool

__all__ = [
    "EntropyChunk",
    "HealthReport",
    "PoolSnapshot",
    "SensorFrame",
    "CPUJitterSource",
    "SensorEntropySource",
    "HealthEstimator",
    "EntropyPool",
]