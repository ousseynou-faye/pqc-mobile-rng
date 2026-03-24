from __future__ import annotations

from typing import Any

from software.api import get_rng_service


def get_health_status() -> dict[str, Any]:
    """Wrapper fin vers l'etat de sante synthetique du service canonique."""

    return get_rng_service().health_status()


def rng_health() -> dict[str, Any]:
    """
    Retourne un etat de sante public et non sensible du SDK RNG.

    La structure retournee ne contient ni seed, ni materiau d'entropie brut,
    ni etat interne complet du DRBG.
    """

    return get_rng_service().sdk_status()
