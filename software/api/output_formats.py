from __future__ import annotations

"""Utilitaires canoniques de conversion et d'observabilite de sortie RNG."""

from typing import Any


DEFAULT_BYTEORDER = "big"


def _coerce_output_bytes(output_bytes: bytes | bytearray) -> bytes:
    if not isinstance(output_bytes, (bytes, bytearray)):
        raise TypeError("output_bytes doit etre de type bytes.")
    blob = bytes(output_bytes)
    if not blob:
        raise ValueError("output_bytes ne doit pas etre vide.")
    return blob


def _validate_byteorder(byteorder: str) -> str:
    normalized = byteorder.lower()
    if normalized not in {"big", "little"}:
        raise ValueError("byteorder doit valoir 'big' ou 'little'.")
    return normalized


def to_decimal(output_bytes: bytes | bytearray, *, byteorder: str = DEFAULT_BYTEORDER) -> int:
    """Convertit une sortie binaire en entier non signe."""

    blob = _coerce_output_bytes(output_bytes)
    return int.from_bytes(blob, _validate_byteorder(byteorder), signed=False)


def to_hex(output_bytes: bytes | bytearray) -> str:
    """Retourne la representation hexadecimale continue, sans prefixe."""

    return _coerce_output_bytes(output_bytes).hex()


def to_binary(output_bytes: bytes | bytearray) -> str:
    """Retourne la representation binaire continue sur 8 bits par octet."""

    blob = _coerce_output_bytes(output_bytes)
    return "".join(f"{value:08b}" for value in blob)


def group_bits(binary_string: str, *, group_size: int = 8, separator: str = " ") -> str:
    """Groupe une chaine binaire en blocs lisibles."""

    if group_size <= 0:
        raise ValueError("group_size doit etre > 0.")
    if not binary_string:
        raise ValueError("binary_string ne doit pas etre vide.")
    return separator.join(
        binary_string[index:index + group_size]
        for index in range(0, len(binary_string), group_size)
    )


def format_output_bytes(
    output_bytes: bytes | bytearray,
    *,
    byteorder: str = DEFAULT_BYTEORDER,
    bit_group_size: int = 8,
) -> dict[str, Any]:
    """Construit une vue complete et stable d'une sortie RNG."""

    blob = _coerce_output_bytes(output_bytes)
    normalized_byteorder = _validate_byteorder(byteorder)
    binary = to_binary(blob)
    return {
        "raw_bytes": blob,
        "raw_bytes_repr": repr(blob),
        "raw_byte_values": list(blob),
        "length_bytes": len(blob),
        "length_bits": len(blob) * 8,
        "byteorder": normalized_byteorder,
        "hex": to_hex(blob),
        "binary": binary,
        "binary_grouped": group_bits(binary, group_size=bit_group_size),
        "decimal": to_decimal(blob, byteorder=normalized_byteorder),
    }

