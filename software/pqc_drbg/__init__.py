"""
Composants publics du DRBG post-quantique.

Le moteur nominal du depot est desormais Multiplexed Sponge.
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
