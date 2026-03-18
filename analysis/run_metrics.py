"""Je decris ici les runs observes dans une sequence binaire finie."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence


def extract_runs(bits: Sequence[int]) -> list[dict[str, int]]:
    """J'extrais la liste ordonnee des runs dans l'echantillon binaire."""

    sample = [int(bit) for bit in bits]
    if any(bit not in (0, 1) for bit in sample):
        raise ValueError("Je demande une sequence binaire composee uniquement de 0 et de 1.")

    if not sample:
        return []

    runs: list[dict[str, int]] = []
    current_bit = sample[0]
    current_length = 1

    for bit in sample[1:]:
        if bit == current_bit:
            current_length += 1
            continue

        runs.append({"bit": current_bit, "length": current_length})
        current_bit = bit
        current_length = 1

    runs.append({"bit": current_bit, "length": current_length})
    return runs


def compute_run_metrics(bits: Sequence[int]) -> dict[str, object]:
    """Je resume ici les runs pour obtenir une vue exploitable dans mon memoire.

    J'utilise cette mesure pour regarder l'alternance des 0 et des 1, ainsi
    que la repartition empirique des longueurs de runs.
    """

    runs = extract_runs(bits)
    if not runs:
        return {
            "total_runs": 0,
            "longest_run": 0,
            "mean_run_length": 0.0,
            "run_counts_by_length": {},
            "run_counts_by_bit": {"0": 0, "1": 0},
        }

    total_runs = len(runs)
    total_bits = sum(run["length"] for run in runs)
    longest_run = max(run["length"] for run in runs)
    counts_by_length = Counter(run["length"] for run in runs)
    counts_by_bit = Counter(str(run["bit"]) for run in runs)

    return {
        "total_runs": total_runs,
        "longest_run": longest_run,
        "mean_run_length": total_bits / total_runs,
        "run_counts_by_length": dict(sorted(counts_by_length.items())),
        "run_counts_by_bit": {
            "0": counts_by_bit.get("0", 0),
            "1": counts_by_bit.get("1", 0),
        },
        "runs": runs,
    }
