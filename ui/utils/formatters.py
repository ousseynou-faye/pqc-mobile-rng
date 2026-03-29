from __future__ import annotations

from statistics import fmean
from typing import Any


def decimal_rows(data: bytes, *, limit: int | None = None) -> list[dict[str, Any]]:
    blob = list(bytes(data))
    if limit is not None:
        blob = blob[:limit]
    return [
        {
            "index": index,
            "decimal": value,
            "hex": f"0x{value:02x}",
            "binary": f"{value:08b}",
        }
        for index, value in enumerate(blob)
    ]


def byte_histogram(data: bytes) -> list[dict[str, Any]]:
    counts: dict[int, int] = {}
    for value in bytes(data):
        counts[value] = counts.get(value, 0) + 1
    return [{"byte": key, "count": counts[key]} for key in sorted(counts)]


def summarize_bytes(data: bytes) -> dict[str, Any]:
    blob = list(bytes(data))
    if not blob:
        return {
            "count": 0,
            "min": None,
            "max": None,
            "mean": None,
            "unique_values": 0,
        }
    return {
        "count": len(blob),
        "min": min(blob),
        "max": max(blob),
        "mean": round(fmean(blob), 3),
        "unique_values": len(set(blob)),
    }
