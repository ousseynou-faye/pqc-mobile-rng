from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import shake_256

"""J'implémente ici le moteur nominal Module-LWR."""

from .errors import DRBGError
from .interfaces import DRBGEngine, EngineHealth, StateExport
from .lattice_math import (
    apply_lwr_rounding,
    encode_vector,
    matrix_vector_mul,
    sample_ternary_vector,
    seed_to_matrix,
)
from .params import LWRParams, default_lwr_params


@dataclass(slots=True)
class ModuleLWRCore(DRBGEngine):
    """
    Je considère ici Module-LWR comme moteur nominal du système.

    Je garde ce prototype volontairement lisible pour le mémoire :
    - je dérive d'abord les graines internes ;
    - je matérialise ensuite la formule LWR ;
    - je recompresse enfin l'état via SHAKE-256.
    """

    params: LWRParams = field(default_factory=default_lwr_params)

    def __post_init__(self) -> None:
        self.params.validate()
        self._initialized = False
        self._counter = 0
        self._secret_vector: list[list[int]] | None = None
        self._seed_a: bytes | None = None
        self._last_output_digest = b""

    @property
    def name(self) -> str:
        """Je retourne ici le nom stable du moteur nominal."""

        return "module_lwr"

    def _require_non_empty_seed(self, seed_material: bytes) -> None:
        """Je refuse ici une seed vide car elle rendrait l'initialisation ambiguë."""

        if not seed_material:
            raise DRBGError("seed_material ne doit pas être vide.")

    def _require_initialized(self) -> None:
        """Je vérifie ici que l'état interne du moteur est exploitable."""

        if not self._initialized or self._secret_vector is None or self._seed_a is None:
            raise DRBGError("Le moteur Module-LWR n'est pas initialisé.")

    def _require_nbytes(self, nbytes: int) -> None:
        """Je vérifie ici la taille de sortie demandée."""

        if nbytes < 0:
            raise ValueError("nbytes doit être >= 0.")

    def _derive_seed_parts(self, seed_material: bytes, personalization: bytes = b"") -> tuple[bytes, bytes]:
        """Je dérive ici séparément la seed secrète et la seed publique `A`."""

        self._require_non_empty_seed(seed_material)
        digest = shake_256(b"instantiate:" + personalization + seed_material).digest(64)
        return digest[:32], digest[32:]

    def _materialize_public_matrix(self) -> list[list[list[int]]]:
        """Je reconstruis ici la matrice publique `A` à partir de `seed_a`."""

        self._require_initialized()
        return seed_to_matrix(self._seed_a, self.params.k, self.params.n, self.params.q)

    def _materialize_lwr_vector(self) -> list[list[int]]:
        """
        Je calcule ici la formule centrale du prototype LWR.

        Dans cette étape, je produis :
        - `A * s mod q`
        - puis `floor((p / q) * (A * s)) mod p`
        """

        self._require_initialized()
        raw_product = matrix_vector_mul(self._materialize_public_matrix(), self._secret_vector, self.params.q)
        return apply_lwr_rounding(raw_product, self.params.p, self.params.q)

    def _derive_next_state(self, domain: bytes) -> tuple[list[list[int]], bytes]:
        """Je dérive ici l'état suivant à partir de l'image LWR courante."""

        rounded = self._materialize_lwr_vector()
        state_material = encode_vector(rounded, self.params.p)
        digest = shake_256(
            domain + self._seed_a + state_material + self._counter.to_bytes(8, "big")
        ).digest(64)
        new_seed_s = digest[:32]
        new_seed_a = digest[32:]
        new_secret = sample_ternary_vector(
            new_seed_s,
            self.params.k,
            self.params.n,
            self.params.secret_bound,
        )
        return new_secret, new_seed_a

    def _mutate_state(self, domain: bytes = b"update") -> None:
        """Je mets ici à jour l'état interne après une génération ou un reseed."""

        self._require_initialized()
        next_secret, next_seed_a = self._derive_next_state(domain=domain)
        self._secret_vector = next_secret
        self._seed_a = next_seed_a

    def _derive_output_block(self, additional_input: bytes = b"") -> bytes:
        """Je dérive ici un bloc de sortie à partir de l'état secret courant."""

        self._require_initialized()
        state_bytes = encode_vector(self._secret_vector, self.params.q)
        digest = shake_256(
            b"generate:" + self._seed_a + state_bytes + self._counter.to_bytes(8, "big") + additional_input
        ).digest(64)
        self._last_output_digest = digest
        return digest

    def instantiate(self, seed_material: bytes, personalization: bytes = b"") -> None:
        """J'initialise ici complètement l'état interne du moteur nominal."""

        seed_s, seed_a = self._derive_seed_parts(seed_material, personalization)
        self._secret_vector = sample_ternary_vector(
            seed_s,
            self.params.k,
            self.params.n,
            self.params.secret_bound,
        )
        self._seed_a = seed_a
        self._counter = 0
        self._last_output_digest = b""
        self._initialized = True

    def reseed(self, seed_material: bytes, additional_input: bytes = b"") -> None:
        """Je mélange ici une nouvelle seed dans le moteur déjà initialisé."""

        self._require_initialized()
        self._require_non_empty_seed(seed_material)
        mixed_seed = shake_256(
            b"reseed:" + self._seed_a + self._counter.to_bytes(8, "big") + seed_material + additional_input
        ).digest(64)
        self.instantiate(mixed_seed, personalization=b"reseeded")

    def generate(self, nbytes: int, additional_input: bytes = b"") -> bytes:
        """Je génère ici une suite d'octets puis je mute l'état après chaque bloc."""

        self._require_nbytes(nbytes)
        self._require_initialized()
        out = bytearray()
        while len(out) < nbytes:
            block = self._derive_output_block(additional_input=additional_input)
            out.extend(block)
            self._counter += 1
            self._mutate_state(domain=b"update_after_generate:")
        return bytes(out[:nbytes])

    def export_state(self) -> StateExport:
        """J'exporte ici uniquement des informations non sensibles."""

        return {
            "name": self.name,
            "initialized": self._initialized,
            "counter": self._counter,
            "has_seed_a": self._seed_a is not None,
            "has_secret_vector": self._secret_vector is not None,
            "secret_dimension_k": self.params.k,
            "polynomial_degree_n": self.params.n,
            "modulus_q": self.params.q,
            "rounding_modulus_p": self.params.p,
            "rounding_shift": self.params.rounding_shift,
            "last_output_digest_prefix": self._last_output_digest[:8].hex() if self._last_output_digest else "",
        }

    def zeroize(self) -> None:
        """Je détruis ici au mieux l'état sensible maintenu par le prototype."""

        self._secret_vector = None
        self._seed_a = None
        self._counter = 0
        self._last_output_digest = b""
        self._initialized = False

    def health(self) -> EngineHealth:
        """Je fournis ici un contrôle de santé logique très simple du moteur."""

        healthy = self._initialized and self._secret_vector is not None and self._seed_a is not None
        reason = "" if healthy else "Le moteur LWR n'est pas initialisé."
        return EngineHealth(
            engine_name=self.name,
            healthy=healthy,
            reason=reason,
            details={
                "initialized": self._initialized,
                "counter": self._counter,
                "has_seed_a": self._seed_a is not None,
                "has_secret_vector": self._secret_vector is not None,
            },
        )
