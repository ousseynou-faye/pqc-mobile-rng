"""J'expose ici les fonctions principales de la couche d'analyse experimentale."""

from .bit_metrics import compute_bit_balance
from .generators import bits_from_object, bits_from_sponge
from .golomb_checks import compute_golomb_indicators
from .linear_complexity import berlekamp_massey_linear_complexity
from .period_metrics import estimate_observed_period
from .report import build_bit_sequence_report, build_sponge_report
from .run_metrics import compute_run_metrics

__all__ = [
    "berlekamp_massey_linear_complexity",
    "bits_from_object",
    "bits_from_sponge",
    "build_bit_sequence_report",
    "build_sponge_report",
    "compute_bit_balance",
    "compute_golomb_indicators",
    "compute_run_metrics",
    "estimate_observed_period",
]
