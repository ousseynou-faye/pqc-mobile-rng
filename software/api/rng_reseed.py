from __future__ import annotations

from typing import Any

from software.api import get_rng_service
from software.api.exceptions import RNGNotInitializedError, RNGRestoreError, RNGStateError
from software.api.rng_service import ConditioningResult, RNGServiceError


def reseed_rng(*, additional_input: bytes = b"") -> ConditioningResult:
    """Wrapper fin vers le reseed canonique."""

    return get_rng_service().reseed_rng(additional_input=additional_input)


def checkpoint_state(*, payload_metadata: dict[str, Any] | None = None):
    """Wrapper fin vers le checkpoint d'etat canonique."""

    return get_rng_service().checkpoint_state(payload_metadata=payload_metadata)


def restore_state(*, payload_metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Wrapper fin vers la restauration d'etat canonique."""

    return get_rng_service().restore_state(payload_metadata=payload_metadata)


def rng_reseed(*, additional_input: bytes | None = None) -> bool:
    """Force un reseed controle du RNG courant."""

    payload = b"" if additional_input is None else additional_input
    service = get_rng_service()
    if service.drbg is None:
        raise RNGNotInitializedError(
            "Le RNG n'est pas initialise. Appelez rng_init() avant rng_reseed()."
        )
    try:
        service.reseed_rng(additional_input=payload)
    except RNGServiceError as exc:
        raise RNGStateError(f"Echec de rng_reseed(): {exc}") from exc
    return True


def rng_zeroize() -> bool:
    """Efface l'etat memoire du SDK RNG pour la session courante."""

    get_rng_service().zeroize()
    return True


def rng_restore_state(*, payload_metadata: dict[str, Any] | None = None) -> bool:
    """Restaure un etat scelle via la couche STATE existante."""

    try:
        get_rng_service().restore_state(payload_metadata=payload_metadata)
    except RNGServiceError as exc:
        raise RNGRestoreError(f"Echec de rng_restore_state(): {exc}") from exc
    return True
