"""Je regroupe ici quelques indicateurs simples inspires des proprietes de Golomb."""

from __future__ import annotations

from collections.abc import Sequence

from .bit_metrics import compute_bit_balance
from .run_metrics import compute_run_metrics


def compute_golomb_indicators(bits: Sequence[int], max_run_length: int = 6) -> dict[str, object]:
    """Je calcule ici quelques indicateurs empiriques inspires des proprietes de Golomb.

    Je reste volontairement prudent :
    - je ne cherche pas a affirmer qu'une sequence satisfait formellement les
      postulats de Golomb ;
    - je produis seulement des indicateurs simples pour guider mon analyse
      experimentale sur une fenetre finie.
    """

    sample = [int(bit) for bit in bits]
    if any(bit not in (0, 1) for bit in sample):
        raise ValueError("Je demande une sequence binaire composee uniquement de 0 et de 1.")

    balance = compute_bit_balance(sample)
    run_metrics = compute_run_metrics(sample)
    total_runs = int(run_metrics["total_runs"])
    run_counts_by_length = run_metrics["run_counts_by_length"]

    empirical_vs_expected: dict[int, dict[str, float | int]] = {}
    for run_length in range(1, max_run_length + 1):
        observed = int(run_counts_by_length.get(run_length, 0))
        expected = total_runs / (2 ** run_length) if total_runs else 0.0
        empirical_vs_expected[run_length] = {
            "observed": observed,
            "expected_approx": expected,
            "difference": observed - expected,
        }

    return {
        "balance_gap": abs(int(balance["count_1"]) - int(balance["count_0"])),
        "run_count_gap": abs(
            int(run_metrics["run_counts_by_bit"]["1"]) - int(run_metrics["run_counts_by_bit"]["0"])
        ),
        "longest_run": run_metrics["longest_run"],
        "empirical_run_profile": empirical_vs_expected,
    }
