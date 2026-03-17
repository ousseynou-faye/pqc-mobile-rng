'''
    Ce fichier contient la base de données des polynômes primitifs utilisés pour configurer les LFSR.
'''

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True) # On rend la classe immuable pour garantir que les polynômes primitifs ne peuvent pas être modifiés après leur création.
class PrimitivePolynomial:
    degree: int
    taps: tuple[int, ...]
    polynomial: str


PRIMITIVE_POLYNOMIALS: Dict[int, PrimitivePolynomial] = {
    8: PrimitivePolynomial(8, (8, 6, 5, 4), "x^8 + x^6 + x^5 + x^4 + 1"),
    9: PrimitivePolynomial(9, (9, 5), "x^9 + x^5 + 1"),
    10: PrimitivePolynomial(10, (10, 7), "x^10 + x^7 + 1"),
    11: PrimitivePolynomial(11, (11, 9), "x^11 + x^9 + 1"),
    12: PrimitivePolynomial(12, (12, 6, 4, 1), "x^12 + x^6 + x^4 + x + 1"),
    13: PrimitivePolynomial(13, (13, 4, 3, 1), "x^13 + x^4 + x^3 + x + 1"),
    16: PrimitivePolynomial(16, (16, 14, 13, 11), "x^16 + x^14 + x^13 + x^11 + 1"),
    17: PrimitivePolynomial(17, (17, 14), "x^17 + x^14 + 1"),
    19: PrimitivePolynomial(19, (19, 5, 2, 1), "x^19 + x^5 + x^2 + x + 1"),
    21: PrimitivePolynomial(21, (21, 2), "x^21 + x^2 + 1"),
    23: PrimitivePolynomial(23, (23, 5), "x^23 + x^5 + 1"),
    24: PrimitivePolynomial(24, (24, 23, 22, 17), "x^24 + x^23 + x^22 + x^17 + 1"),
    31: PrimitivePolynomial(31, (31, 3), "x^31 + x^3 + 1"),
    32: PrimitivePolynomial(32, (32, 22, 2, 1), "x^32 + x^22 + x^2 + x + 1"),
    40: PrimitivePolynomial(40, (40, 5, 4, 3), "x^40 + x^5 + x^4 + x^3 + 1"),
    48: PrimitivePolynomial(48, (48, 28, 27, 1), "x^48 + x^28 + x^27 + x + 1"),
    64: PrimitivePolynomial(64, (64, 4, 3, 1), "x^64 + x^4 + x^3 + x + 1"),
    96: PrimitivePolynomial(96, (96, 10, 9, 6), "x^96 + x^10 + x^9 + x^6 + 1"),
    128: PrimitivePolynomial(128, (128, 7, 2, 1), "x^128 + x^7 + x^2 + x + 1"),
    256: PrimitivePolynomial(256, (256, 10, 5, 2), "x^256 + x^10 + x^5 + x^2 + 1"),
}


def get_polynomial(degree: int) -> PrimitivePolynomial:
    if degree not in PRIMITIVE_POLYNOMIALS:
        raise ValueError(f"Aucun polynôme primitif défini pour le degré {degree}.")
    return PRIMITIVE_POLYNOMIALS[degree]


def list_supported_degrees() -> List[int]:
    return sorted(PRIMITIVE_POLYNOMIALS.keys())