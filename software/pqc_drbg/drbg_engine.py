from __future__ import annotations

"""
J'orchestre ici les deux moteurs DRBG :
- Module-LWR comme moteur nominal ;
- Multiplexed Sponge comme moteur secondaire.

Je m'appuie sur une vraie machine à états sécurisée pour rendre
les transitions explicites et auditables.
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
from .lwr_core import ModuleLWRCore
from .policy import DRBGPolicy, EngineSelectionMode
from .sponge_core import MultiplexedSpongeAdapter
from .state import DRBGEvent, DRBGLifecycleState, DRBGState


@dataclass(slots=True)
class PQCCompositeDRBG:
    """
    Je construis ici un gestionnaire de moteurs post-quantiques.

    Je conserve :
    - Module-LWR comme moteur nominal ;
    - Multiplexed Sponge comme moteur secondaire ;
    - une machine à états explicite ;
    - un comportement FAIL_STOP en cas de faute critique.
    """

    lwr_engine: ModuleLWRCore = field(default_factory=ModuleLWRCore)
    sponge_engine: MultiplexedSpongeAdapter | None = None
    policy: DRBGPolicy = field(default_factory=DRBGPolicy)
    state: DRBGState = field(default_factory=DRBGState)

    def _select_engine_for_instantiate(self) -> DRBGEngine:
        """Je choisis ici le moteur d'instanciation selon la politique active."""

        if self.policy.selection_mode == EngineSelectionMode.FORCE_SPONGE_RESEARCH:
            if self.sponge_engine is None:
                raise EngineUnavailableError("Le mode FORCE_SPONGE_RESEARCH exige un moteur sponge.")
            return self.sponge_engine
        return self.lwr_engine

    def _ensure_not_fail_stop(self) -> None:
        """Je refuse ici toute opération tant que le système reste en FAIL_STOP."""

        if self.state.lifecycle_state == DRBGLifecycleState.FAIL_STOP:
            raise FailStopError(
                "Le système est verrouillé en FAIL_STOP jusqu'à une réinitialisation explicite."
            )

    def instantiate(self, seed_material: bytes, personalization: bytes = b"") -> None:
        """
        J'initialise ici le moteur choisi selon la politique active.

        Je conserve Module-LWR comme moteur nominal.
        Je réserve le sponge au mode recherche ou au fallback expérimental.
        """

        self._ensure_not_fail_stop()
        engine = self._select_engine_for_instantiate()
        engine.instantiate(seed_material, personalization=personalization)
        self.state.mark_ready(
            active_engine=engine.name,
            reseed_reason="instantiate",
            degraded=(engine.name == "multiplexed_sponge"),
        )

    def _active_engine(self) -> DRBGEngine:
        """Je retourne ici le moteur actif après validation de l'état logique."""

        if not self.state.initialized or self.state.active_engine is None:
            raise InvalidDRBGStateError("Le DRBG composite n'est pas initialisé.")

        if self.state.active_engine == self.lwr_engine.name:
            return self.lwr_engine

        if self.sponge_engine is not None and self.state.active_engine == self.sponge_engine.name:
            return self.sponge_engine

        raise EngineUnavailableError("Le moteur actif déclaré n'est pas disponible.")

    def _check_reseed_policy(self) -> None:
        """
        Je fais respecter ici la politique de reseed.

        Je transforme le dépassement de seuil en vrai état `NEED_RESEED`.
        """

        if self.state.lifecycle_state == DRBGLifecycleState.NEED_RESEED:
            raise ReseedRequiredError(
                "L'état du système impose un reseed avant de continuer."
            )

        if self.policy.prediction_resistance:
            self.state.flags.prediction_resistance_request = True
            self.state.mark_need_reseed(reason="Prediction resistance active : reseed imposé.")
            raise ReseedRequiredError(
                "Prediction resistance active : reseed requis avant Generate."
            )

        if self.state.request_counter >= self.policy.reseed_interval_requests:
            self.state.mark_need_reseed(
                reason="Le compteur de requêtes a atteint la limite de reseed."
            )
            raise ReseedRequiredError("Le seuil de reseed a été atteint.")

    def _can_switch_to_sponge_after_exception(self, exc: Exception) -> bool:
        """
        Je décide ici si une bascule contrôlée vers sponge est autorisée.

        Je conserve le comportement expérimental déjà testé :
        - jamais pour masquer une faute de sécurité ;
        - uniquement si la politique l'autorise ;
        - uniquement si un moteur sponge est disponible.
        """

        if self.policy.selection_mode != EngineSelectionMode.ALLOW_EXPERIMENTAL_SPONGE_FALLBACK:
            return False

        if self.sponge_engine is None:
            return False

        if not self.policy.allow_fallback_on_unavailability_only:
            return False

        if isinstance(exc, (FailStopError, ReseedRequiredError, DRBGError)):
            return False

        return True

    def _switch_to_sponge_engine(self) -> None:
        """Je bascule ici explicitement vers le moteur sponge secondaire."""

        if self.sponge_engine is None:
            raise EngineUnavailableError("Aucun moteur sponge n'est disponible.")

        sponge_health = self.sponge_engine.health()
        if not sponge_health.healthy:
            raise HealthCheckError(
                f"Le moteur sponge n'est pas prêt pour la bascule : {sponge_health.reason}"
            )

        self.state.active_engine = self.sponge_engine.name
        self.state.flags.degraded_research = True

    def generate(self, nbytes: int, additional_input: bytes = b"") -> bytes:
        """
        Je produis ici des octets pseudo-aléatoires selon le moteur actif.

        Je verrouille le système en FAIL_STOP si la santé du moteur actif échoue.
        Je ne masque jamais une faute critique par un fallback silencieux.
        """

        self._ensure_not_fail_stop()
        self._check_reseed_policy()

        engine = self._active_engine()
        health = engine.health()

        if not health.healthy:
            reason = f"Moteur actif non sain : {health.reason}"
            if self.policy.fail_stop_on_health_error:
                self.state.transition(DRBGEvent.HEALTH_FAILURE, reason=reason)
                raise FailStopError(
                    f"Échec santé du moteur actif ({health.engine_name}) : {health.reason}"
                )
            raise HealthCheckError(reason)

        try:
            out = engine.generate(nbytes, additional_input=additional_input)
        except (FailStopError, ReseedRequiredError, DRBGError):
            raise
        except Exception as exc:
            if self._can_switch_to_sponge_after_exception(exc):
                self._switch_to_sponge_engine()
                out = self._active_engine().generate(nbytes, additional_input=additional_input)
            else:
                raise

        self.state.request_counter += 1
        self.state.generated_bytes_since_reseed += len(out)
        self.state.transition(DRBGEvent.GENERATE, reason="Génération nominale réussie.")
        return out

    def reseed(self, seed_material: bytes, additional_input: bytes = b"", reason: str = "manual_reseed") -> None:
        """Je rafraîchis ici le moteur actif et je remets l'état en READY."""

        self._ensure_not_fail_stop()
        if self.state.lifecycle_state == DRBGLifecycleState.UNINITIALIZED:
            raise InvalidDRBGStateError("Je ne peux pas reseed un moteur non initialisé.")
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
        """Je force ici l'entrée en FAIL_STOP après une violation d'intégrité."""

        self.state.transition(
            DRBGEvent.INTEGRITY_FAILURE,
            reason=reason or "Violation d'intégrité signalée.",
        )

    def reset_from_fail_stop(self, reason: str = "") -> None:
        """
        Je sors ici explicitement du mode FAIL_STOP.

        Je ne réinitialise pas automatiquement le moteur.
        Je remets seulement le composant dans un état où une nouvelle
        instanciation est autorisée.
        """

        if self.state.lifecycle_state != DRBGLifecycleState.FAIL_STOP:
            raise DRBGError("Le système n'est pas en FAIL_STOP.")

        self.state.transition(
            DRBGEvent.RESET_FROM_FAIL_STOP,
            reason=reason or "Reset explicite après FAIL_STOP.",
        )
        self.lwr_engine.zeroize()
        if self.sponge_engine is not None:
            self.sponge_engine.zeroize()
        self.state.active_engine = None
        self.state.request_counter = 0
        self.state.generated_bytes_since_reseed = 0
        self.state.flags.degraded_research = False

    def force_engine(self, engine_name: str) -> None:
        """
        Je force ici explicitement le moteur actif dans un cadre de test ou de recherche.
        """

        if not self.state.initialized:
            raise InvalidDRBGStateError(
                "Je ne peux pas changer de moteur si le système n'est pas initialisé."
            )

        if engine_name == self.lwr_engine.name:
            self.state.active_engine = self.lwr_engine.name
            self.state.flags.degraded_research = False
            return

        if self.sponge_engine is not None and engine_name == self.sponge_engine.name:
            self.state.active_engine = self.sponge_engine.name
            self.state.flags.degraded_research = True
            return

        raise EngineUnavailableError(f"Moteur inconnu : {engine_name}")

    def export_state(self) -> dict[str, object]:
        """J'exporte ici une vue consolidée du gestionnaire et du moteur actif."""

        active = None
        if self.state.initialized and self.state.active_engine is not None:
            try:
                active = self._active_engine().export_state()
            except Exception:
                active = {"error": "Impossible d'exporter l'état du moteur actif."}

        return {
            "manager_state": self.state.export(),
            "policy": {
                "selection_mode": self.policy.selection_mode.value,
                "reseed_interval_requests": self.policy.reseed_interval_requests,
                "prediction_resistance": self.policy.prediction_resistance,
                "fail_stop_on_health_error": self.policy.fail_stop_on_health_error,
                "allow_fallback_on_unavailability_only": self.policy.allow_fallback_on_unavailability_only,
            },
            "active_engine_state": active,
        }

    def export_sealable_state(self) -> dict[str, object]:
        """
        J'exporte ici un état scellable complet du DRBG composite.
        """

        return {
            "version": 1,
            "manager_state": self.state.export(),
            "lwr_private_state": self.lwr_engine.export_private_state(),
            "sponge_private_state": (
                self.sponge_engine.export_private_state()
                if self.sponge_engine is not None
                else None
            ),
        }

    def import_sealable_state(self, payload: dict[str, object]) -> None:
        """
        Je restaure ici un état scellé dans le DRBG composite.
        """

        manager_state = payload["manager_state"]
        if not isinstance(manager_state, dict):
            raise DRBGError("manager_state doit être un dictionnaire.")

        self.state.lifecycle_state = DRBGLifecycleState(manager_state["lifecycle_state"])
        self.state.active_engine = manager_state["active_engine"]
        self.state.request_counter = int(manager_state["request_counter"])
        self.state.generated_bytes_since_reseed = int(manager_state["generated_bytes_since_reseed"])
        self.state.last_reseed_reason = str(manager_state["last_reseed_reason"])
        self.state.last_failure_reason = str(manager_state.get("last_failure_reason", ""))

        flags = manager_state["flags"]
        if not isinstance(flags, dict):
            raise DRBGError("manager_state.flags doit être un dictionnaire.")
        self.state.flags.prediction_resistance_request = bool(flags["prediction_resistance_request"])
        self.state.flags.security_strength_reached = bool(flags["security_strength_reached"])
        self.state.flags.fail_stop = bool(flags["fail_stop"])
        self.state.flags.reseed_required = bool(flags["reseed_required"])
        self.state.flags.degraded_research = bool(flags["degraded_research"])
        self.state.transition_history = []

        lwr_private_state = payload["lwr_private_state"]
        if not isinstance(lwr_private_state, dict):
            raise DRBGError("lwr_private_state doit être un dictionnaire.")
        self.lwr_engine.import_private_state(lwr_private_state)

        sponge_private_state = payload.get("sponge_private_state")
        if self.sponge_engine is not None and isinstance(sponge_private_state, dict):
            self.sponge_engine.import_private_state(sponge_private_state)
        elif self.sponge_engine is not None:
            self.sponge_engine.zeroize()

    def zeroize(self) -> None:
        """J'efface ici au maximum tous les états des moteurs et du gestionnaire."""

        self.lwr_engine.zeroize()
        if self.sponge_engine is not None:
            self.sponge_engine.zeroize()
        self.state.mark_zeroized()
