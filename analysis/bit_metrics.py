"""Je mesure ici la distribution empirique des bits 0 et 1."""

from __future__ import annotations

from collections.abc import Sequence


def compute_bit_balance(bits: Sequence[int]) -> dict[str, float | int]:
    """Je mesure ici la frequence empirique des bits 0 et 1 sur un echantillon donne.

    Cette mesure ne prouve pas la securite du generateur ; elle me permet
    seulement d'evaluer experimentalement l'equilibre binaire de l'echantillon.
    """

    sample = [int(bit) for bit in bits]
    if any(bit not in (0, 1) for bit in sample):
        raise ValueError("Je demande une sequence binaire composee uniquement de 0 et de 1.")

    length = len(sample)
    if length == 0:
        return {
            "length": 0,
            "count_0": 0,
            "count_1": 0,
            "frequency_0": 0.0,
            "frequency_1": 0.0,
            "bias": 0.0,
        }

    count_1 = sum(sample)
    count_0 = length - count_1
    frequency_1 = count_1 / length
    frequency_0 = count_0 / length

    return {
        "length": length,
        "count_0": count_0,
        "count_1": count_1,
        "frequency_0": frequency_0,
        "frequency_1": frequency_1,
        "bias": frequency_1 - 0.5,
    }
