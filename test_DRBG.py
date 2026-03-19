from __future__ import annotations

"""
Je lance ici une démonstration pratique de mon DRBG post-quantique.

Dans ce fichier, je veux voir concrètement :
- la génération avec le moteur nominal Module-LWR ;
- la génération avec le moteur secondaire Multiplexed Sponge ;
- la différence entre les deux sorties ;
- une vue simple en bytes et en bits.
"""

from software.lfsr.recurrence_sequences import RecurrenceSequence
from software.pqc_drbg.lwr_core import ModuleLWRCore
from software.pqc_drbg.policy import DRBGPolicy, EngineSelectionMode
from software.pqc_drbg.drbg_engine import PQCCompositeDRBG
from software.pqc_drbg.sponge_core import MultiplexedSpongeAdapter
from software.sponge.multiplexed_sponge import MultiplexedSponge


def bytes_to_bits(data: bytes) -> list[int]:
    """
    Je convertis ici un flux d'octets en liste de bits.
    """
    bits = []
    for byte in data:
        for shift in range(7, -1, -1):
            bits.append((byte >> shift) & 1)
    return bits


def non_zero_seed(value: int, mask: int) -> int:
    """
    Je m'assure ici que le seed n'est jamais nul.
    """
    seed = value & mask
    return seed if seed != 0 else 1


def real_sponge_factory(seed_digest: bytes) -> MultiplexedSponge:
    """
    Je construis ici une vraie instance de mon Multiplexed Sponge
    à partir d'une seed dérivée.
    """
    seed_s = non_zero_seed(int.from_bytes(seed_digest[:2], "big"), (1 << 8) - 1)
    seed_t = non_zero_seed(int.from_bytes(seed_digest[2:4], "big"), (1 << 9) - 1)

    seq_s = RecurrenceSequence(degree=8, seed=seed_s)
    seq_t = RecurrenceSequence(degree=9, seed=seed_t)

    return MultiplexedSponge(
        seq_s=seq_s,
        seq_t=seq_t,
        l=4,
        rate=32,
        capacity=32,
    )


def print_result(title: str, data: bytes) -> None:
    """
    Je présente ici le résultat de génération de manière lisible.
    """
    bits = bytes_to_bits(data)

    print("=" * 70)
    print(title)
    print("-" * 70)
    print("Hex :", data.hex())
    print("Bits:", bits[:64], "..." if len(bits) > 64 else "")
    print("Nombre d'octets :", len(data))
    print("Nombre de bits  :", len(bits))
    print()


def run_lwr_demo() -> None:
    """
    Je teste ici directement le moteur Module-LWR.
    """
    engine = ModuleLWRCore()
    engine.instantiate(b"demo-seed-lwr")

    output = engine.generate(32)
    print_result("DEMO - MODULE LWR", output)


def run_sponge_demo() -> None:
    """
    Je teste ici directement le moteur Multiplexed Sponge via son adaptateur.
    """
    sponge_engine = MultiplexedSpongeAdapter(sponge_factory=real_sponge_factory)
    sponge_engine.instantiate(b"demo-seed-sponge")

    output = sponge_engine.generate(16)
    print_result("DEMO - MULTIPLEXED SPONGE", output)


def run_composite_demo() -> None:
    """
    Je montre ici l'utilisation du gestionnaire composite dans les deux modes.
    """
    sponge_engine = MultiplexedSpongeAdapter(sponge_factory=real_sponge_factory)

    # Cas 1 : moteur nominal LWR
    drbg_lwr = PQCCompositeDRBG(
        sponge_engine=sponge_engine,
        policy=DRBGPolicy(
            selection_mode=EngineSelectionMode.STRICT_LWR_ONLY
        ),
    )
    drbg_lwr.instantiate(b"demo-composite-lwr")
    output_lwr = drbg_lwr.generate(32)
    print_result("COMPOSITE - MODE STRICT LWR", output_lwr)

    # Cas 2 : moteur sponge forcé en mode recherche
    drbg_sponge = PQCCompositeDRBG(
        sponge_engine=MultiplexedSpongeAdapter(sponge_factory=real_sponge_factory),
        policy=DRBGPolicy(
            selection_mode=EngineSelectionMode.FORCE_SPONGE_RESEARCH
        ),
    )
    drbg_sponge.instantiate(b"demo-composite-sponge")
    output_sponge = drbg_sponge.generate(16)
    print_result("COMPOSITE - MODE RECHERCHE SPONGE", output_sponge)


def main() -> None:
    """
    Je lance ici toutes les démonstrations.
    """
    print("\\nDEMONSTRATION PRATIQUE DU DRBG POST-QUANTIQUE\\n")

    run_lwr_demo()
    run_sponge_demo()
    run_composite_demo()


if __name__ == "__main__":
    main()