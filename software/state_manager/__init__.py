"""
J'expose ici les composants publics de la couche STATE / TEE simulé.

Cette couche me sert à :
- sceller l'état sensible ;
- vérifier l'intégrité du blob ;
- simuler un compteur monotone matériel ;
- détecter les tentatives de rollback ;
- restaurer proprement un état scellé.
"""

from .errors import (
    IntegrityError,
    RollbackDetectedError,
    SealedBlobNotFoundError,
    StateManagerError,
)
from .models import SealedBlob, TeeDeviceStatus
from .state_manager import StateManager
from .tee_simulator import SimulatedTEE

__all__ = [
    "IntegrityError",
    "RollbackDetectedError",
    "SealedBlobNotFoundError",
    "StateManagerError",
    "SealedBlob",
    "TeeDeviceStatus",
    "SimulatedTEE",
    "StateManager",
]
