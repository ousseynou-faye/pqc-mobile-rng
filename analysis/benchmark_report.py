"""Exports de rapports de benchmark pour l'etape 7."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def build_benchmark_metadata(*, benchmark_kind: str, config: dict[str, Any], environment: dict[str, Any]) -> dict[str, Any]:
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "benchmark_kind": benchmark_kind,
        "config": config,
        "environment": environment,
        "methodology_warnings": [
            "Benchmark logiciel Python local.",
            "Les resultats ne sont pas directement generalisables a un smartphone sans execution sur cible reelle.",
            "Les mesures memoire sont des estimations via tracemalloc, pas une mesure systeme mobile complete.",
        ],
    }


def export_benchmark_json(report: dict[str, Any], output_path: str | Path) -> Path:
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")
    return target


def export_benchmark_csv(report: dict[str, Any], output_path: str | Path) -> Path:
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "engine",
                "measurement",
                "size_bytes",
                "mean_ns",
                "median_ns",
                "min_ns",
                "max_ns",
                "stdev_ns",
                "mean_peak_memory_bytes",
                "throughput_bytes_per_second",
            ]
        )
        for engine_name, engine_report in report.get("engines", {}).items():
            instantiate = engine_report.get("instantiate")
            if instantiate is not None:
                writer.writerow(
                    [
                        engine_name,
                        "instantiate",
                        "",
                        instantiate["timing"]["mean_ns"],
                        instantiate["timing"]["median_ns"],
                        instantiate["timing"]["min_ns"],
                        instantiate["timing"]["max_ns"],
                        instantiate["timing"]["stdev_ns"],
                        instantiate["memory"]["mean_peak_bytes"],
                        "",
                    ]
                )

            reseed = engine_report.get("reseed")
            if reseed is not None:
                writer.writerow(
                    [
                        engine_name,
                        "reseed",
                        "",
                        reseed["timing"]["mean_ns"],
                        reseed["timing"]["median_ns"],
                        reseed["timing"]["min_ns"],
                        reseed["timing"]["max_ns"],
                        reseed["timing"]["stdev_ns"],
                        reseed["memory"]["mean_peak_bytes"],
                        "",
                    ]
                )

            for size_key, generation in engine_report.get("generation", {}).items():
                writer.writerow(
                    [
                        engine_name,
                        "generate",
                        size_key,
                        generation["timing"]["mean_ns"],
                        generation["timing"]["median_ns"],
                        generation["timing"]["min_ns"],
                        generation["timing"]["max_ns"],
                        generation["timing"]["stdev_ns"],
                        generation["memory"]["mean_peak_bytes"],
                        generation["throughput_bytes_per_second"]["mean"],
                    ]
                )
    return target


def render_benchmark_markdown(report: dict[str, Any]) -> str:
    metadata = report.get("metadata", {})
    lines = [
        "# Benchmark Report",
        "",
        f"- Type: {metadata.get('benchmark_kind', 'unknown')}",
        f"- Date UTC: {metadata.get('generated_at_utc', 'unknown')}",
        f"- Machine: {metadata.get('environment', {}).get('machine', 'unknown')}",
        f"- Systeme: {metadata.get('environment', {}).get('system', 'unknown')}",
        "",
        "## Methodologie",
    ]
    for warning in metadata.get("methodology_warnings", []):
        lines.append(f"- {warning}")

    lines.extend(["", "## Comparaison"])
    for engine_name, summary in report.get("comparison", {}).items():
        lines.append(f"- {engine_name}: {summary}")

    return "\n".join(lines) + "\n"


def export_benchmark_markdown(report: dict[str, Any], output_path: str | Path) -> Path:
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_benchmark_markdown(report), encoding="utf-8")
    return target
