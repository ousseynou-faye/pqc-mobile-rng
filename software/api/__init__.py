from __future__ import annotations

from .rng_service import RNGService, RNGServiceConfig

_default_service: RNGService | None = None


def get_rng_service(*, reset: bool = False, config: RNGServiceConfig | None = None) -> RNGService:
    """Retourne l'instance de service canonique partagee par les wrappers."""

    global _default_service
    if reset or _default_service is None:
        _default_service = RNGService(config=config or RNGServiceConfig())
    elif config is not None:
        _default_service = RNGService(config=config)
    return _default_service


from .exceptions import (  # noqa: E402
    RNGAPIError,
    RNGInvalidLengthError,
    RNGNotInitializedError,
    RNGProfileError,
    RNGRestoreError,
    RNGStateError,
)
from .rng_generate import rng_generate, rng_get_bytes  # noqa: E402
from .rng_health import rng_health  # noqa: E402
from .rng_init import rng_init  # noqa: E402
from .rng_reseed import rng_reseed, rng_restore_state, rng_zeroize  # noqa: E402

__all__ = [
    "RNGAPIError",
    "RNGInvalidLengthError",
    "RNGNotInitializedError",
    "RNGProfileError",
    "RNGRestoreError",
    "RNGStateError",
    "RNGService",
    "RNGServiceConfig",
    "get_rng_service",
    "rng_generate",
    "rng_get_bytes",
    "rng_health",
    "rng_init",
    "rng_reseed",
    "rng_restore_state",
    "rng_zeroize",
]
