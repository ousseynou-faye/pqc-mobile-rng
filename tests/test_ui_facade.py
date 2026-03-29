from __future__ import annotations

from ui.services.project_facade import ProjectFacade


def test_facade_collect_entropy_returns_safe_summary(tmp_path):
    facade = ProjectFacade(root_dir=tmp_path / "ui")

    result = facade.collect_entropy(use_cpu=True, use_sensor=False, cpu_sample_count=64)

    assert result["pool_summary"]["accepted_chunks"] >= 1
    assert isinstance(result["raw_preview_hex"], str)
    assert "raw_data" in result


def test_facade_condition_entropy_returns_previews(tmp_path):
    facade = ProjectFacade(root_dir=tmp_path / "ui")
    src = facade.collect_entropy(use_cpu=True, use_sensor=False, cpu_sample_count=64)

    conditioned = facade.condition_entropy(src["raw_data"], metadata=src["pool_summary"])

    assert conditioned["input_bits"] > conditioned["output_bits"]
    assert isinstance(conditioned["seed_preview_hex"], str)


def test_facade_validation_smoke_returns_results(tmp_path):
    facade = ProjectFacade(root_dir=tmp_path / "ui")

    report = facade.run_validation_smoke()

    assert len(report["results"]) >= 3
    assert any(item["name"] == "API publique" for item in report["results"])
