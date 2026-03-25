from analysis.entropy_validation import (
    analyze_entropy_source,
    compare_before_after_conditioning,
    estimate_mcv_min_entropy,
)
from analysis.validation_report import build_validation_metadata


def test_entropy_mcv_on_balanced_source():
    report = estimate_mcv_min_entropy([0, 1] * 16)

    assert report["method"] == "most_common_value"
    assert report["most_common_value_probability"] == 0.5
    assert report["min_entropy_per_symbol"] == 1.0


def test_entropy_detects_degenerate_source():
    report = analyze_entropy_source(
        [0] * 64,
        symbol_bits=1,
        source_name="degenerate",
        repetition_limit=8,
        adaptive_window_size=16,
        adaptive_max_proportion=0.75,
    )

    assert report["health_report"]["accepted"] is False
    assert report["repetition_count_test"]["passed"] is False
    assert report["adaptive_proportion_test"]["passed"] is False


def test_entropy_conditioning_comparison_is_structured():
    report = compare_before_after_conditioning(bytes(range(32)))

    assert report["raw_data_bytes"] == 32
    assert "raw_bit_assessment" in report
    assert "toeplitz_bit_assessment" in report
    assert "seed_bit_assessment" in report


def test_report_contains_non_compliance_disclaimer():
    metadata = build_validation_metadata(
        context="unit_test",
        mode="smoke",
        parameters={"n_bits": 128},
    )

    assert any(
        "ne revendique aucune conformite" in item.lower() or "non" in item.lower()
        for item in metadata["non_compliance_scope"]
    )
