"""Cadre honnete pour les mesures d'energie de l'etape 7."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from benchmarks.common import collect_environment_info


def build_energy_result_template(
    *,
    status: str = "not_measured",
    collection_mode: str = "external_meter_required",
    notes: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "status": status,
        "collection_mode": collection_mode,
        "environment": collect_environment_info(),
        "unit": None,
        "measurement_window_seconds": None,
        "hardware_used": None,
        "measured_values": None,
        "notes": notes
        or [
            "Aucune mesure energetique reelle n'a ete effectuee dans cet environnement.",
            "Un wattmetre externe, ADB batterystats ou Android Profiler est requis pour une mesure credible.",
        ],
    }


def import_external_energy_measurement(source_path: str | Path) -> dict[str, Any]:
    path = Path(source_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["status"] = "measured_external"
    payload.setdefault("notes", [])
    payload["notes"].append("Mesure importee depuis un rapport externe.")
    return payload


def export_energy_result(result: dict[str, Any], output_path: str | Path) -> Path:
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, ensure_ascii=True), encoding="utf-8")
    return target
