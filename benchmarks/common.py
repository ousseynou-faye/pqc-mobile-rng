"""Helpers communs pour les benchmarks logiciels."""

from __future__ import annotations

import platform
import statistics
import sys
import tracemalloc
from typing import Any, Callable

from software.api.rng_service import _build_research_sponge
from software.pqc_drbg import DRBGPolicy, EngineSelectionMode, PQCCompositeDRBG
from software.pqc_drbg.sponge_core import MultiplexedSpongeAdapter


def collect_environment_info() -> dict[str, Any]:
    machine = platform.machine() or "unknown"
    return {
        "machine": machine,
        "processor": platform.processor() or "unknown",
        "system": platform.system(),
        "platform": platform.platform(),
        "python_version": sys.version,
        "is_arm": machine.lower() in {"arm64", "aarch64", "armv7l"},
        "environment_type": "local_python_benchmark",
    }


def build_composite_drbg(engine_name: str) -> PQCCompositeDRBG:
    if engine_name == "multiplexed_sponge":
        return PQCCompositeDRBG()

    if engine_name == "module_lwr":
        return PQCCompositeDRBG(
            sponge_engine=MultiplexedSpongeAdapter(sponge_factory=_build_research_sponge),
            policy=DRBGPolicy(selection_mode=EngineSelectionMode.FORCE_LWR_RESEARCH),
        )

    raise ValueError(f"Moteur inconnu: {engine_name}")


def summarize_ns(samples_ns: list[int]) -> dict[str, float | int]:
    if not samples_ns:
        raise ValueError("Je demande au moins un echantillon.")

    return {
        "count": len(samples_ns),
        "mean_ns": statistics.fmean(samples_ns),
        "median_ns": statistics.median(samples_ns),
        "min_ns": min(samples_ns),
        "max_ns": max(samples_ns),
        "stdev_ns": statistics.stdev(samples_ns) if len(samples_ns) > 1 else 0.0,
    }


def measure_callable(func: Callable[[], Any]) -> tuple[int, int, Any]:
    """Mesure une operation avec temps mur et pic memoire Python via tracemalloc."""

    tracemalloc.start()
    start_ns = __import__("time").perf_counter_ns()
    result = func()
    end_ns = __import__("time").perf_counter_ns()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return end_ns - start_ns, peak, result
