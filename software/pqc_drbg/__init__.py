"""
J'expose ici les composants publics du DRBG post-quantique.

Dans cette étape, je structure le moteur nominal Module-LWR et
le moteur secondaire basé sur le Multiplexed Sponge.
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
from .state import DRBGFlags, DRBGState, DRBGStatus

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
    "DRBGState",
    "DRBGStatus",
    "PQCCompositeDRBG",
]
