"""Mobile trajectory profiling helper.

This script does not claim real mobile measurements unless it is executed on an
actual ARM target. It reuses the Python reference implementation and records
that limitation in the exported metadata.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from statistics import fmean
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from software.api import get_rng_service
from software.interface_hw.mobile_bridge import collect_mobile_environment

try:
    from .common import measure_callable
except ImportError:  # pragma: no cover - direct script execution fallback
    from benchmarks.common import measure_callable

DEFAULT_OUTPUT_SIZES = (32, 256, 1024)
DEFAULT_REPETITIONS = 5
DEFAULT_OUTPUT_PATH = Path("benchmarks/results/mobile_profile_smoke.json")


def _measure_many(func, repetitions: int) -> dict[str, float | int]:
    timings = []
    peaks = []
    for _ in range(repetitions):
        elapsed_ns, peak_bytes, _ = measure_callable(func)
        timings.append(elapsed_ns)
        peaks.append(peak_bytes)
    return {
        "count": len(timings),
        "mean_ns": fmean(timings),
        "min_ns": min(timings),
        "max_ns": max(timings),
        "mean_peak_bytes": fmean(peaks),
    }


def run_mobile_profile(
    *,
    output_sizes: tuple[int, ...] = DEFAULT_OUTPUT_SIZES,
    repetitions: int = DEFAULT_REPETITIONS,
) -> dict[str, Any]:
    environment = collect_mobile_environment()
    report: dict[str, Any] = {
        "metadata": {
            "profile_kind": "mobile_transition_reference",
            "environment": environment,
            "not_measured_on_arm": not bool(environment["is_arm"]),
            "warnings": [
                "This profile measures the Python reference path, not a native mobile wrapper.",
            ],
        },
        "operations": {},
    }

    service = get_rng_service(reset=True)
    report["operations"]["instantiate"] = _measure_many(lambda: service.instantiate_rng(), repetitions)

    generation: dict[str, Any] = {}
    for size in output_sizes:
        def _generate() -> bytes:
            service.zeroize()
            service.instantiate_rng()
            return service.generate_bytes(size)

        generation[str(size)] = _measure_many(_generate, repetitions)
    report["operations"]["generate"] = generation

    def _reseed() -> None:
        service.zeroize()
        service.instantiate_rng()
        service.reseed_rng()

    report["operations"]["reseed"] = _measure_many(_reseed, repetitions)

    def _zeroize() -> None:
        service.instantiate_rng()
        service.zeroize()

    report["operations"]["zeroize"] = _measure_many(_zeroize, repetitions)
    return report


def export_mobile_profile(report: dict[str, Any], output_path: str | Path = DEFAULT_OUTPUT_PATH) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return path


if __name__ == "__main__":
    report = run_mobile_profile()
    output = export_mobile_profile(report)
    print(json.dumps(report["metadata"], indent=2))
    print(output)
