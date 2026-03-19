from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from hashlib import shake_256

"""J'adapte ici le Multiplexed Sponge existant à l'interface DRBG."""

from .errors import DRBGError
from .interfaces import DRBGEngine, EngineHealth, StateExport


@dataclass(slots=True)
class MultiplexedSpongeAdapter(DRBGEngine):
    """
    J'encapsule ici le sponge comme moteur secondaire de recherche.

    Je refuse d'en faire un remplacement silencieux du moteur nominal.
    Je le traite comme un adaptateur explicite vers le contrat DRBG.
    """

    sponge_factory: Callable[[bytes], object]

    def __post_init__(self) -> None:
        if not callable(self.sponge_factory):
            raise DRBGError("sponge_factory doit être appelable.")
        self._instance: object | None = None
        self._initialized = False
        self._seed_digest = b""
        self._generate_counter = 0

    @property
    def name(self) -> str:
        """Je retourne ici le nom stable du moteur secondaire."""

        return "multiplexed_sponge"

    def _require_non_empty_seed(self, seed_material: bytes) -> None:
        """Je refuse ici une seed vide pour rester cohérent avec le moteur LWR."""

        if not seed_material:
            raise DRBGError("seed_material ne doit pas être vide.")

    def _require_initialized(self) -> None:
        """Je vérifie ici que l'adaptateur dispose d'une instance sponge valide."""

        if not self._initialized or self._instance is None:
            raise DRBGError("Le moteur Multiplexed Sponge n'est pas initialisé.")

    def _require_nbytes(self, nbytes: int) -> None:
        """Je vérifie ici la taille de sortie demandée."""

        if nbytes < 0:
            raise ValueError("nbytes doit être >= 0.")

    def _build_instance_from_digest(self, seed_digest: bytes) -> object:
        """Je construis ici l'instance sponge à partir d'un digest interne."""

        instance = self.sponge_factory(seed_digest)
        if not hasattr(instance, "squeeze_bytes"):
            raise DRBGError(
                "L'instance sponge fournie par sponge_factory ne supporte pas squeeze_bytes."
            )
        return instance

    def _rekey(self, seed_material: bytes, *, domain: bytes, context: bytes = b"") -> None:
        """Je redérive ici l'état du moteur sponge de manière explicite et déterministe."""

        self._seed_digest = shake_256(domain + self._seed_digest + seed_material + context).digest(64)
        self._instance = self._build_instance_from_digest(self._seed_digest)
        self._generate_counter = 0
        self._initialized = True

    def instantiate(self, seed_material: bytes, personalization: bytes = b"") -> None:
        """J'initialise ici l'adaptateur sponge à partir d'une seed compacte."""

        self._require_non_empty_seed(seed_material)
        self._seed_digest = shake_256(b"sponge_init:" + personalization + seed_material).digest(64)
        self._instance = self._build_instance_from_digest(self._seed_digest)
        self._generate_counter = 0
        self._initialized = True

    def reseed(self, seed_material: bytes, additional_input: bytes = b"") -> None:
        """Je mélange ici une nouvelle seed dans l'adaptateur sponge."""

        self._require_initialized()
        self._require_non_empty_seed(seed_material)
        self._rekey(seed_material, domain=b"sponge_reseed:", context=additional_input)

    def generate(self, nbytes: int, additional_input: bytes = b"") -> bytes:
        """
        Je génère ici la sortie du moteur secondaire.

        Si `additional_input` est fourni, je le transforme d'abord en rekey
        explicite du moteur pour éviter une ambiguïté de comportement.
        """

        self._require_initialized()
        self._require_nbytes(nbytes)
        if additional_input:
            self._rekey(additional_input, domain=b"sponge_generate_mix:", context=self._generate_counter.to_bytes(8, "big"))
        out = self._instance.squeeze_bytes(nbytes)
        self._generate_counter += 1
        return out

    def export_state(self) -> StateExport:
        """J'exporte ici un état non sensible de l'adaptateur sponge."""

        return {
            "name": self.name,
            "initialized": self._initialized,
            "has_instance": self._instance is not None,
            "generate_counter": self._generate_counter,
            "seed_digest_prefix": self._seed_digest[:8].hex() if self._seed_digest else "",
        }

    def zeroize(self) -> None:
        """Je détruis ici l'état logique du moteur secondaire."""

        self._instance = None
        self._initialized = False
        self._seed_digest = b""
        self._generate_counter = 0

    def health(self) -> EngineHealth:
        """Je fournis ici un contrôle de santé logique de l'adaptateur sponge."""

        healthy = self._initialized and self._instance is not None and hasattr(self._instance, "squeeze_bytes")
        reason = "" if healthy else "Le moteur sponge n'est pas initialisé correctement."
        return EngineHealth(
            engine_name=self.name,
            healthy=healthy,
            reason=reason,
            details={
                "initialized": self._initialized,
                "has_instance": self._instance is not None,
                "supports_squeeze_bytes": hasattr(self._instance, "squeeze_bytes") if self._instance else False,
                "generate_counter": self._generate_counter,
            },
        )
