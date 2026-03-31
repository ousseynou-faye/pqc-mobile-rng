from __future__ import annotations

from pathlib import Path

from software.pqc_drbg.policy import EngineSelectionMode


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_engine_selection_mode_contains_only_sponge_only():
    assert [mode.value for mode in EngineSelectionMode] == ["strict_sponge_only"]


def test_maintained_source_tree_contains_no_legacy_engine_markers():
    tracked_roots = [
        PROJECT_ROOT / "software",
        PROJECT_ROOT / "docs",
        PROJECT_ROOT / "ui",
        PROJECT_ROOT / "analysis",
        PROJECT_ROOT / "benchmarks",
        PROJECT_ROOT / "README.md",
        PROJECT_ROOT / "main.py",
        PROJECT_ROOT / "demo" / "run_full_project_demo.py",
        PROJECT_ROOT / "test_DRBG.py",
    ]
    forbidden = [
        "module" + "_lwr",
        "Module" + "-LWR",
        "ALLOW" + "_EXPERIMENTAL_" + "LWR" + "_FALLBACK",
        "FORCE" + "_LWR_" + "RESEARCH",
    ]

    file_paths: list[Path] = []
    for root in tracked_roots:
        if root.is_file():
            file_paths.append(root)
        else:
            file_paths.extend(path for path in root.rglob("*") if path.is_file())

    text_suffixes = {".py", ".md", ".txt", ".json", ".csv", ".vhd", ".css"}
    for path in file_paths:
        if path.suffix.lower() not in text_suffixes:
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        for marker in forbidden:
            assert marker not in content, f"{marker} trouve dans {path}"
