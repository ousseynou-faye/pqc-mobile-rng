from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from software.conditioner import decode_conditioner_seed_for_drbg
from ui.services.project_facade import ProjectFacade


def build_temp_root() -> Path:
    root = Path(__file__).resolve().parents[1] / "tests_runtime" / "ui_facade"
    path = root / f"case_{uuid4().hex[:8]}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_facade_collect_entropy_returns_safe_summary():
    facade = ProjectFacade(root_dir=build_temp_root() / "ui")

    result = facade.collect_entropy(use_cpu=True, use_sensor=False, cpu_sample_count=64)

    assert result["pool_summary"]["accepted_chunks"] >= 1
    assert isinstance(result["raw_preview_hex"], str)
    assert "raw_data" in result


def test_facade_condition_entropy_returns_previews():
    facade = ProjectFacade(root_dir=build_temp_root() / "ui")
    src = facade.collect_entropy(use_cpu=True, use_sensor=False, cpu_sample_count=64)

    conditioned = facade.condition_entropy(src["raw_data"], metadata=src["pool_summary"])

    assert conditioned["input_bits"] > conditioned["output_bits"]
    assert isinstance(conditioned["seed_preview_hex"], str)


def test_facade_validation_smoke_returns_results():
    facade = ProjectFacade(root_dir=build_temp_root() / "ui")

    report = facade.run_validation_smoke()

    assert len(report["results"]) >= 3
    assert any(item["name"] == "API publique" for item in report["results"])


def test_facade_build_lab_seed_material_returns_conditioned_seed():
    facade = ProjectFacade(root_dir=build_temp_root() / "ui")

    bundle = facade.build_lab_seed_material(b"ui-lab-seed", personalization=b"demo")

    assert bundle["seed_material"]
    assert decode_conditioner_seed_for_drbg(bundle["seed_material"]) == bundle["result"].seedinit
