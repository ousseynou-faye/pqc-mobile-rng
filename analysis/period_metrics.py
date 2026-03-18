"""J'estime ici une periode observee sur une fenetre binaire finie."""

from __future__ import annotations

from collections.abc import Sequence


def estimate_observed_period(bits: Sequence[int], max_period: int | None = None) -> dict[str, int | None]:
    """J'utilise cette fonction pour estimer une periode observee sur un echantillon.

    Cette mesure reste strictement experimentale :
    - elle depend de la longueur de l'echantillon ;
    - elle ne garantit pas que la periode theorique complete a ete atteinte ;
    - elle detecte seulement le plus petit decalage qui reproduit exactement la
      fenetre observee sur sa partie comparable.
    """

    sample = [int(bit) for bit in bits]
    if any(bit not in (0, 1) for bit in sample):
        raise ValueError("Je demande une sequence binaire composee uniquement de 0 et de 1.")

    length = len(sample)
    if length == 0:
        return {"observed_period": None, "checked_prefix_length": 0}

    upper_bound = max_period if max_period is not None else length // 2
    upper_bound = max(1, min(upper_bound, max(length - 1, 1)))

    for period in range(1, upper_bound + 1):
        comparable_length = length - period
        if comparable_length <= 0:
            break
        if sample[:comparable_length] == sample[period:period + comparable_length]:
            return {
                "observed_period": period,
                "checked_prefix_length": comparable_length,
            }

    return {"observed_period": None, "checked_prefix_length": max(length - 1, 0)}
