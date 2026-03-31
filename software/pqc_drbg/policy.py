from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .errors import DRBGError

"""Politique de selection et de fallback des moteurs DRBG."""


class EngineSelectionMode(str, Enum):
    STRICT_SPONGE_ONLY = "strict_sponge_only"
    ALLOW_EXPERIMENTAL_LWR_FALLBACK = "allow_experimental_lwr_fallback"
    FORCE_LWR_RESEARCH = "force_lwr_research"
    # Aliases de transition pour les anciens noms publics.
    STRICT_LWR_ONLY = STRICT_SPONGE_ONLY
    ALLOW_EXPERIMENTAL_SPONGE_FALLBACK = ALLOW_EXPERIMENTAL_LWR_FALLBACK
    FORCE_SPONGE_RESEARCH = FORCE_LWR_RESEARCH


@dataclass(slots=True)
class DRBGPolicy:
    """
    Centralise les choix de securite qui pilotent l'orchestrateur.

    Le mode nominal est `STRICT_SPONGE_ONLY`.
    Le fallback vers Module-LWR reste explicite, limite a l'indisponibilite
    technique du moteur principal, et n'est jamais utilise pour masquer une
    faute critique.
    """

    selection_mode: EngineSelectionMode = EngineSelectionMode.STRICT_SPONGE_ONLY
    reseed_interval_requests: int = 2**16
    prediction_resistance: bool = False
    fail_stop_on_health_error: bool = True
    allow_fallback_on_unavailability_only: bool = True

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Valide la coherence minimale de la politique."""

        if self.reseed_interval_requests <= 0:
            raise DRBGError("Je dois avoir un reseed_interval_requests strictement positif.")

        if (
            self.selection_mode == EngineSelectionMode.STRICT_SPONGE_ONLY
            and not self.allow_fallback_on_unavailability_only
        ):
            raise DRBGError("Je refuse une politique STRICT_SPONGE_ONLY qui autorise un fallback.")

    def allows_research_lwr(self) -> bool:
        """Indique si la politique autorise un usage explicite de Module-LWR."""

        return self.selection_mode in {
            EngineSelectionMode.ALLOW_EXPERIMENTAL_LWR_FALLBACK,
            EngineSelectionMode.FORCE_LWR_RESEARCH,
        }

    def allows_research_sponge(self) -> bool:
        """Alias de transition vers la politique de recherche historique."""

        return self.allows_research_lwr()

    def allows_lwr_fallback_for_unavailability(self) -> bool:
        """
        Indique si un fallback controle vers Module-LWR est autorise.

        Ce fallback reste reserve a une indisponibilite technique detectee
        avant la generation, jamais a une faute de sante critique.
        """

        return (
            self.selection_mode == EngineSelectionMode.ALLOW_EXPERIMENTAL_LWR_FALLBACK
            and self.allow_fallback_on_unavailability_only
        )

    def allows_sponge_fallback_for_unavailability(self) -> bool:
        """Alias de transition vers l'ancien nom de helper de fallback."""

        return self.allows_lwr_fallback_for_unavailability()
