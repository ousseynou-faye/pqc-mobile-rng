from __future__ import annotations

from dataclasses import dataclass

from .errors import DRBGError

"""Je regroupe ici les paramètres cryptographiques du prototype Module-LWR."""


@dataclass(frozen=True, slots=True)
class LWRParams:
    """Je rassemble ici les paramètres publics du moteur Module-LWR."""

    n: int
    k: int
    q: int
    p: int
    secret_bound: int = 1

    def validate(self) -> None:
        """Je vérifie ici la cohérence minimale des paramètres."""

        if self.n <= 0 or self.k <= 0:
            raise DRBGError("Je dois avoir des dimensions LWR strictement positives.")
        if self.q <= 0 or self.p <= 0:
            raise DRBGError("Je dois avoir des moduli strictement positifs.")
        if self.p >= self.q:
            raise DRBGError("Je dois avoir un modulus de réduction p strictement plus petit que q.")
        if self.secret_bound != 1:
            raise DRBGError("Je limite ici le prototype au secret ternaire {-1, 0, 1}.")

    @property
    def rounding_shift(self) -> int | None:
        """Je calcule ici le décalage idéal quand q et p sont des puissances de deux."""

        if self.q <= 0 or self.p <= 0:
            return None
        if (self.q & (self.q - 1)) != 0:
            return None
        if (self.p & (self.p - 1)) != 0:
            return None
        q_bits = self.q.bit_length() - 1
        p_bits = self.p.bit_length() - 1
        if p_bits > q_bits:
            return None
        return q_bits - p_bits


def default_lwr_params() -> LWRParams:
    """Je fournis ici le jeu de paramètres nominal du prototype."""

    return LWRParams(n=256, k=3, q=8192, p=1024, secret_bound=1)
