"""Cadre honnete pour la latence materielle de l'etape 7."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def build_hardware_latency_result(
    *,
    measurement_type: str = "not_measured",
    source: str = "none",
    values: dict[str, Any] | None = None,
    notes: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "measurement_type": measurement_type,
        "source": source,
        "values": values or {},
        "notes": notes
        or [
            "Aucune latence materielle reelle n'est fournie dans cet environnement.",
            "Une simulation VHDL/FPGA ou un rapport de synthese externe est necessaire pour renseigner cette section.",
        ],
    }


def import_hardware_latency_report(source_path: str | Path) -> dict[str, Any]:
    path = Path(source_path)
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
    elif path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            payload = {"rows": list(reader)}
    else:
        raise ValueError("Formats supportes: .json et .csv")

    return build_hardware_latency_result(
        measurement_type="imported_report",
        source=str(path),
        values=payload,
        notes=["Latence materielle importee depuis un rapport externe."],
    )


def export_hardware_latency_result(result: dict[str, Any], output_path: str | Path) -> Path:
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, ensure_ascii=True), encoding="utf-8")
    return target
