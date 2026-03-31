from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from hashlib import shake_256

from software.conditioner import decode_conditioner_seed_for_drbg
from software.lfsr import RecurrenceSequence
from software.sponge import MultiplexedSponge, derive_sponge_lfsr_seeds

from .errors import DRBGError
from .interfaces import DRBGEngine, EngineHealth, StateExport

"""Adaptateur du moteur Multiplexed Sponge vers le contrat DRBG."""


def build_reference_sponge(seed_digest: bytes) -> MultiplexedSponge:
    """Construit l'implementation sponge de reference du projet.

    `seed_digest` est le materiau canonicalise par la couche DRBG a partir de la
    seed recue de COND (`ConditioningResult.seedinit`). Les etats initiaux des
    deux LFSR sont ensuite derives explicitement avec separation de domaine.
    """

    derived = derive_sponge_lfsr_seeds(
        seed_digest,
        degree_s=16,
        degree_t=16,
        context=b"build_reference_sponge",
    )

    seq_s = RecurrenceSequence(degree=16, seed=derived.seed_s)
    seq_t = RecurrenceSequence(degree=16, seed=derived.seed_t)
    sponge = MultiplexedSponge(seq_s=seq_s, seq_t=seq_t, l=4, rate=128, capacity=128)

    material = shake_256(b"rng-service-sponge:" + seed_digest).digest(32)
    blocks = [int.from_bytes(material[index:index + 8], "big") for index in range(0, 32, 8)]
    sponge.absorb_blocks(blocks, block_size=64)
    return sponge


@dataclass(slots=True)
class MultiplexedSpongeAdapter(DRBGEngine):
    """
    Encapsule Multiplexed Sponge comme moteur nominal du projet.

    L'adaptateur conserve un contrat DRBG stable pour que l'orchestrateur,
    la couche API et la couche STATE partagent la meme frontiere logicielle.
    """

    sponge_factory: Callable[[bytes], object]

    def __post_init__(self) -> None:
        if not callable(self.sponge_factory):
            raise DRBGError("sponge_factory doit etre appelable.")
        self._instance: object | None = None
        self._initialized = False
        self._seed_digest = b""
        self._generate_counter = 0

    @property
    def name(self) -> str:
        return "multiplexed_sponge"

    def _require_non_empty_seed(self, seed_material: bytes) -> None:
        if not seed_material:
            raise DRBGError("seed_material ne doit pas etre vide.")

    def _require_initialized(self) -> None:
        if not self._initialized or self._instance is None:
            raise DRBGError("Le moteur Multiplexed Sponge n'est pas initialise.")

    def _require_nbytes(self, nbytes: int) -> None:
        if nbytes < 0:
            raise ValueError("nbytes doit etre >= 0.")

    def _build_instance_from_digest(self, seed_digest: bytes) -> object:
        instance = self.sponge_factory(seed_digest)
        if not hasattr(instance, "squeeze_bytes"):
            raise DRBGError(
                "L'instance sponge fournie par sponge_factory ne supporte pas squeeze_bytes."
            )
        return instance

    def _rekey(self, seed_material: bytes, *, domain: bytes, context: bytes = b"", require_conditioner_seed: bool = False) -> None:
        try:
            mix_material = (
                decode_conditioner_seed_for_drbg(seed_material)
                if require_conditioner_seed
                else bytes(seed_material)
            )
        except (TypeError, ValueError) as exc:
            raise DRBGError(str(exc)) from exc
        self._seed_digest = shake_256(domain + self._seed_digest + mix_material + context).digest(64)
        self._instance = self._build_instance_from_digest(self._seed_digest)
        self._generate_counter = 0
        self._initialized = True

    def instantiate(self, seed_material: bytes, personalization: bytes = b"") -> None:
        self._require_non_empty_seed(seed_material)
        try:
            conditioner_seed = decode_conditioner_seed_for_drbg(seed_material)
        except (TypeError, ValueError) as exc:
            raise DRBGError(str(exc)) from exc
        self._seed_digest = shake_256(b"sponge_init:" + personalization + conditioner_seed).digest(64)
        self._instance = self._build_instance_from_digest(self._seed_digest)
        self._generate_counter = 0
        self._initialized = True

    def reseed(self, seed_material: bytes, additional_input: bytes = b"") -> None:
        self._require_initialized()
        self._require_non_empty_seed(seed_material)
        self._rekey(
            seed_material,
            domain=b"sponge_reseed:",
            context=additional_input,
            require_conditioner_seed=True,
        )

    def generate(self, nbytes: int, additional_input: bytes = b"") -> bytes:
        self._require_initialized()
        self._require_nbytes(nbytes)
        if additional_input:
            self._rekey(
                additional_input,
                domain=b"sponge_generate_mix:",
                context=self._generate_counter.to_bytes(8, "big"),
                require_conditioner_seed=False,
            )
        out = self._instance.squeeze_bytes(nbytes)
        self._generate_counter += 1
        return out

    def export_state(self) -> StateExport:
        return {
            "name": self.name,
            "initialized": self._initialized,
            "has_instance": self._instance is not None,
            "generate_counter": self._generate_counter,
            "seed_digest_prefix": self._seed_digest[:8].hex() if self._seed_digest else "",
        }

    def _export_instance_state(self) -> dict[str, object] | None:
        if self._instance is None:
            return None

        snapshot: dict[str, object] = {}
        state_obj = getattr(self._instance, "state", None)
        if state_obj is not None and hasattr(state_obj, "get_state"):
            snapshot["sponge_state"] = int(state_obj.get_state())

        sequence = getattr(self._instance, "sequence", None)
        if sequence is not None:
            seq_s = getattr(sequence, "seq_s", None)
            seq_t = getattr(sequence, "seq_t", None)
            if seq_s is not None and hasattr(seq_s, "get_state"):
                snapshot["seq_s_state"] = int(seq_s.get_state())
            if seq_t is not None and hasattr(seq_t, "get_state"):
                snapshot["seq_t_state"] = int(seq_t.get_state())

        return snapshot or None

    def _restore_instance_state(self, instance_state: dict[str, object] | None) -> None:
        if self._instance is None or not instance_state:
            return

        state_obj = getattr(self._instance, "state", None)
        if state_obj is not None and hasattr(state_obj, "set_state") and "sponge_state" in instance_state:
            state_obj.set_state(int(instance_state["sponge_state"]))

        sequence = getattr(self._instance, "sequence", None)
        if sequence is not None:
            seq_s = getattr(sequence, "seq_s", None)
            seq_t = getattr(sequence, "seq_t", None)
            if seq_s is not None and hasattr(seq_s, "reseed") and "seq_s_state" in instance_state:
                seq_s.reseed(int(instance_state["seq_s_state"]))
            if seq_t is not None and hasattr(seq_t, "reseed") and "seq_t_state" in instance_state:
                seq_t.reseed(int(instance_state["seq_t_state"]))

    def export_private_state(self) -> dict[str, object]:
        return {
            "initialized": bool(self._initialized),
            "seed_digest_hex": self._seed_digest.hex(),
            "generate_counter": int(self._generate_counter),
            "instance_state": self._export_instance_state(),
        }

    def import_private_state(self, payload: dict[str, object]) -> None:
        seed_digest_hex = payload.get("seed_digest_hex")
        self._seed_digest = (
            bytes.fromhex(seed_digest_hex)
            if isinstance(seed_digest_hex, str) and seed_digest_hex
            else b""
        )
        self._initialized = bool(payload["initialized"])
        self._generate_counter = int(payload.get("generate_counter", 0))
        if self._initialized:
            self._instance = self._build_instance_from_digest(self._seed_digest)
            instance_state = payload.get("instance_state")
            if isinstance(instance_state, dict):
                self._restore_instance_state(instance_state)
        else:
            self._instance = None

    def zeroize(self) -> None:
        self._instance = None
        self._initialized = False
        self._seed_digest = b""
        self._generate_counter = 0

    def health(self) -> EngineHealth:
        healthy = self._initialized and self._instance is not None and hasattr(self._instance, "squeeze_bytes")
        reason = "" if healthy else "Le moteur sponge n'est pas initialise correctement."
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
