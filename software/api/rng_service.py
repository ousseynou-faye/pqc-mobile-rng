from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from software.conditioner import ConditioningResult, EntropyMixer
from software.entropy import CPUJitterSource, EntropyPool, SensorEntropySource
from software.lfsr import RecurrenceSequence
from software.pqc_drbg import DRBGPolicy, EngineSelectionMode, PQCCompositeDRBG
from software.pqc_drbg.sponge_core import MultiplexedSpongeAdapter
from software.sponge import MultiplexedSponge
from software.state_manager import SealedBlob, SimulatedTEE, StateManager


class RNGServiceError(RuntimeError):
    """Erreur de coordination du chemin canonique RNG."""


@dataclass(slots=True)
class EntropySourceConfig:
    cpu_sample_count: int = 512
    cpu_inner_loops: int = 256
    cpu_lsb_count: int = 2
    cpu_warmup_rounds: int = 32
    sensor_frame_count: int = 128
    sensor_lsb_count: int = 2
    pool_target_min_entropy_bits: float = 256.0
    pool_target_min_symbols: int = 512
    pool_reject_on_fail: bool = True


@dataclass(slots=True)
class ConditionerConfig:
    toeplitz_output_bits: int = 256
    shake_output_bytes: int = 32
    personalization: bytes = b""
    extra_context: bytes = b""
    toeplitz_public_seed: bytes | None = None


@dataclass(slots=True)
class DRBGConfig:
    personalization: bytes = b""
    policy: DRBGPolicy = field(
        default_factory=lambda: DRBGPolicy(
            selection_mode=EngineSelectionMode.STRICT_LWR_ONLY,
        )
    )


@dataclass(slots=True)
class StateConfig:
    root_dir: str | Path = "state_data"
    device_id: str = "dev-001"
    namespace: str = "pqc_rng"
    blob_id: str = "drbg_state"
    checkpoint_metadata: dict[str, Any] = field(
        default_factory=lambda: {"purpose": "rng_service_checkpoint"}
    )


@dataclass(slots=True)
class RNGServiceConfig:
    profile: str = "baseline"
    entropy: EntropySourceConfig = field(default_factory=EntropySourceConfig)
    conditioner: ConditionerConfig = field(default_factory=ConditionerConfig)
    drbg: DRBGConfig = field(default_factory=DRBGConfig)
    state: StateConfig = field(default_factory=StateConfig)


def _build_research_sponge(seed_digest: bytes) -> MultiplexedSponge:
    """Construit le moteur sponge secondaire sans l'activer dans le flux nominal."""

    seed_s = (int.from_bytes(seed_digest[:2], "big") % ((1 << 16) - 1)) + 1
    seed_t = (int.from_bytes(seed_digest[2:4], "big") % ((1 << 16) - 1)) + 1

    seq_s = RecurrenceSequence(degree=16, seed=seed_s)
    seq_t = RecurrenceSequence(degree=16, seed=seed_t)
    sponge = MultiplexedSponge(seq_s=seq_s, seq_t=seq_t, l=4, rate=128, capacity=128)

    material = hashlib.shake_256(b"rng-service-sponge:" + seed_digest).digest(32)
    blocks = [int.from_bytes(material[index:index + 8], "big") for index in range(0, 32, 8)]
    sponge.absorb_blocks(blocks, block_size=64)
    return sponge


@dataclass
class RNGService:
    """Orchestration canonique officielle : SRC -> COND -> DRBG -> STATE."""

    config: RNGServiceConfig = field(default_factory=RNGServiceConfig)

    def __post_init__(self) -> None:
        self._last_pool: EntropyPool | None = None
        self._last_conditioning: ConditioningResult | None = None
        self._drbg: PQCCompositeDRBG | None = None
        self._state_manager: StateManager | None = None
        self._last_operation: str | None = None

    def _build_entropy_pool(self) -> EntropyPool:
        entropy_config = self.config.entropy
        pool = EntropyPool(
            target_min_entropy_bits=entropy_config.pool_target_min_entropy_bits,
            target_min_symbols=entropy_config.pool_target_min_symbols,
            reject_on_fail=entropy_config.pool_reject_on_fail,
        )

        cpu_chunk = CPUJitterSource(
            sample_count=entropy_config.cpu_sample_count,
            inner_loops=entropy_config.cpu_inner_loops,
            lsb_count=entropy_config.cpu_lsb_count,
            warmup_rounds=entropy_config.cpu_warmup_rounds,
        ).collect()
        pool.add_chunk(cpu_chunk)

        sensor_chunk = SensorEntropySource(
            frame_count=entropy_config.sensor_frame_count,
            lsb_count=entropy_config.sensor_lsb_count,
        ).collect()
        pool.add_chunk(sensor_chunk)
        return pool

    def _build_conditioner(self) -> EntropyMixer:
        conditioner_config = self.config.conditioner
        return EntropyMixer(
            toeplitz_output_bits=conditioner_config.toeplitz_output_bits,
            shake_output_bytes=conditioner_config.shake_output_bytes,
        )

    def _build_drbg(self) -> PQCCompositeDRBG:
        return PQCCompositeDRBG(
            sponge_engine=MultiplexedSpongeAdapter(sponge_factory=_build_research_sponge),
            policy=self.config.drbg.policy,
        )

    def _build_state_manager(self) -> StateManager:
        state_config = self.config.state
        tee = SimulatedTEE(
            root_dir=state_config.root_dir,
            device_id=state_config.device_id,
            namespace=state_config.namespace,
        )
        return StateManager(tee=tee, blob_id=state_config.blob_id)

    @property
    def drbg(self) -> PQCCompositeDRBG | None:
        return self._drbg

    @property
    def last_conditioning(self) -> ConditioningResult | None:
        return self._last_conditioning

    @property
    def last_operation(self) -> str | None:
        return self._last_operation

    @property
    def profile(self) -> str:
        return self.config.profile

    def build_entropy_seed(self) -> ConditioningResult:
        """Construit `Seedinit` via les briques SRC et COND existantes."""

        pool = self._build_entropy_pool()
        raw_data = pool.export_raw_bytes()
        if not raw_data:
            raise RNGServiceError("La construction de seed a echoue : aucun octet brut accepte.")

        conditioner = self._build_conditioner()
        conditioner_config = self.config.conditioner
        result = conditioner.condition_from_pool(
            pool,
            personalization=conditioner_config.personalization,
            extra_context=conditioner_config.extra_context,
            toeplitz_public_seed=conditioner_config.toeplitz_public_seed,
        )

        self._last_pool = pool
        self._last_conditioning = result
        self._last_operation = "build_entropy_seed"
        return result

    def instantiate_rng(
        self,
        *,
        personalization: bytes | None = None,
        seed_result: ConditioningResult | None = None,
    ) -> PQCCompositeDRBG:
        """Initialise le DRBG officiel a partir de la seed conditionnee."""

        result = seed_result or self._last_conditioning or self.build_entropy_seed()
        drbg = self._build_drbg()
        drbg.instantiate(
            result.seedinit,
            personalization=self.config.drbg.personalization if personalization is None else personalization,
        )
        self._drbg = drbg
        self._last_operation = "instantiate_rng"
        return drbg

    def generate_bytes(self, length: int, additional_input: bytes = b"") -> bytes:
        """Produit des octets via le chemin officiel apres instanciation."""

        if self._drbg is None:
            raise RNGServiceError(
                "generate_bytes() exige un RNG instantie. Appelez instantiate_rng() avant toute generation."
            )
        output = self._drbg.generate(length, additional_input=additional_input)
        self._last_operation = "generate_bytes"
        return output

    def reseed_rng(self, *, additional_input: bytes = b"") -> ConditioningResult:
        """Reconstruit une seed fraiche et reseed le moteur courant."""

        if self._drbg is None:
            raise RNGServiceError(
                "reseed_rng() exige un RNG instantie. Appelez instantiate_rng() avant le reseed."
            )
        result = self.build_entropy_seed()
        self._drbg.reseed(result.seedinit, additional_input=additional_input, reason="rng_service_reseed")
        self._last_operation = "reseed_rng"
        return result

    def checkpoint_state(self, *, payload_metadata: dict[str, Any] | None = None) -> SealedBlob:
        """Scelle l'etat courant via la couche STATE existante."""

        if self._drbg is None:
            raise RNGServiceError(
                "checkpoint_state() exige un RNG instantie. Appelez instantiate_rng() ou restore_state() d'abord."
            )
        manager = self._state_manager or self._build_state_manager()
        metadata = payload_metadata or self.config.state.checkpoint_metadata
        blob = manager.checkpoint_drbg(self._drbg, payload_metadata=metadata)
        self._state_manager = manager
        self._last_operation = "checkpoint_state"
        return blob

    def restore_state(self, *, payload_metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        """Restaure un etat DRBG scelle et rebranche le service dessus."""

        try:
            manager = self._state_manager or self._build_state_manager()
            drbg = self._build_drbg()
            metadata = payload_metadata or self.config.state.checkpoint_metadata
            payload = manager.restore_drbg(drbg, payload_metadata=metadata)
        except Exception as exc:
            raise RNGServiceError(f"La restauration de l'etat a echoue : {exc}") from exc

        self._state_manager = manager
        self._drbg = drbg
        self._last_operation = "restore_state"
        return payload

    def has_checkpoint_state(self) -> bool:
        """Indique si un blob d'etat scelle est disponible pour restauration."""

        manager = self._state_manager or self._build_state_manager()
        return manager.tee._blob_path(manager.blob_id).exists()

    def zeroize(self) -> None:
        """Efface l'etat en memoire maintenu par le service canonique."""

        if self._drbg is not None:
            self._drbg.zeroize()
        self._drbg = None
        self._last_pool = None
        self._last_conditioning = None
        self._last_operation = "zeroize"

    def sdk_status(self) -> dict[str, Any]:
        """Expose un resume public sur pour la couche SDK."""

        state_available = False
        try:
            state_available = self.has_checkpoint_state()
        except Exception:
            state_available = False

        lifecycle_state = None
        health_status = "warning"
        if self._drbg is not None:
            exported = self._drbg.export_state()
            manager_state = exported.get("manager_state", {})
            if isinstance(manager_state, dict):
                lifecycle_state = manager_state.get("lifecycle_state")
                if lifecycle_state == "ready":
                    health_status = "ok"
                elif lifecycle_state == "need_reseed":
                    health_status = "warning"
                else:
                    health_status = "error"

        return {
            "initialized": self._drbg is not None,
            "instantiated": self._drbg is not None,
            "state_available": state_available,
            "reseed_supported": self._drbg is not None,
            "last_operation": self._last_operation,
            "profile": self.profile,
            "health_status": health_status,
            "lifecycle_state": lifecycle_state,
        }

    def health_status(self) -> dict[str, Any]:
        """Expose un etat synthetique pour les wrappers internes et les tests."""

        return {
            "instantiated": self._drbg is not None,
            "seed_built": self._last_conditioning is not None,
            "entropy_pool": self._last_pool.export_metadata() if self._last_pool is not None else None,
            "conditioning": (
                {
                    "input_bits": self._last_conditioning.input_bits,
                    "output_bits": self._last_conditioning.output_bits,
                    "seed_length_bytes": len(self._last_conditioning.seedinit),
                }
                if self._last_conditioning is not None
                else None
            ),
            "drbg_state": self._drbg.export_state() if self._drbg is not None else None,
        }
