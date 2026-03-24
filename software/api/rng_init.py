from __future__ import annotations

from software.api import get_rng_service
from software.api.exceptions import RNGProfileError, RNGStateError
from software.api.rng_service import ConditioningResult
from software.pqc_drbg import PQCCompositeDRBG

_SUPPORTED_PROFILES = {"baseline", "default"}


def _normalize_profile(profile: str | None) -> str:
    normalized = "baseline" if profile is None else profile.strip().lower()
    if normalized not in _SUPPORTED_PROFILES:
        raise RNGProfileError(
            f"Profil SDK non supporte: {profile!r}. Profils disponibles: baseline, default."
        )
    return "baseline" if normalized == "default" else normalized


def build_entropy_seed() -> ConditioningResult:
    """Wrapper fin vers la construction canonique de seed."""

    return get_rng_service().build_entropy_seed()


def instantiate_rng(*, personalization: bytes | None = None) -> PQCCompositeDRBG:
    """Wrapper fin vers l'instanciation canonique du RNG."""

    return get_rng_service().instantiate_rng(personalization=personalization)


def rng_init(
    *,
    personalization: bytes | None = None,
    force_reinit: bool = False,
    profile: str | None = None,
) -> bool:
    """
    Initialise le SDK RNG pour le processus courant.

    Returns:
        `True` si le RNG est pret pour la generation.
    """

    normalized_profile = _normalize_profile(profile)
    config = None
    if force_reinit:
        service = get_rng_service()
        config = service.config
        config.profile = normalized_profile
    service = get_rng_service(reset=force_reinit, config=config)
    if not force_reinit and service.drbg is not None:
        return True

    service.config.profile = normalized_profile
    try:
        service.instantiate_rng(personalization=personalization)
    except Exception as exc:
        raise RNGStateError(f"Echec de rng_init(): {exc}") from exc
    return True
