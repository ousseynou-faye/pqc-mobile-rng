from pathlib import Path
from uuid import uuid4

from analysis.campaign_runner import CAMPAIGN_PRESETS, export_campaign_report, run_comparative_campaign
from analysis.statistical_tests import monobit_frequency_test, run_sp800_22_inspired_suite, runs_test


def test_monobit_frequency_on_balanced_sequence():
    result = monobit_frequency_test([0, 1] * 64, alpha=0.01)

    assert result["passed"] is True
    assert result["p_value"] is not None


def test_runs_test_rejects_pathological_sequence():
    result = runs_test([0] * 128, alpha=0.01)

    assert result["passed"] is False
    assert result["p_value"] == 0.0


def test_statistical_suite_contains_descriptive_metrics():
    report = run_sp800_22_inspired_suite([0, 1] * 128, alpha=0.01, block_size=32, max_period=32)

    assert "linear_complexity_metric" in report["tests"]
    assert "observed_periodicity_metric" in report["tests"]


def test_statistical_smoke_campaign_generates_report():
    config = CAMPAIGN_PRESETS["smoke"]
    report = run_comparative_campaign(config)
    output_dir = Path("tests_runtime") / "stage6" / f"smoke_{uuid4().hex[:8]}"
    output_dir.mkdir(parents=True, exist_ok=True)
    exported = export_campaign_report(report, output_dir=output_dir, basename="smoke_campaign")

    assert "multiplexed_sponge" in report["engines"]
    assert Path(exported["json"]).exists()
    assert Path(exported["markdown"]).exists()
    assert Path(exported["csv"]).exists()
