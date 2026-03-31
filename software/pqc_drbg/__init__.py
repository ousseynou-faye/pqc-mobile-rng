"""
Composants publics du DRBG post-quantique.

Le moteur nominal du depot est desormais Multiplexed Sponge.
Module-LWR reste disponible comme moteur secondaire et experimental.
"""

from .drbg_engine import PQCCompositeDRBG
from .errors import (
    DRBGError,
    EngineUnavailableError,
    FailStopError,
    HealthCheckError,
    InvalidDRBGStateError,
    InvalidStateTransitionError,
    ReseedRequiredError,
)
from .interfaces import DRBGEngine, EngineHealth
from .params import LWRParams, default_lwr_params
from .policy import DRBGPolicy, EngineSelectionMode
from .state import DRBGEvent, DRBGFlags, DRBGLifecycleState, DRBGState, DRBGStatus, TransitionRecord

__all__ = [
    "DRBGError",
    "EngineUnavailableError",
    "FailStopError",
    "HealthCheckError",
    "InvalidDRBGStateError",
    "InvalidStateTransitionError",
    "ReseedRequiredError",
    "DRBGEngine",
    "EngineHealth",
    "LWRParams",
    "default_lwr_params",
    "DRBGPolicy",
    "EngineSelectionMode",
    "DRBGFlags",
    "DRBGEvent",
    "DRBGLifecycleState",
    "DRBGState",
    "DRBGStatus",
    "TransitionRecord",
    "PQCCompositeDRBG",
]
