from __future__ import annotations

from pathlib import Path
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def section(title: str, lines: Iterable[str]) -> str:
    body = "\n".join(lines)
    return f"=== {title} ===\n{body}".rstrip()


def join_sections(*blocks: str) -> str:
    return "\n\n".join(block for block in blocks if block)


def format_int_list(values: list[int]) -> str:
    return ", ".join(str(value) for value in values)
