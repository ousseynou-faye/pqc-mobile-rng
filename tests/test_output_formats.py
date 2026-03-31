from __future__ import annotations

import pytest

from software.api.output_formats import format_output_bytes, group_bits, to_binary, to_decimal, to_hex


def test_output_conversions_are_deterministic_big_endian():
    sample = b"\x00\x01\x02"

    assert to_decimal(sample) == 258
    assert to_decimal(sample) == 258
    assert to_hex(sample) == "000102"
    assert to_binary(sample) == "000000000000000100000010"


def test_format_output_bytes_includes_all_expected_views():
    sample = b"\x01\x23\x45"

    bundle = format_output_bytes(sample)

    assert bundle["raw_bytes"] == sample
    assert bundle["raw_byte_values"] == [1, 35, 69]
    assert bundle["length_bytes"] == 3
    assert bundle["length_bits"] == 24
    assert bundle["byteorder"] == "big"
    assert bundle["hex"] == "012345"
    assert bundle["decimal"] == int.from_bytes(sample, "big")
    assert bundle["binary_grouped"] == "00000001 00100011 01000101"


def test_same_and_different_inputs_map_as_expected_in_decimal():
    left = b"\x12\x34\x56"
    right = b"\x12\x34\x57"

    assert to_decimal(left) == to_decimal(left)
    assert to_decimal(left) != to_decimal(right)


def test_group_bits_rejects_invalid_inputs():
    with pytest.raises(ValueError):
        group_bits("", group_size=8)
    with pytest.raises(ValueError):
        group_bits("1010", group_size=0)


def test_output_conversions_reject_empty_or_invalid_inputs():
    with pytest.raises(ValueError):
        to_decimal(b"")
    with pytest.raises(ValueError):
        to_hex(b"")
    with pytest.raises(ValueError):
        to_binary(b"")
    with pytest.raises(TypeError):
        to_decimal("abc")  # type: ignore[arg-type]
