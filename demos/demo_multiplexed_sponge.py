from __future__ import annotations

import sys
from hashlib import shake_256
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT_STR = str(PROJECT_ROOT)
if PROJECT_ROOT_STR not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_STR)

from demos.common import format_int_list, join_sections, section
from software.lfsr import RecurrenceSequence
from software.sponge import MultiplexedSequence, derive_sponge_lfsr_seeds
from software.sponge.phi_function import PhiFunction
from software.pqc_drbg.sponge_core import build_reference_sponge


def render_multiplexed_sponge_demo() -> str:
    seedinit = b"demo-multiplexed-sponge-seed"
    seed_digest = shake_256(b"sponge_init:" + seedinit).digest(64)
    derived = derive_sponge_lfsr_seeds(
        seed_digest,
        degree_s=16,
        degree_t=16,
        context=b"build_reference_sponge",
    )

    seq_s_preview = RecurrenceSequence(degree=16, seed=derived.seed_s)
    seq_t_preview = RecurrenceSequence(degree=16, seed=derived.seed_t)
    s_sample = seq_s_preview.peek_bits(12)
    t_sample = seq_t_preview.peek_bits(12)

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
    mux_sample = mux.generate_bits(16)

    sponge = build_reference_sponge(seed_digest)
    squeeze_trace: list[str] = []
    for index in range(4):
        before = sponge.state.get_state()
        block = sponge.squeezer.squeeze_block(8)
        after = sponge.state.get_state()
        squeeze_trace.append(
            f"Etape {index}: state_avant=0x{before:064x} bloc=0x{block:02x} state_apres=0x{after:064x}"
        )

    return join_sections(
        section(
            "DERIVATION LFSR",
            [
                f"Seed digest prefixe: {seed_digest[:8].hex()}",
                f"seed_s: {derived.seed_s}",
                f"seed_t: {derived.seed_t}",
            ],
        ),
        section("SEQUENCE S_n", [format_int_list(s_sample)]),
        section("SEQUENCE T_n", [format_int_list(t_sample)]),
        section("PHI(l,n)", [format_int_list(phi_values)]),
        section("SEQUENCE MULTIPLEXEE", [format_int_list(mux_sample)]),
        section("TRACE SPONGE", squeeze_trace),
    )


if __name__ == "__main__":
    print(render_multiplexed_sponge_demo())
