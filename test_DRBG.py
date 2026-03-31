from __future__ import annotations

"""Petit script manuel pour verifier le DRBG sponge-only."""

from software.conditioner import encode_conditioner_seed_for_drbg
from software.pqc_drbg.drbg_engine import PQCCompositeDRBG


def run_manual_demo() -> None:
    drbg = PQCCompositeDRBG()
    drbg.instantiate(encode_conditioner_seed_for_drbg(b"manual-demo-seed"))
    print("active_engine:", drbg.export_state()["manager_state"]["active_engine"])
    print("generate(32):", drbg.generate(32).hex())
    drbg.reseed(encode_conditioner_seed_for_drbg(b"manual-demo-reseed"), reason="manual_demo")
    print("generate_after_reseed(32):", drbg.generate(32).hex())


if __name__ == "__main__":
    run_manual_demo()
