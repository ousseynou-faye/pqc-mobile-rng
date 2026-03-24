from __future__ import annotations

from software.api import get_rng_service
from software.api.exceptions import RNGInvalidLengthError, RNGNotInitializedError, RNGStateError
from software.api.rng_service import RNGServiceError

MAX_PUBLIC_GENERATE_BYTES = 4096


def _validate_length(length: int) -> None:
    if isinstance(length, bool) or not isinstance(length, int):
        raise RNGInvalidLengthError("length doit etre un entier strictement positif.")
    if length <= 0:
        raise RNGInvalidLengthError("length doit etre > 0.")
    if length > MAX_PUBLIC_GENERATE_BYTES:
        raise RNGInvalidLengthError(
            f"length depasse la limite publique du SDK ({MAX_PUBLIC_GENERATE_BYTES} octets par appel)."
        )


def generate_bytes(length: int, additional_input: bytes = b"") -> bytes:
    """Wrapper fin vers la generation canonique."""

    return get_rng_service().generate_bytes(length, additional_input=additional_input)


def rng_get_bytes(length: int) -> bytes:
    """
    Retourne `length` octets pseudo-aleatoires via le RNG officiel.
    """

    _validate_length(length)
    service = get_rng_service()
    if service.drbg is None:
        raise RNGNotInitializedError(
            "Le RNG n'est pas initialise. Appelez rng_init() avant rng_get_bytes()."
        )
    try:
        return service.generate_bytes(length)
    except RNGServiceError as exc:
        raise RNGStateError(f"Echec de rng_get_bytes(): {exc}") from exc


def rng_generate(length: int) -> bytes:
    """Alias public de `rng_get_bytes()`."""

    return rng_get_bytes(length)
