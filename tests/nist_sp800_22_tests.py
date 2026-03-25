"""Facade legere pour la batterie statistique experimentale."""

from analysis.statistical_tests import (
    block_frequency_test,
    linear_complexity_metric,
    monobit_frequency_test,
    observed_periodicity_metric,
    run_sp800_22_inspired_suite,
    runs_test,
)

__all__ = [
    "block_frequency_test",
    "linear_complexity_metric",
    "monobit_frequency_test",
    "observed_periodicity_metric",
    "run_sp800_22_inspired_suite",
    "runs_test",
]
