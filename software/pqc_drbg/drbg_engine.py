from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from .errors import DRBGError, FailStopError, ReseedRequiredError
from .interfaces import DRBGEngine
from .lwr_core import ModuleLWRCore
from .policy import DRBGPolicy, EngineSelectionMode
from .sponge_core import MultiplexedSpongeAdapter
from .state import DRBGState


@dataclass
class PQCCompositeDRBG:
    """
    Je construis ici un gestionnaire de moteurs post-quantiques.

    Philosophie :
    - Module-LWR est le moteur nominal.
    - Multiplexed Sponge est optionnel et secondaire.
    - en cas d'échec de sécurité, je peux entrer en FAIL_STOP selon la politique.
    """

    lwr_engine: ModuleLWRCore = field(default_factory=ModuleLWRCore)
    sponge_engine: Optional[MultiplexedSpongeAdapter] = None
    policy: DRBGPolicy = field(default_factory=DRBGPolicy)
    state: DRBGState = field(default_factory=DRBGState)

    def _select_engine_for_instantiate(self) -> DRBGEngine:
        if self.policy.selection_mode == EngineSelectionMode.FORCE_SPONGE_RESEARCH:
            if self.sponge_engine is None:
                raise DRBGError("Le mode FORCE_SPONGE_RESEARCH exige un moteur sponge.")
            return self.sponge_engine
        return self.lwr_engine

    def _ensure_not_fail_stop(self) -> None:
        if self.state.flags.fail_stop:
            raise FailStopError(
                "Le système est verrouillé en FAIL_STOP jusqu'à une réinitialisation explicite."
            )

    def instantiate(
        self,
        seed_material: bytes,
        personalization: bytes = b"",
    ) -> None:
        """
        J'initialise ici le moteur selon la politique choisie.
        """
        self._ensure_not_fail_stop()
        engine = self._select_engine_for_instantiate()
        engine.instantiate(seed_material, personalization=personalization)
        self.state.active_engine = engine.name
        self.state.initialized = True
        self.state.request_counter = 0
        self.state.generated_bytes_since_reseed = 0
        self.state.last_reseed_reason = "instantiate"
        self.state.flags.reseed_required = False

    def _active_engine(self) -> DRBGEngine:
        if not self.state.initialized or self.state.active_engine is None:
            raise DRBGError("Le DRBG composite n'est pas initialisé.")

        if self.state.active_engine == self.lwr_engine.name:
            return self.lwr_engine

        if self.sponge_engine is not None and self.state.active_engine == self.sponge_engine.name:
            return self.sponge_engine

        raise DRBGError("Le moteur actif déclaré n'est pas disponible.")

    def _check_reseed_policy(self) -> None:
        if self.state.request_counter >= self.policy.reseed_interval_requests:
            self.state.flags.reseed_required = True

        if self.policy.prediction_resistance:
            self.state.flags.reseed_required = True

        if self.state.flags.reseed_required:
            raise ReseedRequiredError(
                "Un reseed est requis avant toute nouvelle génération."
            )

    def _can_switch_to_sponge_after_exception(self, exc: Exception) -> bool:
        """
        Je décide ici si une bascule contrôlée vers le moteur sponge est autorisée.

        Règle :
        - uniquement en mode expérimental ;
        - uniquement si un moteur sponge est disponible ;
        - uniquement pour une indisponibilité technique ;
        - jamais pour masquer une erreur de sécurité ou un FAIL_STOP.
        """
        if self.policy.selection_mode != EngineSelectionMode.ALLOW_EXPERIMENTAL_SPONGE_FALLBACK:
            return False

        if self.sponge_engine is None:
            return False

        if not self.policy.allow_fallback_on_unavailability_only:
            return False

        # Je refuse toute bascule si l'erreur appartient déjà à ma logique de sécurité.
        if isinstance(exc, (FailStopError, ReseedRequiredError, DRBGError)):
            return False

        return True

    def _switch_to_sponge_engine(self) -> None:
        """
        Je bascule ici explicitement vers le moteur sponge.

        Si le moteur sponge n'est pas encore initialisé, je refuse la bascule.
        """
        if self.sponge_engine is None:
            raise DRBGError("Aucun moteur sponge n'est disponible pour la bascule.")

        sponge_health = self.sponge_engine.health()
        if not sponge_health.healthy:
            raise DRBGError(
                f"Le moteur sponge n'est pas prêt pour la bascule : {sponge_health.reason}"
            )

        self.state.active_engine = self.sponge_engine.name

    def generate(
        self,
        nbytes: int,
        additional_input: bytes = b"",
    ) -> bytes:
        """
        Je produis ici des octets pseudo-aléatoires selon le moteur actif.

        Règle forte :
        - si un contrôle de sécurité impose FAIL_STOP, je verrouille ;
        - je n'utilise pas la bascule pour masquer un problème de sécurité ;
        - la bascule n'est autorisée que pour une indisponibilité technique
          en mode expérimental.
        """
        self._ensure_not_fail_stop()
        self._check_reseed_policy()

        engine = self._active_engine()
        health = engine.health()

        if not health.healthy:
            if self.policy.fail_stop_on_health_error:
                self.state.flags.fail_stop = True
                raise FailStopError(
                    f"Échec santé du moteur actif ({health.engine_name}) : {health.reason}"
                )
            raise DRBGError(f"Moteur non sain : {health.reason}")

        try:
            out = engine.generate(nbytes, additional_input=additional_input)

        except (FailStopError, ReseedRequiredError, DRBGError):
            # Je ne masque jamais ces erreurs.
            raise

        except Exception as exc:
            if self._can_switch_to_sponge_after_exception(exc):
                self._switch_to_sponge_engine()
                fallback_engine = self._active_engine()
                out = fallback_engine.generate(nbytes, additional_input=additional_input)
            else:
                raise

        self.state.request_counter += 1
        self.state.generated_bytes_since_reseed += len(out)
        return out

    def reseed(
        self,
        seed_material: bytes,
        additional_input: bytes = b"",
        reason: str = "manual_reseed",
    ) -> None:
        """
        Je rafraîchis ici le moteur actif.
        """
        self._ensure_not_fail_stop()
        engine = self._active_engine()
        engine.reseed(seed_material, additional_input=additional_input)
        self.state.request_counter = 0
        self.state.generated_bytes_since_reseed = 0
        self.state.last_reseed_reason = reason
        self.state.flags.reseed_required = False

    def force_engine(self, engine_name: str) -> None:
        """
        Je permets ici de forcer explicitement le moteur actif dans un cadre
        de test ou de recherche.
        """
        if engine_name == self.lwr_engine.name:
            self.state.active_engine = self.lwr_engine.name
            return

        if self.sponge_engine is not None and engine_name == self.sponge_engine.name:
            self.state.active_engine = self.sponge_engine.name
            return

        raise DRBGError(f"Moteur inconnu : {engine_name}")

    def export_state(self) -> Dict[str, object]:
        """
        J'exporte ici une vue consolidée du gestionnaire.
        """
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

    def zeroize(self) -> None:
        """
        J'efface ici au maximum tous les états des moteurs et du gestionnaire.
        """
        self.lwr_engine.zeroize()
        if self.sponge_engine is not None:
            self.sponge_engine.zeroize()

        self.state = DRBGState()