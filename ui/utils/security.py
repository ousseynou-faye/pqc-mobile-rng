from __future__ import annotations

from typing import Any


def preview_bytes(data: bytes | None, *, head: int = 8, tail: int = 8) -> str:
    if not data:
        return "(vide)"
    blob = bytes(data)
    if len(blob) <= head + tail:
        return blob.hex()
    return f"{blob[:head].hex()}...{blob[-tail:].hex()} ({len(blob)} B)"


def preview_bits(data: bytes | None, *, max_bits: int = 64) -> str:
    if not data:
        return "(vide)"
    bits = "".join(f"{byte:08b}" for byte in bytes(data))
    if len(bits) <= max_bits:
        return bits
    return f"{bits[:max_bits]}..."


def truncate_text(text: str | None, *, limit: int = 120) -> str:
    if not text:
        return ""
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


def redact_state_payload(payload: dict[str, Any] | None) -> dict[str, Any]:
    if not payload:
        return {}
    redacted = dict(payload)
    for key in ("lwr_private_state", "sponge_private_state", "seedinit", "raw_data", "toeplitz_seed"):
        if key in redacted:
            redacted[key] = "<masque>"
    return redacted
