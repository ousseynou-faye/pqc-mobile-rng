"""J'expose ici les fonctions principales de la couche d'analyse experimentale."""

from .bit_metrics import compute_bit_balance
from .campaign_runner import CAMPAIGN_PRESETS, CampaignConfig, export_campaign_report, run_comparative_campaign
from .entropy_validation import (
    adaptive_proportion_test,
    analyze_entropy_source,
    compare_before_after_conditioning,
    estimate_mcv_min_entropy,
    repetition_count_test,
)
from .generators import bits_from_object, bits_from_sponge
from .golomb_checks import compute_golomb_indicators
from .linear_complexity import berlekamp_massey_linear_complexity
from .period_metrics import estimate_observed_period
from .report import build_bit_sequence_report, build_sponge_report
from .run_metrics import compute_run_metrics
from .statistical_tests import (
    block_frequency_test,
    bytes_to_bits,
    linear_complexity_metric,
    monobit_frequency_test,
    observed_periodicity_metric,
    run_sp800_22_inspired_suite,
    runs_test,
)

__all__ = [
    "CAMPAIGN_PRESETS",
    "CampaignConfig",
    "adaptive_proportion_test",
    "analyze_entropy_source",
    "berlekamp_massey_linear_complexity",
    "bits_from_object",
    "bytes_to_bits",
    "bits_from_sponge",
    "block_frequency_test",
    "build_bit_sequence_report",
    "build_sponge_report",
    "compare_before_after_conditioning",
    "compute_bit_balance",
    "compute_golomb_indicators",
    "compute_run_metrics",
    "estimate_observed_period",
    "estimate_mcv_min_entropy",
    "export_campaign_report",
    "linear_complexity_metric",
    "monobit_frequency_test",
    "observed_periodicity_metric",
    "repetition_count_test",
    "run_comparative_campaign",
    "run_sp800_22_inspired_suite",
    "runs_test",
]
