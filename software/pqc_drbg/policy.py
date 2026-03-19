from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .errors import DRBGError

"""Je définis ici la politique d'utilisation des moteurs DRBG."""


class EngineSelectionMode(str, Enum):
    STRICT_LWR_ONLY = "strict_lwr_only"
    ALLOW_EXPERIMENTAL_SPONGE_FALLBACK = "allow_experimental_sponge_fallback"
    FORCE_SPONGE_RESEARCH = "force_sponge_research"


@dataclass(slots=True)
class DRBGPolicy:
    """
    Je centralise ici les choix de sécurité qui pilotent l'orchestrateur.

    Je considère `STRICT_LWR_ONLY` comme le mode nominal.
    Je réserve le mode de fallback au cas d'indisponibilité technique du LWR.
    Je réserve `FORCE_SPONGE_RESEARCH` aux scénarios de recherche contrôlés.
    """

    selection_mode: EngineSelectionMode = EngineSelectionMode.STRICT_LWR_ONLY
    reseed_interval_requests: int = 2**16
    prediction_resistance: bool = False
    fail_stop_on_health_error: bool = True
    allow_fallback_on_unavailability_only: bool = True

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Je valide ici la cohérence minimale de la politique."""

        if self.reseed_interval_requests <= 0:
            raise DRBGError("Je dois avoir un reseed_interval_requests strictement positif.")

        if (
            self.selection_mode == EngineSelectionMode.STRICT_LWR_ONLY
            and not self.allow_fallback_on_unavailability_only
        ):
            raise DRBGError("Je refuse une politique STRICT_LWR_ONLY qui autorise un fallback.")

    def allows_research_sponge(self) -> bool:
        """Je dis ici si la politique autorise un usage explicite du moteur sponge."""

        return self.selection_mode in {
            EngineSelectionMode.ALLOW_EXPERIMENTAL_SPONGE_FALLBACK,
            EngineSelectionMode.FORCE_SPONGE_RESEARCH,
        }

    def allows_sponge_fallback_for_unavailability(self) -> bool:
        """
        Je dis ici si un fallback contrôlé vers le sponge est autorisé.

        Je limite volontairement ce cas à une indisponibilité technique
        détectée avant la génération, jamais à une faute de santé critique.
        """

        return (
            self.selection_mode == EngineSelectionMode.ALLOW_EXPERIMENTAL_SPONGE_FALLBACK
            and self.allow_fallback_on_unavailability_only
        )
