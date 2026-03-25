"""Orchestration minimale des benchmarks de l'etape 7."""

from __future__ import annotations

from pathlib import Path

from benchmarks.config import BENCHMARK_PRESETS
from benchmarks.energy_consumption import build_energy_result_template, export_energy_result
from benchmarks.hardware_latency import build_hardware_latency_result, export_hardware_latency_result
from benchmarks.performance_arm import export_performance_report, run_performance_benchmark


def run_all(mode: str = "smoke", output_dir: str = "benchmarks/results") -> dict[str, object]:
    config = BENCHMARK_PRESETS[mode]
    performance = run_performance_benchmark(config)
    performance_paths = export_performance_report(performance, output_dir=output_dir, basename=f"performance_{mode}")

    energy = build_energy_result_template()
    energy_path = export_energy_result(energy, Path(output_dir) / f"energy_{mode}.json")

    hardware = build_hardware_latency_result()
    hardware_path = export_hardware_latency_result(hardware, Path(output_dir) / f"hardware_latency_{mode}.json")

    return {
        "performance": performance_paths,
        "energy": str(energy_path),
        "hardware_latency": str(hardware_path),
    }


if __name__ == "__main__":
    print(run_all())
