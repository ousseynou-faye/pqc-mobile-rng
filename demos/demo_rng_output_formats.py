from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT_STR = str(PROJECT_ROOT)
if PROJECT_ROOT_STR not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_STR)

from demos.common import join_sections, section
from software.api.output_formats import format_output_bytes


def render_output_formats_demo(sample: bytes = b"\x00\x06\xcd\xef\x12\x34\x56\x78") -> str:
    bundle = format_output_bytes(sample)
    return join_sections(
        section(
            "FORMATS DE SORTIE",
            [
                f"Bytes: {bundle['raw_bytes_repr']}",
                f"Liste decimale des octets: {bundle['raw_byte_values']}",
                f"Longueur (octets): {bundle['length_bytes']}",
                f"Longueur (bits): {bundle['length_bits']}",
                f"Hex: {bundle['hex']}",
                f"Decimal: {bundle['decimal']}",
                f"Binaire: {bundle['binary']}",
                f"Binaire groupe: {bundle['binary_grouped']}",
                f"Endian utilise pour Decimal: {bundle['byteorder']}",
            ],
        )
    )


if __name__ == "__main__":
    print(render_output_formats_demo())
