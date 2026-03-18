"""Je consolide ici les differentes metriques dans un rapport simple."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .bit_metrics import compute_bit_balance
from .generators import bits_from_iterable, bits_from_object, bits_from_sponge
from .golomb_checks import compute_golomb_indicators
from .linear_complexity import berlekamp_massey_linear_complexity
from .period_metrics import estimate_observed_period
from .run_metrics import compute_run_metrics


def build_bit_sequence_report(bits: Iterable[int], max_period: int | None = None) -> dict[str, object]:
    """Je construis un rapport consolide a partir d'un echantillon de bits deja genere."""

    sample = bits_from_iterable(bits)
    return {
        "sample_length": len(sample),
        "bit_balance": compute_bit_balance(sample),
        "runs": compute_run_metrics(sample),
        "observed_period": estimate_observed_period(sample, max_period=max_period),
        "linear_complexity": berlekamp_massey_linear_complexity(sample),
        "golomb_indicators": compute_golomb_indicators(sample),
    }


def build_generator_report(source: Any, n_bits: int, max_period: int | None = None) -> dict[str, object]:
    """J'utilise cette fonction pour analyser un objet qui expose des bits."""

    sample = bits_from_object(source, n_bits)
    return build_bit_sequence_report(sample, max_period=max_period)


def build_sponge_report(
    sponge: Any,
    n_bits: int,
    absorb_blocks: Iterable[int] | None = None,
    block_size: int | None = None,
    max_period: int | None = None,
) -> dict[str, object]:
    """J'utilise cette fonction pour produire un rapport simple sur un sponge.

    Si je fournis des blocs a absorber, je les injecte avant de mesurer la
    sequence de sortie. Je garde ce flux de travail volontairement simple pour
    rester au niveau du prototype experimental.
    """

    if absorb_blocks is not None:
        if block_size is None:
            raise ValueError("Je dois connaitre block_size si je fournis absorb_blocks.")
        sponge.absorb_blocks(absorb_blocks, block_size=block_size)

    sample = bits_from_sponge(sponge, n_bits)
    report = build_bit_sequence_report(sample, max_period=max_period)
    report["source"] = "multiplexed_sponge"
    return report
