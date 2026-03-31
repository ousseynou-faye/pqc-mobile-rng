from __future__ import annotations

"""
Orchestrateur DRBG de la baseline Sponge-only.

- Multiplexed Sponge est l'unique moteur DRBG.
- La machine a etats explicite reste la frontiere officielle.
"""

from dataclasses import dataclass, field

from .errors import (
    DRBGError,
    EngineUnavailableError,
    FailStopError,
    HealthCheckError,
    InvalidDRBGStateError,
    ReseedRequiredError,
)
from .interfaces import DRBGEngine
from .policy import DRBGPolicy
from .sponge_core import MultiplexedSpongeAdapter, build_reference_sponge
from .state import DRBGEvent, DRBGLifecycleState, DRBGState


@dataclass(slots=True)
class PQCCompositeDRBG:
    """Facade DRBG compatible avec l'ancien nom public, desormais sponge-only."""

    sponge_engine: MultiplexedSpongeAdapter = field(
        default_factory=lambda: MultiplexedSpongeAdapter(sponge_factory=build_reference_sponge)
    )
    policy: DRBGPolicy = field(default_factory=DRBGPolicy)
    state: DRBGState = field(default_factory=DRBGState)

    def _ensure_not_fail_stop(self) -> None:
        if self.state.lifecycle_state == DRBGLifecycleState.FAIL_STOP:
            raise FailStopError(
                "Le systeme est verrouille en FAIL_STOP jusqu'a une reinitialisation explicite."
            )

    def _validate_state_coherence(self) -> None:
        if not self.state.initialized:
            return
        if self.state.active_engine != self.sponge_engine.name:
            raise InvalidDRBGStateError("Etat incoherent: moteur actif invalide pour la baseline sponge-only.")


    def instantiate(self, seed_material: bytes, personalization: bytes = b"") -> None:
        """Instancie le moteur sponge et place la machine a etats en READY."""
        self._ensure_not_fail_stop()
        self.policy.validate()
        self.sponge_engine.instantiate(seed_material, personalization=personalization)
        self.state.mark_ready(
            active_engine=self.sponge_engine.name,
            reseed_reason="instantiate",
            degraded=False,
        )

    def _active_engine(self) -> DRBGEngine:
        self._validate_state_coherence()
        if not self.state.initialized or self.state.active_engine is None:
            raise InvalidDRBGStateError("Le DRBG n'est pas initialise.")
        if self.state.active_engine != self.sponge_engine.name:
            raise EngineUnavailableError("Le moteur actif declare n'est pas disponible.")
        return self.sponge_engine

    def _check_reseed_policy(self) -> None:
        if self.state.lifecycle_state == DRBGLifecycleState.NEED_RESEED:
            raise ReseedRequiredError("L'etat du systeme impose un reseed avant de continuer.")

        if self.policy.prediction_resistance:
            self.state.flags.prediction_resistance_request = True
            self.state.mark_need_reseed(reason="Prediction resistance active : reseed impose.")
            raise ReseedRequiredError(
                "Prediction resistance active : reseed requis avant Generate."
            )

        if self.state.request_counter >= self.policy.reseed_interval_requests:
            self.state.mark_need_reseed(reason="Le compteur de requetes a atteint la limite de reseed.")
            raise ReseedRequiredError("Le seuil de reseed a ete atteint.")

    def generate(self, nbytes: int, additional_input: bytes = b"") -> bytes:
        self._ensure_not_fail_stop()
        self._check_reseed_policy()

        engine = self._active_engine()
        health = engine.health()

        if not health.healthy:
            reason = f"Moteur actif non sain : {health.reason}"
            if self.policy.fail_stop_on_health_error:
                self.state.transition(DRBGEvent.HEALTH_FAILURE, reason=reason)
                raise FailStopError(
                    f"Echec sante du moteur actif ({health.engine_name}) : {health.reason}"
                )
            raise HealthCheckError(reason)

        try:
            out = engine.generate(nbytes, additional_input=additional_input)
        except (FailStopError, ReseedRequiredError):
            raise
        except Exception as exc:
            if self.policy.fail_stop_on_health_error:
                self.state.transition(DRBGEvent.HEALTH_FAILURE, reason=str(exc) or "Generation echouee.")
                raise FailStopError(f"Echec du moteur actif ({health.engine_name}) : {exc}") from exc
            if isinstance(exc, DRBGError):
                raise
            raise HealthCheckError(str(exc) or "Generation echouee.") from exc

        self.state.request_counter += 1
        self.state.generated_bytes_since_reseed += len(out)
        self.state.transition(DRBGEvent.GENERATE, reason="Generation nominale reussie.")
        return out

    def reseed(
        self,
        seed_material: bytes,
        additional_input: bytes = b"",
        reason: str = "manual_reseed",
    ) -> None:
        self._ensure_not_fail_stop()
        if self.state.lifecycle_state == DRBGLifecycleState.UNINITIALIZED:
            raise InvalidDRBGStateError("Je ne peux pas reseed un moteur non initialise.")
        if self.state.lifecycle_state == DRBGLifecycleState.ZEROIZED:
            raise InvalidDRBGStateError("Je ne peux pas reseed un moteur zeroized sans instantiate.")

        engine = self._active_engine()
        engine.reseed(seed_material, additional_input=additional_input)
        self.state.active_engine = engine.name
        self.state.last_reseed_reason = reason
        self.state.transition(DRBGEvent.RESEED, reason=reason)
        self.state.request_counter = 0
        self.state.generated_bytes_since_reseed = 0

    def signal_integrity_failure(self, reason: str = "") -> None:
        self.state.transition(
            DRBGEvent.INTEGRITY_FAILURE,
            reason=reason or "Violation d'integrite signalee.",
        )

    def reset_from_fail_stop(self, reason: str = "") -> None:
        if self.state.lifecycle_state != DRBGLifecycleState.FAIL_STOP:
            raise DRBGError("Le systeme n'est pas en FAIL_STOP.")

        self.state.transition(
            DRBGEvent.RESET_FROM_FAIL_STOP,
            reason=reason or "Reset explicite apres FAIL_STOP.",
        )
        self.sponge_engine.zeroize()
        self.state.active_engine = None
        self.state.request_counter = 0
        self.state.generated_bytes_since_reseed = 0
        self.state.flags.degraded_research = False

    def force_engine(self, engine_name: str) -> None:
        if not self.state.initialized:
            raise InvalidDRBGStateError(
                "Je ne peux pas changer de moteur si le systeme n'est pas initialise."
            )

        if engine_name == self.sponge_engine.name:
            self.state.active_engine = self.sponge_engine.name
            self.state.flags.degraded_research = False
            return

        if engine_name == self.lwr_engine.name:
            self.state.active_engine = self.lwr_engine.name
            self.state.flags.degraded_research = True
            return

        raise EngineUnavailableError(f"Moteur inconnu : {engine_name}")

    def export_state(self) -> dict[str, object]:
        active = None
        if self.state.initialized and self.state.active_engine is not None:
            try:
                active = self._active_engine().export_state()
            except Exception:
                active = {"error": "Impossible d'exporter l'etat du moteur actif."}

        return {
            "manager_state": self.state.export(),
            "policy": {
                "selection_mode": self.policy.selection_mode.value,
                "reseed_interval_requests": self.policy.reseed_interval_requests,
                "prediction_resistance": self.policy.prediction_resistance,
                "fail_stop_on_health_error": self.policy.fail_stop_on_health_error,
            },
            "active_engine_state": active,
        }

    def export_sealable_state(self) -> dict[str, object]:
        return {
            "version": 1,
            "manager_state": self.state.export(),
            "sponge_private_state": self.sponge_engine.export_private_state(),
        }

    def import_sealable_state(self, payload: dict[str, object]) -> None:
        if payload.get("version") != 1:
            raise DRBGError("Version de payload scellee non supportee.")
        manager_state = payload["manager_state"]
        if not isinstance(manager_state, dict):
            raise DRBGError("manager_state doit etre un dictionnaire.")

        self.state.lifecycle_state = DRBGLifecycleState(manager_state["lifecycle_state"])
        self.state.active_engine = manager_state["active_engine"]
        self.state.request_counter = int(manager_state["request_counter"])
        self.state.generated_bytes_since_reseed = int(manager_state["generated_bytes_since_reseed"])
        self.state.last_reseed_reason = str(manager_state["last_reseed_reason"])
        self.state.last_failure_reason = str(manager_state.get("last_failure_reason", ""))

        flags = manager_state["flags"]
        if not isinstance(flags, dict):
            raise DRBGError("manager_state.flags doit etre un dictionnaire.")
        self.state.flags.prediction_resistance_request = bool(flags["prediction_resistance_request"])
        self.state.flags.security_strength_reached = bool(flags["security_strength_reached"])
        self.state.flags.fail_stop = bool(flags["fail_stop"])
        self.state.flags.reseed_required = bool(flags["reseed_required"])
        self.state.flags.degraded_research = bool(flags["degraded_research"])
        self.state.transition_history = []

        sponge_private_state = payload.get("sponge_private_state")
        if isinstance(sponge_private_state, dict):
            self.sponge_engine.import_private_state(sponge_private_state)
        else:
            self.sponge_engine.zeroize()
        self._validate_state_coherence()

    def zeroize(self) -> None:
        self.sponge_engine.zeroize()
        self.state.mark_zeroized()
