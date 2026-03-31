"""Orchestrateur de campagnes comparatives pour l'etape 6."""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean
from typing import Any

from software.api.rng_service import _build_research_sponge
from software.pqc_drbg import DRBGPolicy, EngineSelectionMode, PQCCompositeDRBG
from software.pqc_drbg.sponge_core import MultiplexedSpongeAdapter

from .bit_metrics import compute_bit_balance
from .statistical_tests import bytes_to_bits, run_sp800_22_inspired_suite
from .validation_report import build_validation_metadata, export_json_report, export_markdown_summary


@dataclass(frozen=True)
class CampaignConfig:
    mode: str
    n_bits: int
    repetitions: int
    alpha: float = 0.01
    block_size: int = 128
    max_period: int | None = None
    output_dir: str = "analysis/reports"
    export_markdown: bool = True
    export_csv: bool = True


CAMPAIGN_PRESETS: dict[str, CampaignConfig] = {
    "smoke": CampaignConfig(mode="smoke", n_bits=1024, repetitions=2, block_size=64, max_period=64),
    "local": CampaignConfig(mode="local", n_bits=8192, repetitions=4, block_size=128, max_period=256),
    "memoire": CampaignConfig(mode="memoire", n_bits=65536, repetitions=8, block_size=256, max_period=1024),
}


def _build_drbg(engine_name: str) -> PQCCompositeDRBG:
    if engine_name == "multiplexed_sponge":
        drbg = PQCCompositeDRBG()
        drbg.instantiate(b"stage6-multiplexed-sponge-seed")
        return drbg

    if engine_name == "module_lwr":
        drbg = PQCCompositeDRBG(
            sponge_engine=MultiplexedSpongeAdapter(sponge_factory=_build_research_sponge),
            policy=DRBGPolicy(selection_mode=EngineSelectionMode.FORCE_LWR_RESEARCH),
        )
        drbg.instantiate(b"stage6-module-lwr-seed")
        return drbg

    raise ValueError(f"Moteur inconnu: {engine_name}")


def _aggregate_engine_runs(run_results: list[dict[str, Any]]) -> dict[str, Any]:
    bias_values = [run["bit_balance"]["bias"] for run in run_results]
    success_ratios = [run["suite"]["summary"]["success_ratio"] for run in run_results]
    longest_runs = [
        run["suite"]["tests"]["runs"]["statistic"]
        for run in run_results
        if run["suite"]["tests"]["runs"]["statistic"] is not None
    ]
    normalized_linear_complexities = [
        run["suite"]["tests"]["linear_complexity_metric"]["normalized_linear_complexity"]
        for run in run_results
    ]

    per_test_success: dict[str, float] = {}
    for test_name in run_results[0]["suite"]["tests"]:
        pass_count = sum(1 for run in run_results if run["suite"]["tests"][test_name]["passed"])
        per_test_success[test_name] = pass_count / len(run_results)

    return {
        "bias": {
            "mean": mean(bias_values),
            "min": min(bias_values),
            "max": max(bias_values),
        },
        "suite_success_ratio": {
            "mean": mean(success_ratios),
            "min": min(success_ratios),
            "max": max(success_ratios),
        },
        "runs_statistic": {
            "mean": mean(longest_runs) if longest_runs else None,
            "min": min(longest_runs) if longest_runs else None,
            "max": max(longest_runs) if longest_runs else None,
        },
        "normalized_linear_complexity": {
            "mean": mean(normalized_linear_complexities),
            "min": min(normalized_linear_complexities),
            "max": max(normalized_linear_complexities),
        },
        "per_test_success_rate": per_test_success,
    }


def _write_csv_summary(report: dict[str, Any], output_path: str | Path) -> Path:
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["engine", "bias_mean", "suite_success_mean", "linear_complexity_mean"])
        for engine_name, engine_report in report["engines"].items():
            aggregates = engine_report["aggregates"]
            writer.writerow(
                [
                    engine_name,
                    aggregates["bias"]["mean"],
                    aggregates["suite_success_ratio"]["mean"],
                    aggregates["normalized_linear_complexity"]["mean"],
                ]
            )
    return target


def run_comparative_campaign(
    config: CampaignConfig,
    *,
    engines: tuple[str, ...] = ("multiplexed_sponge", "module_lwr"),
) -> dict[str, Any]:
    """Lance une campagne comparative reproductible sur des flux DRBG."""

    if config.n_bits <= 0:
        raise ValueError("n_bits doit etre > 0.")
    if config.repetitions <= 0:
        raise ValueError("repetitions doit etre > 0.")

    report: dict[str, Any] = {
        "metadata": build_validation_metadata(
            context="comparative_drbg_campaign",
            mode=config.mode,
            parameters=asdict(config),
        ),
        "engines": {},
        "comparison": {},
    }

    nbytes = (config.n_bits + 7) // 8
    for engine_name in engines:
        drbg = _build_drbg(engine_name)
        runs: list[dict[str, Any]] = []
        for repetition in range(config.repetitions):
            out = drbg.generate(nbytes, additional_input=f"{engine_name}:{repetition}".encode("ascii"))
            bits = bytes_to_bits(out)[:config.n_bits]
            suite = run_sp800_22_inspired_suite(
                bits,
                alpha=config.alpha,
                block_size=config.block_size,
                max_period=config.max_period,
            )
            runs.append(
                {
                    "repetition": repetition,
                    "n_bits": config.n_bits,
                    "bit_balance": compute_bit_balance(bits),
                    "suite": suite,
                }
            )

        aggregates = _aggregate_engine_runs(runs)
        report["engines"][engine_name] = {
            "engine_name": engine_name,
            "n_bits": config.n_bits,
            "repetitions": config.repetitions,
            "runs": runs,
            "aggregates": aggregates,
        }

    for engine_name, engine_report in report["engines"].items():
        aggregates = engine_report["aggregates"]
        report["comparison"][engine_name] = (
            f"taux moyen de succes {aggregates['suite_success_ratio']['mean']:.3f}, "
            f"biais moyen {aggregates['bias']['mean']:.6f}, "
            f"complexite lineaire normalisee moyenne {aggregates['normalized_linear_complexity']['mean']:.6f}"
        )

    return report


def export_campaign_report(report: dict[str, Any], *, output_dir: str | Path, basename: str) -> dict[str, str]:
    """Exporte le rapport de campagne en JSON et formats complementaires."""

    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    json_path = export_json_report(report, output_root / f"{basename}.json")
    exported = {"json": str(json_path)}

    markdown_path = export_markdown_summary(report, output_root / f"{basename}.md")
    exported["markdown"] = str(markdown_path)

    csv_path = _write_csv_summary(report, output_root / f"{basename}.csv")
    exported["csv"] = str(csv_path)
    return exported
