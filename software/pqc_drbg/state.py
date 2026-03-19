from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .errors import InvalidStateTransitionError

"""Je formalise ici l'état logique de la couche DRBG."""


class DRBGStatus(str, Enum):
    UNINITIALIZED = "uninitialized"
    READY = "ready"
    NEED_RESEED = "need_reseed"
    FAIL_STOP = "fail_stop"
    ZEROIZED = "zeroized"
    DEGRADED_RESEARCH = "degraded_research"


@dataclass(slots=True)
class DRBGFlags:
    """Je regroupe ici les drapeaux qui complètent l'état principal."""

    prediction_resistance_request: bool = False
    security_strength_reached: bool = False
    fail_stop: bool = False
    reseed_required: bool = False
    degraded_research: bool = False


@dataclass(slots=True)
class DRBGState:
    """
    Je représente ici l'état observable de l'orchestrateur DRBG.

    Je sépare l'état principal `status` des compteurs et des drapeaux afin de
    documenter plus clairement la machine à états dans le mémoire.
    """

    status: DRBGStatus = DRBGStatus.UNINITIALIZED
    active_engine: str | None = None
    request_counter: int = 0
    generated_bytes_since_reseed: int = 0
    last_reseed_reason: str = "uninitialized"
    last_failure_reason: str = ""
    flags: DRBGFlags = field(default_factory=DRBGFlags)

    @property
    def initialized(self) -> bool:
        """Je garde ici un alias de compatibilité pour le code existant."""

        return self.status in {DRBGStatus.READY, DRBGStatus.NEED_RESEED, DRBGStatus.DEGRADED_RESEARCH}

    @initialized.setter
    def initialized(self, value: bool) -> None:
        """
        Je garde ici un point d'écriture compatible avec l'ancien code.

        Je fais de `status` la source de vérité, mais j'accepte encore
        `state.initialized = True/False` pour éviter de casser les démos
        et les tests historiques du projet.
        """

        if value:
            if self.status == DRBGStatus.FAIL_STOP:
                raise InvalidStateTransitionError(
                    "Je refuse de quitter FAIL_STOP via initialized=True."
                )
            if self.status in {DRBGStatus.UNINITIALIZED, DRBGStatus.ZEROIZED}:
                self.status = DRBGStatus.READY
            return

        if self.status == DRBGStatus.FAIL_STOP:
            return
        if self.status != DRBGStatus.ZEROIZED:
            self.status = DRBGStatus.UNINITIALIZED

    def mark_ready(self, *, active_engine: str, reseed_reason: str, degraded: bool = False) -> None:
        """Je place ici le DRBG dans un état prêt après initialisation ou reseed."""

        self.active_engine = active_engine
        self.request_counter = 0
        self.generated_bytes_since_reseed = 0
        self.last_reseed_reason = reseed_reason
        self.last_failure_reason = ""
        self.flags.fail_stop = False
        self.flags.reseed_required = False
        self.flags.degraded_research = degraded
        self.status = DRBGStatus.DEGRADED_RESEARCH if degraded else DRBGStatus.READY

    def mark_need_reseed(self, *, reason: str) -> None:
        """Je demande ici un reseed explicite avant toute nouvelle génération."""

        if self.status not in {DRBGStatus.READY, DRBGStatus.DEGRADED_RESEARCH, DRBGStatus.NEED_RESEED}:
            raise InvalidStateTransitionError(
                f"Je refuse de demander un reseed depuis l'état {self.status.value}."
            )
        self.flags.reseed_required = True
        self.last_failure_reason = reason
        self.status = DRBGStatus.NEED_RESEED

    def mark_fail_stop(self, *, reason: str) -> None:
        """Je verrouille ici le DRBG en FAIL_STOP après une faute critique."""

        self.flags.fail_stop = True
        self.last_failure_reason = reason
        self.status = DRBGStatus.FAIL_STOP

    def mark_zeroized(self) -> None:
        """Je représente ici une destruction logique de l'état interne."""

        self.status = DRBGStatus.ZEROIZED
        self.active_engine = None
        self.request_counter = 0
        self.generated_bytes_since_reseed = 0
        self.last_reseed_reason = "zeroized"
        self.last_failure_reason = ""
        self.flags = DRBGFlags()

    def can_generate(self) -> bool:
        """Je dis ici si la machine autorise une opération de génération."""

        return self.status in {DRBGStatus.READY, DRBGStatus.DEGRADED_RESEARCH}

    def export(self) -> dict[str, object]:
        """J'exporte ici un état lisible et non sensible pour le diagnostic."""

        return {
            "status": self.status.value,
            "active_engine": self.active_engine,
            "request_counter": self.request_counter,
            "generated_bytes_since_reseed": self.generated_bytes_since_reseed,
            "last_reseed_reason": self.last_reseed_reason,
            "last_failure_reason": self.last_failure_reason,
            "initialized": self.initialized,
            "flags": {
                "prediction_resistance_request": self.flags.prediction_resistance_request,
                "security_strength_reached": self.flags.security_strength_reached,
                "fail_stop": self.flags.fail_stop,
                "reseed_required": self.flags.reseed_required,
                "degraded_research": self.flags.degraded_research,
            },
        }
