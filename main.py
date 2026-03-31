from __future__ import annotations

"""Point d'entree de demonstration pour la baseline sponge-only."""

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from software.api.output_formats import format_output_bytes
from software.api.rng_service import RNGService, RNGServiceConfig, StateConfig


@dataclass(slots=True)
class DemoConfig:
    output_bytes: int = 32
    checkpoint_root: str = "demo/.runtime/main_demo"


def _json_ready_output(bundle: dict[str, Any]) -> dict[str, Any]:
    serializable = dict(bundle)
    serializable.pop("raw_bytes", None)
    return serializable


def run_demo(config: DemoConfig | None = None) -> dict[str, Any]:
    cfg = config or DemoConfig()
    service = RNGService(
        config=RNGServiceConfig(
            state=StateConfig(
                root_dir=Path(cfg.checkpoint_root),
                device_id="main-demo-device",
                namespace="main-demo",
                blob_id="main-demo-blob",
                checkpoint_metadata={"purpose": "main-demo-checkpoint"},
            )
        )
    )

    seed = service.build_entropy_seed()
    drbg = service.instantiate_rng(seed_result=seed)
    first = drbg.generate(cfg.output_bytes)
    blob = service.checkpoint_state()
    restored = service.restore_state()
    second = service.generate_bytes(cfg.output_bytes)

    return {
        "config": asdict(cfg),
        "seed_length": len(seed.seedinit),
        "active_engine": drbg.export_state()["manager_state"]["active_engine"],
        "first_output": _json_ready_output(format_output_bytes(first)),
        "second_output": _json_ready_output(format_output_bytes(second)),
        "checkpoint_blob_id": blob.blob_id,
        "restored_lifecycle_state": restored["manager_state"]["lifecycle_state"],
    }


if __name__ == "__main__":
    print(json.dumps(run_demo(), indent=2))
