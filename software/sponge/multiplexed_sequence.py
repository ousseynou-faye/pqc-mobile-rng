"""Multiplexed sequence implementation for the prototype sponge.

This module freezes the defining relation
``u_n = t_{n + phi(l, n)}`` while keeping preview operations non-destructive.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ..bit_utils import pack_bits
from ..lfsr.recurrence_sequences import RecurrenceSequence
from .phi_function import PhiFunction


@dataclass
class MultiplexedSequence:
    """Generate the multiplexed sequence defined by ``u_n = t_{n + phi(l, n)}``.

    Design choice kept explicit:
    - ``seq_t`` is never advanced by ``phi(l, n)`` in a destructive way;
    - the implementation previews ``t_{n + phi(l, n)}``, then advances
      ``seq_s`` and ``seq_t`` by exactly one step.
    """

    seq_s: RecurrenceSequence
    seq_t: RecurrenceSequence
    l: int
    phi_offsets: Optional[tuple[int, ...]] = None
    msb_first: bool = True
    phi: PhiFunction = field(init=False)

    def __post_init__(self) -> None:
        """Instantiate the phi selector bound to ``seq_s``."""

        self.phi = PhiFunction(
            sequence_s=self.seq_s,
            l=self.l,
            offsets=self.phi_offsets,
            msb_first=self.msb_first,
        )

    def next_bit(self) -> int:
        """Return the next multiplexed bit and advance both source sequences."""

        shift = self.phi.compute()
        bit = self.seq_t.peek_bit(offset=shift % self.seq_t.period)

        self.seq_s.advance(1)
        self.seq_t.advance(1)

        return bit

    def generate_bits(self, n: int) -> list[int]:
        """Generate ``n`` multiplexed bits destructively."""

        if n < 0:
            raise ValueError("n doit etre >= 0.")
        return [self.next_bit() for _ in range(n)]

    def next_block(self, block_size: int, msb_first: bool = True) -> int:
        """Generate one integer block from the multiplexed bit stream.

        Convention:
        - ``msb_first=True`` means the first generated bit becomes the most
          significant bit of the block;
        - ``msb_first=False`` means the first generated bit becomes the least
          significant bit.
        """

        if block_size <= 0:
            raise ValueError("block_size doit etre > 0.")

        bits = [self.next_bit() for _ in range(block_size)]
        return pack_bits(bits, msb_first=msb_first)

    def generate_bytes(self, n: int, msb_first: bool = True) -> bytes:
        """Generate ``n`` bytes from the multiplexed sequence.

        Each byte is formed from eight successive multiplexed bits according to
        the requested bit order.
        """

        if n < 0:
            raise ValueError("n doit etre >= 0.")

        out = bytearray()
        for _ in range(n):
            out.append(self.next_block(8, msb_first=msb_first))
        return bytes(out)
