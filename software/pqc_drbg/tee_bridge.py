from __future__ import annotations

"""
Je fournis ici un pont léger entre le DRBG composite et la couche STATE / TEE simulé.
"""

from pathlib import Path
from typing import Any

from ..state_manager import SealedBlob, SimulatedTEE, StateManager


def build_state_manager(
    root_dir: str | Path = "state_data",
    *,
    device_id: str = "dev-001",
    namespace: str = "pqc_rng",
    blob_id: str = "drbg_state",
) -> StateManager:
    """
    Je construis ici un gestionnaire d'état prêt à l'emploi pour le DRBG.

    Je centralise dans cette fonction la création du TEE simulé et du
    gestionnaire afin de garder un point d'entrée simple côté application.
    """

    tee = SimulatedTEE(root_dir=root_dir, device_id=device_id, namespace=namespace)
    return StateManager(tee=tee, blob_id=blob_id)


def checkpoint_drbg_state(
    drbg: Any,
    state_manager: StateManager,
    payload_metadata: dict[str, Any] | None = None,
) -> SealedBlob:
    """
    Je scelle ici l'état d'un DRBG composite via la couche STATE.
    """

    return state_manager.checkpoint_drbg(drbg, payload_metadata=payload_metadata)


def restore_drbg_state(
    drbg: Any,
    state_manager: StateManager,
    payload_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Je restaure ici l'état d'un DRBG composite via la couche STATE.
    """

    return state_manager.restore_drbg(drbg, payload_metadata=payload_metadata)
