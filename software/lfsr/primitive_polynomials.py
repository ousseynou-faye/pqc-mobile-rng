"""
./software/lfsr/primitive_polynomials.py

Collection de polynômes primitifs pour LFSR utilisés dans le RNG
Mobile Post-Quantique.

Ces polynômes permettent de générer des m-sequences de période :

    T = 2^n - 1

Sources académiques :
- Golomb, Shift Register Sequences
- Xilinx Application Notes
- CRC Polynomial Tables
"""

from dataclasses import dataclass


@dataclass
class PrimitivePolynomial:
    degree: int
    taps: list
    polynomial: str


# ------------------------------------------------------------------
# Base de données des polynômes primitifs
# ------------------------------------------------------------------

PRIMITIVE_POLYNOMIALS = {

    8: PrimitivePolynomial(
        degree=8,
        taps=[8,6,5,4],
        polynomial="x^8 + x^6 + x^5 + x^4 + 1"
    ),

    9: PrimitivePolynomial(
        degree=9,
        taps=[9,5],
        polynomial="x^9 + x^5 + 1"
    ),

    10: PrimitivePolynomial(
        degree=10,
        taps=[10,7],
        polynomial="x^10 + x^7 + 1"
    ),

    11: PrimitivePolynomial(
        degree=11,
        taps=[11,9],
        polynomial="x^11 + x^9 + 1"
    ),

    12: PrimitivePolynomial(
        degree=12,
        taps=[12,6,4,1],
        polynomial="x^12 + x^6 + x^4 + x + 1"
    ),

    13: PrimitivePolynomial(
        degree=13,
        taps=[13,4,3,1],
        polynomial="x^13 + x^4 + x^3 + x + 1"
    ),

    16: PrimitivePolynomial(
        degree=16,
        taps=[16,14,13,11],
        polynomial="x^16 + x^14 + x^13 + x^11 + 1"
    ),

    17: PrimitivePolynomial(
        degree=17,
        taps=[17,14],
        polynomial="x^17 + x^14 + 1"
    ),

    19: PrimitivePolynomial(
        degree=19,
        taps=[19,5,2,1],
        polynomial="x^19 + x^5 + x^2 + x + 1"
    ),

    21: PrimitivePolynomial(
        degree=21,
        taps=[21,2],
        polynomial="x^21 + x^2 + 1"
    ),

    23: PrimitivePolynomial(
        degree=23,
        taps=[23,5],
        polynomial="x^23 + x^5 + 1"
    ),

    24: PrimitivePolynomial(
        degree=24,
        taps=[24,23,22,17],
        polynomial="x^24 + x^23 + x^22 + x^17 + 1"
    ),

    31: PrimitivePolynomial(
        degree=31,
        taps=[31,3],
        polynomial="x^31 + x^3 + 1"
    ),

    32: PrimitivePolynomial(
        degree=32,
        taps=[32,22,2,1],
        polynomial="x^32 + x^22 + x^2 + x + 1"
    ),

    40: PrimitivePolynomial(
        degree=40,
        taps=[40,5,4,3],
        polynomial="x^40 + x^5 + x^4 + x^3 + 1"
    ),

    48: PrimitivePolynomial(
        degree=48,
        taps=[48,28,27,1],
        polynomial="x^48 + x^28 + x^27 + x + 1"
    ),

    64: PrimitivePolynomial(
        degree=64,
        taps=[64,4,3,1],
        polynomial="x^64 + x^4 + x^3 + x + 1"
    ),

    96: PrimitivePolynomial(
        degree=96,
        taps=[96,10,9,6],
        polynomial="x^96 + x^10 + x^9 + x^6 + 1"
    ),

    128: PrimitivePolynomial(
        degree=128,
        taps=[128,7,2,1],
        polynomial="x^128 + x^7 + x^2 + x + 1"
    ),

    256: PrimitivePolynomial(
        degree=256,
        taps=[256,10,5,2],
        polynomial="x^256 + x^10 + x^5 + x^2 + 1"
    )
}

# ------------------------------------------------------------------
# Fonctions utilitaires
# ------------------------------------------------------------------

def get_polynomial(degree: int) -> PrimitivePolynomial:
    """
    Retourne le polynôme primitif pour une taille donnée
    """

    if degree not in PRIMITIVE_POLYNOMIALS:
        raise ValueError(f"Aucun polynôme pour {degree} bits")

    return PRIMITIVE_POLYNOMIALS[degree]


def list_supported_degrees():
    """
    Liste toutes les tailles disponibles
    """

    return sorted(PRIMITIVE_POLYNOMIALS.keys())