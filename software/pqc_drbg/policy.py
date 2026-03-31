from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .errors import DRBGError

"""Politique de securite du DRBG Sponge-only."""


class EngineSelectionMode(str, Enum):
    STRICT_SPONGE_ONLY = "strict_sponge_only"


@dataclass(slots=True)
class DRBGPolicy:
    """
    Centralise les choix de securite qui pilotent l'orchestrateur.

    Le mode nominal est `STRICT_SPONGE_ONLY`.
    Aucune selection de moteur alternative ni aucun fallback n'est autorise
    dans l'architecture finale.
    """

    selection_mode: EngineSelectionMode = EngineSelectionMode.STRICT_SPONGE_ONLY
    reseed_interval_requests: int = 2**16
    prediction_resistance: bool = False
    fail_stop_on_health_error: bool = True

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Valide la coherence minimale de la politique."""

        if self.reseed_interval_requests <= 0:
            raise DRBGError("Je dois avoir un reseed_interval_requests strictement positif.")

        if self.selection_mode != EngineSelectionMode.STRICT_SPONGE_ONLY:
            raise DRBGError("La baseline n'autorise que STRICT_SPONGE_ONLY.")
