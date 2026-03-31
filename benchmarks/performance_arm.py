"""Benchmark logiciel reproductible pour le DRBG Multiplexed Sponge."""

from __future__ import annotations

from pathlib import Path
from statistics import fmean
from typing import Any

from analysis.benchmark_report import (
    build_benchmark_metadata,
    export_benchmark_csv,
    export_benchmark_json,
    export_benchmark_markdown,
)
from software.conditioner import encode_conditioner_seed_for_drbg

from .common import build_composite_drbg, collect_environment_info, measure_callable, summarize_ns
from .config import BENCHMARK_PRESETS, BenchmarkConfig

DEFAULT_SEED = encode_conditioner_seed_for_drbg(b"stage7-performance-seed")
RESEED_PREFIX = b"stage7-reseed-"


def _measure_instantiate(engine_name: str, config: BenchmarkConfig) -> dict[str, Any]:
    timings: list[int] = []
    peaks: list[int] = []

    for _ in range(config.warmup_rounds):
        drbg = build_composite_drbg(engine_name)
        drbg.instantiate(DEFAULT_SEED)

    for _ in range(config.repetitions):
        def _instantiate() -> object:
            drbg = build_composite_drbg(engine_name)
            drbg.instantiate(DEFAULT_SEED)
            return drbg

        elapsed_ns, peak_bytes, _ = measure_callable(_instantiate)
        timings.append(elapsed_ns)
        peaks.append(peak_bytes)

    return {
        "timing": summarize_ns(timings),
        "memory": {
            "mean_peak_bytes": fmean(peaks),
            "min_peak_bytes": min(peaks),
            "max_peak_bytes": max(peaks),
        },
    }


def _measure_reseed(engine_name: str, config: BenchmarkConfig) -> dict[str, Any]:
    timings: list[int] = []
    peaks: list[int] = []

    for _ in range(config.warmup_rounds):
        drbg = build_composite_drbg(engine_name)
        drbg.instantiate(DEFAULT_SEED)
        drbg.reseed(encode_conditioner_seed_for_drbg(RESEED_PREFIX + b"warmup"))

    for index in range(config.repetitions):
        drbg = build_composite_drbg(engine_name)
        drbg.instantiate(DEFAULT_SEED)

        elapsed_ns, peak_bytes, _ = measure_callable(
            lambda: drbg.reseed(
                encode_conditioner_seed_for_drbg(RESEED_PREFIX + str(index).encode("ascii"))
            )
        )
        timings.append(elapsed_ns)
        peaks.append(peak_bytes)

    return {
        "timing": summarize_ns(timings),
        "memory": {
            "mean_peak_bytes": fmean(peaks),
            "min_peak_bytes": min(peaks),
            "max_peak_bytes": max(peaks),
        },
    }


def _measure_generation_for_size(engine_name: str, output_size: int, config: BenchmarkConfig) -> dict[str, Any]:
    timings: list[int] = []
    peaks: list[int] = []

    for warmup_round in range(config.warmup_rounds):
        drbg = build_composite_drbg(engine_name)
        drbg.instantiate(DEFAULT_SEED)
        drbg.generate(output_size, additional_input=f"warmup:{warmup_round}".encode("ascii"))

    for repetition in range(config.repetitions):
        drbg = build_composite_drbg(engine_name)
        drbg.instantiate(DEFAULT_SEED)
        elapsed_ns, peak_bytes, _ = measure_callable(
            lambda: drbg.generate(output_size, additional_input=f"gen:{repetition}".encode("ascii"))
        )
        timings.append(elapsed_ns)
        peaks.append(peak_bytes)

    timing = summarize_ns(timings)
    throughput_values = [
        output_size / (sample_ns / 1_000_000_000)
        for sample_ns in timings
        if sample_ns > 0
    ]
    return {
        "size_bytes": output_size,
        "timing": timing,
        "memory": {
            "mean_peak_bytes": fmean(peaks),
            "min_peak_bytes": min(peaks),
            "max_peak_bytes": max(peaks),
        },
        "throughput_bytes_per_second": {
            "mean": fmean(throughput_values),
            "min": min(throughput_values),
            "max": max(throughput_values),
        },
    }


def run_performance_benchmark(
    config: BenchmarkConfig,
    *,
    engines: tuple[str, ...] = ("multiplexed_sponge",),
) -> dict[str, Any]:
    """Execute un benchmark logiciel local et qualifie l'environnement reel."""

    environment = collect_environment_info()
    report: dict[str, Any] = {
        "metadata": build_benchmark_metadata(
            benchmark_kind="software_performance",
            config=config.to_dict(),
            environment=environment,
        ),
        "engines": {},
        "comparison": {},
    }
    report["metadata"]["methodology_warnings"].append(
        "Le nom performance_arm.py ne signifie pas que les chiffres proviennent d'une cible ARM reelle."
    )

    for engine_name in engines:
        generation_results = {
            str(output_size): _measure_generation_for_size(engine_name, output_size, config)
            for output_size in config.output_sizes
        }
        report["engines"][engine_name] = {
            "engine_name": engine_name,
            "instantiate": _measure_instantiate(engine_name, config),
            "reseed": _measure_reseed(engine_name, config),
            "generation": generation_results,
        }

    for engine_name, engine_report in report["engines"].items():
        instantiate_mean = engine_report["instantiate"]["timing"]["mean_ns"]
        reseed_mean = engine_report["reseed"]["timing"]["mean_ns"]
        largest_size = str(max(config.output_sizes))
        generation_mean = engine_report["generation"][largest_size]["timing"]["mean_ns"]
        throughput_mean = engine_report["generation"][largest_size]["throughput_bytes_per_second"]["mean"]
        report["comparison"][engine_name] = (
            f"instantiate mean {instantiate_mean:.1f} ns, "
            f"reseed mean {reseed_mean:.1f} ns, "
            f"generate({largest_size} B) mean {generation_mean:.1f} ns, "
            f"throughput mean {throughput_mean:.1f} B/s"
        )

    return report


def export_performance_report(report: dict[str, Any], *, output_dir: str | Path, basename: str) -> dict[str, str]:
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    exported = {
        "json": str(export_benchmark_json(report, output_root / f"{basename}.json")),
        "csv": str(export_benchmark_csv(report, output_root / f"{basename}.csv")),
        "markdown": str(export_benchmark_markdown(report, output_root / f"{basename}.md")),
    }
    return exported


if __name__ == "__main__":
    smoke_report = run_performance_benchmark(BENCHMARK_PRESETS["smoke"])
    paths = export_performance_report(smoke_report, output_dir="benchmarks/results", basename="performance_smoke")
    print(smoke_report["comparison"])
    print(paths)
