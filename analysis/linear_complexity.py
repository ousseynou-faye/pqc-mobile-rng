"""J'approxime ici la complexite lineaire d'un echantillon binaire."""

from __future__ import annotations

from collections.abc import Sequence


def berlekamp_massey_linear_complexity(bits: Sequence[int]) -> dict[str, float | int]:
    """J'applique ici Berlekamp-Massey sur une sequence binaire finie.

    Dans cette etape, je cherche a obtenir une approximation exploitable de la
    complexite lineaire sur un echantillon fini. Le resultat depend donc de la
    taille de la fenetre analysee et ne constitue pas une preuve cryptographique.
    """

    sample = [int(bit) for bit in bits]
    if any(bit not in (0, 1) for bit in sample):
        raise ValueError("Je demande une sequence binaire composee uniquement de 0 et de 1.")

    n = len(sample)
    if n == 0:
        return {"length": 0, "linear_complexity": 0, "normalized_linear_complexity": 0.0}

    c = [0] * n
    b = [0] * n
    c[0] = 1
    b[0] = 1

    linear_complexity = 0
    m = -1

    for index in range(n):
        discrepancy = sample[index]
        for j in range(1, linear_complexity + 1):
            discrepancy ^= c[j] & sample[index - j]

        if discrepancy == 0:
            continue

        previous = c[:]
        shift = index - m
        for j in range(n - shift):
            c[j + shift] ^= b[j]

        if 2 * linear_complexity <= index:
            linear_complexity = index + 1 - linear_complexity
            m = index
            b = previous

    return {
        "length": n,
        "linear_complexity": linear_complexity,
        "normalized_linear_complexity": linear_complexity / n,
    }
