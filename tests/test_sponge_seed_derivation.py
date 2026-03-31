from __future__ import annotations

from hashlib import shake_256
from pathlib import Path
from uuid import uuid4

from software.conditioner import encode_conditioner_seed_for_drbg
from software.api.rng_service import RNGService, RNGServiceConfig, StateConfig
from software.lfsr.recurrence_sequences import RecurrenceSequence
from software.pqc_drbg.sponge_core import build_reference_sponge
from software.sponge.multiplexed_sponge import MultiplexedSponge
from software.sponge.seed_derivation import derive_sponge_lfsr_seeds


def _build_runtime_dir(name: str) -> Path:
    root = Path("tests_runtime") / "sponge_seed_derivation" / f"{name}_{uuid4().hex[:8]}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _build_service(root_dir: Path) -> RNGService:
    return RNGService(
        config=RNGServiceConfig(
            state=StateConfig(
                root_dir=root_dir,
                device_id="seed-bridge-device",
                namespace="seed-bridge-namespace",
                blob_id="seed-bridge-blob",
            )
        )
    )


def _build_expected_reference_sponge(seed_digest: bytes) -> MultiplexedSponge:
    derived = derive_sponge_lfsr_seeds(
        seed_digest,
        degree_s=16,
        degree_t=16,
        context=b"build_reference_sponge",
    )
    sponge = MultiplexedSponge(
        seq_s=RecurrenceSequence(degree=16, seed=derived.seed_s),
        seq_t=RecurrenceSequence(degree=16, seed=derived.seed_t),
        l=4,
        rate=128,
        capacity=128,
    )
    material = shake_256(b"rng-service-sponge:" + seed_digest).digest(32)
    blocks = [int.from_bytes(material[index:index + 8], "big") for index in range(0, 32, 8)]
    sponge.absorb_blocks(blocks, block_size=64)
    return sponge


def test_seed_derivation_is_deterministic_and_non_zero():
    seedinit = b"conditioned-seed-material-001"

    first = derive_sponge_lfsr_seeds(seedinit, degree_s=16, degree_t=16)
    second = derive_sponge_lfsr_seeds(seedinit, degree_s=16, degree_t=16)

    assert first == second
    assert first.seed_s != 0
    assert first.seed_t != 0


def test_seed_derivation_changes_with_different_seed_material():
    a = derive_sponge_lfsr_seeds(b"conditioned-seed-A", degree_s=16, degree_t=16)
    b = derive_sponge_lfsr_seeds(b"conditioned-seed-B", degree_s=16, degree_t=16)

    assert (a.seed_s, a.seed_t) != (b.seed_s, b.seed_t)


def test_reference_sponge_initial_states_follow_explicit_derivation_bridge():
    seed_digest = shake_256(b"seedinit-for-reference-sponge").digest(64)

    sponge = build_reference_sponge(seed_digest)
    expected = _build_expected_reference_sponge(seed_digest)

    assert sponge.sequence.seq_s.get_state() == expected.sequence.seq_s.get_state()
    assert sponge.sequence.seq_t.get_state() == expected.sequence.seq_t.get_state()


def test_same_seed_material_builds_same_reference_sponge_states():
    seed_digest = shake_256(b"same-seed-material").digest(64)

    first = build_reference_sponge(seed_digest)
    second = build_reference_sponge(seed_digest)

    assert first.sequence.seq_s.get_state() == second.sequence.seq_s.get_state()
    assert first.sequence.seq_t.get_state() == second.sequence.seq_t.get_state()


def test_rng_service_bridges_conditioner_seed_to_sponge_lfsr_states():
    service = _build_service(_build_runtime_dir("rng_service_bridge"))
    conditioning = service.build_entropy_seed()

    drbg = service.instantiate_rng(seed_result=conditioning)
    private_state = drbg.sponge_engine.export_private_state()
    seed_digest = bytes.fromhex(private_state["seed_digest_hex"])
    expected = _build_expected_reference_sponge(seed_digest)

    assert seed_digest == shake_256(
        b"sponge_init:" + conditioning.seedinit
    ).digest(64)
    assert private_state["instance_state"]["seq_s_state"] == expected.sequence.seq_s.get_state()
    assert private_state["instance_state"]["seq_t_state"] == expected.sequence.seq_t.get_state()


def test_drbg_seed_material_encoding_is_deterministic_and_required():
    encoded = encode_conditioner_seed_for_drbg(b"seed-cond-001")
    assert encoded == encode_conditioner_seed_for_drbg(b"seed-cond-001")
    assert encoded != b"seed-cond-001"
