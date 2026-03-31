from __future__ import annotations

import sys
from hashlib import shake_256
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT_STR = str(PROJECT_ROOT)
if PROJECT_ROOT_STR not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_STR)

from demos.common import format_int_list, join_sections, section
from software.api.rng_service import RNGService, RNGServiceConfig, StateConfig
from software.conditioner import EntropyMixer
from software.entropy import CPUJitterSource, EntropyPool, SensorEntropySource
from software.lfsr import RecurrenceSequence
from software.sponge import MultiplexedSequence, derive_sponge_lfsr_seeds
from software.sponge.phi_function import PhiFunction
from software.pqc_drbg.sponge_core import build_reference_sponge


def _build_runtime_service() -> RNGService:
    return RNGService(
        config=RNGServiceConfig(
            state=StateConfig(
                root_dir=Path("demos/.runtime/full_pipeline"),
                device_id="demo-full-pipeline-device",
                namespace="demo-full-pipeline",
                blob_id="demo-full-pipeline-blob",
                checkpoint_metadata={"purpose": "demo_full_pipeline"},
            )
        )
    )


def render_full_pipeline_demo(output_bytes: int = 24) -> str:
    service = _build_runtime_service()
    entropy_cfg = service.config.entropy
    conditioner_cfg = service.config.conditioner

    cpu_chunk = CPUJitterSource(
        sample_count=entropy_cfg.cpu_sample_count,
        inner_loops=entropy_cfg.cpu_inner_loops,
        lsb_count=entropy_cfg.cpu_lsb_count,
        warmup_rounds=entropy_cfg.cpu_warmup_rounds,
    ).collect()
    sensor_chunk = SensorEntropySource(
        frame_count=entropy_cfg.sensor_frame_count,
        lsb_count=entropy_cfg.sensor_lsb_count,
    ).collect()

    pool = EntropyPool(
        target_min_entropy_bits=entropy_cfg.pool_target_min_entropy_bits,
        target_min_symbols=entropy_cfg.pool_target_min_symbols,
        reject_on_fail=entropy_cfg.pool_reject_on_fail,
    )
    pool.add_chunk(cpu_chunk)
    pool.add_chunk(sensor_chunk)

    conditioner = EntropyMixer(
        toeplitz_output_bits=conditioner_cfg.toeplitz_output_bits,
        shake_output_bytes=conditioner_cfg.shake_output_bytes,
    )
    conditioning = conditioner.condition_from_pool(
        pool,
        personalization=conditioner_cfg.personalization,
        extra_context=conditioner_cfg.extra_context,
        toeplitz_public_seed=conditioner_cfg.toeplitz_public_seed,
    )

    seed_digest = shake_256(b"sponge_init:" + conditioning.seedinit).digest(64)
    derived = derive_sponge_lfsr_seeds(
        seed_digest,
        degree_s=16,
        degree_t=16,
        context=b"build_reference_sponge",
    )

    s_preview = RecurrenceSequence(degree=16, seed=derived.seed_s)
    t_preview = RecurrenceSequence(degree=16, seed=derived.seed_t)
    s_sample = s_preview.peek_bits(12)
    t_sample = t_preview.peek_bits(12)

    phi_sequence = RecurrenceSequence(degree=16, seed=derived.seed_s)
    phi = PhiFunction(sequence_s=phi_sequence, l=4)
    phi_values: list[int] = []
    for _ in range(8):
        phi_values.append(phi.compute())
        phi_sequence.advance(1)

    mux = MultiplexedSequence(
        seq_s=RecurrenceSequence(degree=16, seed=derived.seed_s),
        seq_t=RecurrenceSequence(degree=16, seed=derived.seed_t),
        l=4,
    )
    multiplexed_sample = mux.generate_bits(16)

    sponge = build_reference_sponge(seed_digest)
    sponge_trace: list[str] = []
    for index in range(4):
        before = sponge.state.get_state()
        block = sponge.squeezer.squeeze_block(8)
        after = sponge.state.get_state()
        sponge_trace.append(
            f"Etape {index}: state_avant=0x{before:064x} bloc=0x{block:02x} state_apres=0x{after:064x}"
        )

    service.instantiate_rng(seed_result=conditioning)
    final_bundle = service.generate_output_bundle(output_bytes, additional_input=b"demo-full-pipeline")

    return join_sections(
        section(
            "SOURCE D'ENTROPIE",
            [
                f"CPU jitter octets bruts: {repr(cpu_chunk.raw_bytes[:16])}",
                f"CPU jitter metadata: {cpu_chunk.metadata}",
                f"Source capteur octets bruts: {repr(sensor_chunk.raw_bytes[:16])}",
                f"Source capteur metadata: {sensor_chunk.metadata}",
                f"Pool brut (prefixe hex): {pool.export_raw_bytes()[:16].hex()}",
                f"Pool metadata: {pool.export_metadata()}",
            ],
        ),
        section(
            "CONDITIONNEUR",
            [
                f"Input bits: {conditioning.input_bits}",
                f"Toeplitz seed prefixe: {conditioning.toeplitz_seed[:16].hex()}",
                f"Toeplitz output hex: {conditioning.toeplitz_output.hex()}",
                f"Context info: {conditioning.context_info.decode('utf-8', errors='replace')}",
            ],
        ),
        section(
            "SEEDINIT",
            [
                f"Seedinit bytes: {repr(conditioning.seedinit)}",
                f"Seedinit hex: {conditioning.seedinit.hex()}",
                f"Seed digest prefixe: {seed_digest[:16].hex()}",
            ],
        ),
        section(
            "DERIVATION LFSR",
            [
                f"seed_s: {derived.seed_s}",
                f"seed_t: {derived.seed_t}",
            ],
        ),
        section("SEQUENCE S_n", [format_int_list(s_sample)]),
        section("SEQUENCE T_n", [format_int_list(t_sample)]),
        section("PHI(l,n)", [format_int_list(phi_values)]),
        section("SEQUENCE MULTIPLEXEE", [format_int_list(multiplexed_sample)]),
        section("MULTIPLEXED SPONGE", sponge_trace),
        section(
            "SORTIE FINALE",
            [
                f"Bytes: {final_bundle['raw_bytes_repr']}",
                f"Hex: {final_bundle['hex']}",
                f"Decimal: {final_bundle['decimal']}",
                f"Binary: {final_bundle['binary']}",
                f"Binary groupe: {final_bundle['binary_grouped']}",
                f"Longueur: {final_bundle['length_bytes']} octets / {final_bundle['length_bits']} bits",
            ],
        ),
    )


if __name__ == "__main__":
    print(render_full_pipeline_demo())
