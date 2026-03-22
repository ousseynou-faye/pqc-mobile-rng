from __future__ import annotations

"""
Je formalise ici la vraie machine à états du DRBG.

Je veux distinguer clairement :
- l'état logique du composant ;
- les drapeaux de sécurité ;
- les transitions autorisées ;
- l'historique minimal des événements.
"""

from dataclasses import dataclass, field
from enum import Enum

from .errors import InvalidStateTransitionError


class DRBGLifecycleState(str, Enum):
    """
    Je définis ici les états logiques du composant DRBG.

    Je conserve des valeurs minuscules pour rester compatible avec
    les exports et les tests déjà présents dans le projet.
    """

    UNINITIALIZED = "uninitialized"
    READY = "ready"
    NEED_RESEED = "need_reseed"
    FAIL_STOP = "fail_stop"
    ZEROIZED = "zeroized"


class DRBGEvent(str, Enum):
    """Je définis ici les événements qui pilotent la machine à états."""

    INSTANTIATE = "instantiate"
    GENERATE = "generate"
    RESEED = "reseed"
    HEALTH_FAILURE = "health_failure"
    INTEGRITY_FAILURE = "integrity_failure"
    RESEED_LIMIT_REACHED = "reseed_limit_reached"
    ZEROIZE = "zeroize"
    RESET_FROM_FAIL_STOP = "reset_from_fail_stop"


DRBGStatus = DRBGLifecycleState


@dataclass(slots=True)
class DRBGFlags:
    """Je regroupe ici les drapeaux de sécurité associés au composant."""

    prediction_resistance_request: bool = False
    security_strength_reached: bool = False
    fail_stop: bool = False
    reseed_required: bool = False
    degraded_research: bool = False


@dataclass(slots=True)
class TransitionRecord:
    """Je conserve ici une trace minimale d'une transition importante."""

    event: str
    old_state: str
    new_state: str
    reason: str = ""


@dataclass(slots=True)
class DRBGState:
    """
    Je décris ici l'état global du gestionnaire de moteurs.

    Je garde :
    - un état logique explicite ;
    - le moteur actif ;
    - le compteur de requêtes ;
    - l'historique minimal des transitions ;
    - les drapeaux de sécurité dérivés.
    """

    lifecycle_state: DRBGLifecycleState = DRBGLifecycleState.UNINITIALIZED
    active_engine: str | None = None
    request_counter: int = 0
    generated_bytes_since_reseed: int = 0
    last_reseed_reason: str = "uninitialized"
    last_failure_reason: str = ""
    flags: DRBGFlags = field(default_factory=DRBGFlags)
    transition_history: list[TransitionRecord] = field(default_factory=list)

    @property
    def status(self) -> DRBGLifecycleState:
        """Je garde ici un alias de compatibilité vers l'état logique principal."""

        return self.lifecycle_state

    @status.setter
    def status(self, value: DRBGLifecycleState) -> None:
        """Je garde ici un alias d'écriture pour le code historique."""

        self.lifecycle_state = DRBGLifecycleState(value)

    @property
    def initialized(self) -> bool:
        """
        Je considère ici que le composant est initialisé s'il est prêt
        ou s'il attend explicitement un reseed.
        """

        return self.lifecycle_state in {
            DRBGLifecycleState.READY,
            DRBGLifecycleState.NEED_RESEED,
        }

    @initialized.setter
    def initialized(self, value: bool) -> None:
        """
        Je garde ici un point d'écriture compatible avec l'ancien code.

        Je fais de `lifecycle_state` la source de vérité, mais j'accepte encore
        `state.initialized = True/False` pour éviter de casser les démos
        et les tests historiques du projet.
        """

        if value:
            if self.lifecycle_state == DRBGLifecycleState.FAIL_STOP:
                raise InvalidStateTransitionError(
                    "Je refuse de quitter FAIL_STOP via initialized=True."
                )
            if self.lifecycle_state in {
                DRBGLifecycleState.UNINITIALIZED,
                DRBGLifecycleState.ZEROIZED,
            }:
                self.lifecycle_state = DRBGLifecycleState.READY
            return

        if self.lifecycle_state == DRBGLifecycleState.FAIL_STOP:
            return
        if self.lifecycle_state != DRBGLifecycleState.ZEROIZED:
            self.lifecycle_state = DRBGLifecycleState.UNINITIALIZED

    def _append_transition(
        self,
        event: DRBGEvent,
        old_state: DRBGLifecycleState,
        new_state: DRBGLifecycleState,
        reason: str = "",
    ) -> None:
        """J'enregistre ici une transition dans l'historique interne."""

        self.transition_history.append(
            TransitionRecord(
                event=event.value,
                old_state=old_state.value,
                new_state=new_state.value,
                reason=reason,
            )
        )

    def transition(self, event: DRBGEvent, reason: str = "") -> None:
        """
        J'applique ici une transition autorisée de la machine à états.

        Je garde volontairement une machine simple :
        - `INSTANTIATE` amène vers `READY` ;
        - `RESEED_LIMIT_REACHED` amène vers `NEED_RESEED` ;
        - toute faute de santé ou d'intégrité amène vers `FAIL_STOP` ;
        - `ZEROIZE` amène vers `ZEROIZED`.
        """

        old = self.lifecycle_state
        allowed: dict[DRBGLifecycleState, dict[DRBGEvent, DRBGLifecycleState]] = {
            DRBGLifecycleState.UNINITIALIZED: {
                DRBGEvent.INSTANTIATE: DRBGLifecycleState.READY,
                DRBGEvent.ZEROIZE: DRBGLifecycleState.ZEROIZED,
            },
            DRBGLifecycleState.READY: {
                DRBGEvent.GENERATE: DRBGLifecycleState.READY,
                DRBGEvent.RESEED: DRBGLifecycleState.READY,
                DRBGEvent.RESEED_LIMIT_REACHED: DRBGLifecycleState.NEED_RESEED,
                DRBGEvent.HEALTH_FAILURE: DRBGLifecycleState.FAIL_STOP,
                DRBGEvent.INTEGRITY_FAILURE: DRBGLifecycleState.FAIL_STOP,
                DRBGEvent.ZEROIZE: DRBGLifecycleState.ZEROIZED,
            },
            DRBGLifecycleState.NEED_RESEED: {
                DRBGEvent.RESEED: DRBGLifecycleState.READY,
                DRBGEvent.HEALTH_FAILURE: DRBGLifecycleState.FAIL_STOP,
                DRBGEvent.INTEGRITY_FAILURE: DRBGLifecycleState.FAIL_STOP,
                DRBGEvent.ZEROIZE: DRBGLifecycleState.ZEROIZED,
            },
            DRBGLifecycleState.FAIL_STOP: {
                DRBGEvent.RESET_FROM_FAIL_STOP: DRBGLifecycleState.UNINITIALIZED,
                DRBGEvent.ZEROIZE: DRBGLifecycleState.ZEROIZED,
            },
            DRBGLifecycleState.ZEROIZED: {
                DRBGEvent.INSTANTIATE: DRBGLifecycleState.READY,
                DRBGEvent.ZEROIZE: DRBGLifecycleState.ZEROIZED,
            },
        }

        state_rules = allowed.get(old, {})
        if event not in state_rules:
            raise InvalidStateTransitionError(
                f"Transition interdite : {old.value} --{event.value}--> ?"
            )

        new = state_rules[event]
        self.lifecycle_state = new
        self._append_transition(event, old, new, reason=reason)

        if new == DRBGLifecycleState.FAIL_STOP:
            self.flags.fail_stop = True
            self.last_failure_reason = reason

        if new == DRBGLifecycleState.NEED_RESEED:
            self.flags.reseed_required = True
            self.last_failure_reason = reason

        if new == DRBGLifecycleState.READY:
            self.flags.reseed_required = False
            self.flags.fail_stop = False
            self.last_failure_reason = ""

        if new == DRBGLifecycleState.ZEROIZED:
            self.flags.reseed_required = False
            self.flags.fail_stop = False
            self.active_engine = None
            self.request_counter = 0
            self.generated_bytes_since_reseed = 0
            self.last_reseed_reason = "zeroized"
            self.last_failure_reason = ""

    def mark_ready(self, *, active_engine: str, reseed_reason: str, degraded: bool = False) -> None:
        """Je place ici le DRBG dans un état prêt après instanciation ou reseed."""

        old = self.lifecycle_state
        self.active_engine = active_engine
        self.request_counter = 0
        self.generated_bytes_since_reseed = 0
        self.last_reseed_reason = reseed_reason
        self.last_failure_reason = ""
        self.flags.reseed_required = False
        self.flags.fail_stop = False
        self.flags.degraded_research = degraded
        self.lifecycle_state = DRBGLifecycleState.READY
        self._append_transition(DRBGEvent.RESEED if old == DRBGLifecycleState.NEED_RESEED else DRBGEvent.INSTANTIATE, old, self.lifecycle_state, reason=reseed_reason)

    def mark_need_reseed(self, *, reason: str) -> None:
        """Je demande ici un reseed explicite avant toute nouvelle génération."""

        self.transition(DRBGEvent.RESEED_LIMIT_REACHED, reason=reason)

    def mark_fail_stop(self, *, reason: str) -> None:
        """Je verrouille ici le système en FAIL_STOP après une faute critique."""

        event = DRBGEvent.INTEGRITY_FAILURE if "intégrité" in reason.lower() else DRBGEvent.HEALTH_FAILURE
        self.transition(event, reason=reason)

    def mark_zeroized(self) -> None:
        """Je représente ici un effacement logique explicite du composant."""

        self.transition(DRBGEvent.ZEROIZE, reason="Effacement explicite demandé.")

    def can_generate(self) -> bool:
        """Je dis ici si la machine autorise une opération de génération."""

        return self.lifecycle_state == DRBGLifecycleState.READY

    def export(self) -> dict[str, object]:
        """J'exporte ici une vue sérialisable et non sensible de l'état global."""

        return {
            "status": self.lifecycle_state.value,
            "lifecycle_state": self.lifecycle_state.value,
            "initialized": self.initialized,
            "active_engine": self.active_engine,
            "request_counter": self.request_counter,
            "generated_bytes_since_reseed": self.generated_bytes_since_reseed,
            "last_reseed_reason": self.last_reseed_reason,
            "last_failure_reason": self.last_failure_reason,
            "flags": {
                "prediction_resistance_request": self.flags.prediction_resistance_request,
                "security_strength_reached": self.flags.security_strength_reached,
                "fail_stop": self.flags.fail_stop,
                "reseed_required": self.flags.reseed_required,
                "degraded_research": self.flags.degraded_research,
            },
            "transition_history": [
                {
                    "event": item.event,
                    "old_state": item.old_state,
                    "new_state": item.new_state,
                    "reason": item.reason,
                }
                for item in self.transition_history
            ],
        }
