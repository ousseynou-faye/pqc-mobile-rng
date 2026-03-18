"""Shared bit-packing helpers for the research prototype.

This module centralises the bit-order conventions used by the LFSR and
Multiplexed Sponge code. The objective is not to change the mathematical
behaviour of the prototype, but to make the conventions explicit and reused
consistently.
"""

from __future__ import annotations

from typing import Iterable


def pack_bits(bits: Iterable[int], msb_first: bool = True) -> int:
    """Pack an ordered iterable of bits into an integer."""

    value = 0
    if msb_first:
        for bit in bits:
            if bit not in (0, 1):
                raise ValueError("Each element in bits must be 0 or 1.")
            value = (value << 1) | bit
        return value

    for index, bit in enumerate(bits):
        if bit not in (0, 1):
            raise ValueError("Each element in bits must be 0 or 1.")
        value |= bit << index
    return value
