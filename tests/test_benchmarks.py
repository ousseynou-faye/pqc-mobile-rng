from pathlib import Path
from uuid import uuid4

from benchmarks.config import BENCHMARK_PRESETS
from benchmarks.energy_consumption import build_energy_result_template
from benchmarks.hardware_latency import import_hardware_latency_report
from benchmarks.performance_arm import export_performance_report, run_performance_benchmark


def test_benchmark_result_serialization():
    report = run_performance_benchmark(BENCHMARK_PRESETS["smoke"])
    output_dir = Path("tests_runtime") / "stage7" / f"bench_{uuid4().hex[:8]}"
    output_dir.mkdir(parents=True, exist_ok=True)
    exported = export_performance_report(report, output_dir=output_dir, basename="smoke")

    assert Path(exported["json"]).exists()
    assert Path(exported["csv"]).exists()
    assert Path(exported["markdown"]).exists()


def test_energy_benchmark_reports_not_measured_without_hardware():
    result = build_energy_result_template()

    assert result["status"] == "not_measured"
    assert result["measured_values"] is None


def test_hardware_latency_imports_external_report():
    output_dir = Path("tests_runtime") / "stage7" / f"hw_{uuid4().hex[:8]}"
    output_dir.mkdir(parents=True, exist_ok=True)
    source_path = output_dir / "latency.json"
    source_path.write_text('{"cycles": 1234, "clock_mhz": 50}', encoding="utf-8")

    result = import_hardware_latency_report(source_path)

    assert result["measurement_type"] == "imported_report"
    assert result["values"]["cycles"] == 1234
