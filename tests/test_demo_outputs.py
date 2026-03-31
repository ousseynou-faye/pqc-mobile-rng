from __future__ import annotations

from demos.demo_full_pipeline import render_full_pipeline_demo
from demos.demo_multiplexed_sponge import render_multiplexed_sponge_demo
from demos.demo_rng_output_formats import render_output_formats_demo


def test_output_formats_demo_contains_expected_sections():
    report = render_output_formats_demo()

    assert "=== FORMATS DE SORTIE ===" in report
    assert "Decimal:" in report
    assert "Hex:" in report
    assert "Binaire groupe:" in report


def test_multiplexed_sponge_demo_contains_expected_sections():
    report = render_multiplexed_sponge_demo()

    assert "=== DERIVATION LFSR ===" in report
    assert "=== PHI(l,n) ===" in report
    assert "=== TRACE SPONGE ===" in report


def test_full_pipeline_demo_contains_all_major_layers():
    report = render_full_pipeline_demo(output_bytes=12)

    assert "=== SOURCE D'ENTROPIE ===" in report
    assert "=== CONDITIONNEUR ===" in report
    assert "=== SEEDINIT ===" in report
    assert "=== DERIVATION LFSR ===" in report
    assert "=== SEQUENCE S_n ===" in report
    assert "=== SEQUENCE T_n ===" in report
    assert "=== PHI(l,n) ===" in report
    assert "=== SEQUENCE MULTIPLEXEE ===" in report
    assert "=== MULTIPLEXED SPONGE ===" in report
    assert "=== SORTIE FINALE ===" in report
    assert "Decimal:" in report
