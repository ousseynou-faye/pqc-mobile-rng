from __future__ import annotations

"""Demonstration complete du pipeline officiel SRC -> COND -> DRBG -> STATE."""

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT_STR = str(PROJECT_ROOT)
if PROJECT_ROOT_STR not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_STR)

from software.api.rng_service import RNGService, RNGServiceConfig, StateConfig
from software.api.output_formats import format_output_bytes


@dataclass(slots=True)
class FullDemoConfig:
    output_bytes: int = 48
    root_dir: str = "demo/.runtime/full_project_demo"


def _json_ready_output(bundle: dict[str, Any]) -> dict[str, Any]:
    serializable = dict(bundle)
    serializable.pop("raw_bytes", None)
    return serializable


def run_full_project_demo(config: FullDemoConfig | None = None) -> dict[str, Any]:
    cfg = config or FullDemoConfig()
    service = RNGService(
        config=RNGServiceConfig(
            state=StateConfig(
                root_dir=Path(cfg.root_dir),
                device_id="full-demo-device",
                namespace="full-demo",
                blob_id="full-demo-blob",
                checkpoint_metadata={"purpose": "full-demo-checkpoint"},
            )
        )
    )

    seed = service.build_entropy_seed()
    drbg = service.instantiate_rng(seed_result=seed)
    generated = service.generate_bytes(cfg.output_bytes, additional_input=b"full-demo")
    service.reseed_rng(additional_input=b"full-demo-reseed")
    reseeded = service.generate_bytes(cfg.output_bytes)
    checkpoint = service.checkpoint_state()
    restored_payload = service.restore_state()

    return {
        "seed_length": len(seed.seedinit),
        "conditioner_output_bits": seed.output_bits,
        "active_engine": drbg.export_state()["manager_state"]["active_engine"],
        "generated_output": _json_ready_output(format_output_bytes(generated)),
        "reseeded_output": _json_ready_output(format_output_bytes(reseeded)),
        "checkpoint_blob_id": checkpoint.blob_id,
        "restored_manager_state": restored_payload["manager_state"],
        "sdk_status": service.sdk_status(),
    }


if __name__ == "__main__":
    print(json.dumps(run_full_project_demo(), indent=2))
