"""Helpers de reporting pour la validation experimentale de l'etape 6."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DISCLAIMER_IMPLEMENTED = [
    "Validation experimentale de la source d'entropie, du conditionnement et des sorties DRBG.",
    "Health checks simples et estimation prudente de min-entropie par Most Common Value.",
    "Campagnes statistiques comparatives sur Module-LWR et Multiplexed Sponge.",
]

DISCLAIMER_INSPIRED = [
    "Architecture SRC -> COND -> DRBG inspiree des bonnes pratiques de separation des couches.",
    "Health checks inspires de SP 800-90B pour repetition count et adaptive proportion.",
    "Tests statistiques inspires de SP 800-22 utilises comme indicateurs experimentaux.",
]

DISCLAIMER_NOT_FORMAL = [
    "Ce rapport ne revendique aucune conformite formelle a SP 800-90A, SP 800-90B, SP 800-22, FIPS ou CMVP.",
    "Les tests statistiques presentes ici ne constituent pas une preuve cryptographique.",
    "Module-LWR et Multiplexed Sponge ne sont pas presentes comme des DRBG NIST approuves.",
]


def build_validation_metadata(*, context: str, mode: str, parameters: dict[str, Any]) -> dict[str, Any]:
    """Construit des metadonnees homogenes pour les rapports experimentaux."""

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "context": context,
        "mode": mode,
        "parameters": parameters,
        "implemented_scope": DISCLAIMER_IMPLEMENTED,
        "nist_inspired_scope": DISCLAIMER_INSPIRED,
        "non_compliance_scope": DISCLAIMER_NOT_FORMAL,
        "labels": [
            "validation experimentale",
            "inspire par SP 800-22",
            "inspire par SP 800-90B",
            "non conforme NIST",
        ],
    }


def export_json_report(report: dict[str, Any], output_path: str | Path) -> Path:
    """Exporte un rapport JSON lisible."""

    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")
    return target


def render_markdown_summary(report: dict[str, Any]) -> str:
    """Produit un resume Markdown concis et exploitable dans le memoire."""

    metadata = report.get("metadata", {})
    lines = [
        "# Validation experimentale",
        "",
        f"- Contexte: {metadata.get('context', 'unknown')}",
        f"- Mode: {metadata.get('mode', 'unknown')}",
        f"- Date UTC: {metadata.get('generated_at_utc', 'unknown')}",
        "",
        "## Portee",
        "",
        "### Implemente",
    ]

    for item in metadata.get("implemented_scope", []):
        lines.append(f"- {item}")

    lines.extend(["", "### Inspire par NIST"])
    for item in metadata.get("nist_inspired_scope", []):
        lines.append(f"- {item}")

    lines.extend(["", "### Non conformite formelle"])
    for item in metadata.get("non_compliance_scope", []):
        lines.append(f"- {item}")

    comparison = report.get("comparison", {})
    if comparison:
        lines.extend(["", "## Comparaison"])
        for engine_name, engine_summary in comparison.items():
            lines.append(f"- {engine_name}: {engine_summary}")

    return "\n".join(lines) + "\n"


def export_markdown_summary(report: dict[str, Any], output_path: str | Path) -> Path:
    """Exporte un resume Markdown."""

    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_markdown_summary(report), encoding="utf-8")
    return target
