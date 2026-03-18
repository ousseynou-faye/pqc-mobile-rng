"""Recurrence sequence facade built on top of the project LFSR core.

The class exposes a pedagogical interface used by ``phi(l, n)``,
``MultiplexedSequence`` and the sponge orchestration layer. Peek methods are
explicitly non-destructive.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..bit_utils import pack_bits
from .lfsr_core import LFSR


@dataclass
class RecurrenceSequence:
    """Pedagogical wrapper exposing a binary recurrence sequence interface."""

    degree: int
    seed: int
    taps: Optional[tuple[int, ...]] = None

    def __post_init__(self) -> None:
        """Instantiate the underlying LFSR with the requested parameters."""

        self.lfsr = LFSR(degree=self.degree, seed=self.seed, taps=self.taps)

    @property
    def period(self) -> int:
        """Return the period associated with the configured LFSR."""

        return self.lfsr.max_period()

    def clone(self) -> "RecurrenceSequence":
        """Return an independent copy carrying the same current state."""

        return RecurrenceSequence(
            degree=self.degree,
            seed=self.lfsr.state,
            taps=self.lfsr.taps,
        )

    def next_bit(self) -> int:
        """Return the next emitted bit and advance the sequence by one step."""

        return self.lfsr.step()

    def advance(self, steps: int) -> None:
        """Advance the sequence by ``steps`` transitions."""

        self.lfsr.advance(steps)

    def peek_bit(self, offset: int = 0) -> int:
        """Preview one future bit without consuming the sequence.

        Offsets are reduced modulo the period so that the preview remains on the
        cyclic recurrence sequence.
        """

        offset %= self.period
        return self.lfsr.peek_bit(offset=offset)

    def peek_bits(self, length: int, start_offset: int = 0) -> list[int]:
        """Preview a contiguous future bit window without state mutation."""

        if length < 0:
            raise ValueError("length doit etre >= 0.")
        return [self.peek_bit(start_offset + i) for i in range(length)]

    def generate_sequence(self, length: int) -> list[int]:
        """Generate ``length`` successive bits destructively."""

        if length < 0:
            raise ValueError("length doit etre >= 0.")
        return [self.next_bit() for _ in range(length)]

    def generate_block(self, block_size: int, msb_first: bool = True) -> int:
        """Generate one integer block from successive bits.

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

    def peek_block(
        self,
        block_size: int,
        start_offset: int = 0,
        msb_first: bool = True,
    ) -> int:
        """Preview one integer block without consuming the sequence."""

        if block_size <= 0:
            raise ValueError("block_size doit etre > 0.")

        bits = self.peek_bits(block_size, start_offset=start_offset)
        return pack_bits(bits, msb_first=msb_first)

    def get_state(self) -> int:
        """Return the current raw state of the underlying LFSR."""

        return self.lfsr.state

    def reseed(self, new_seed: int) -> None:
        """Reset the underlying sequence to a new non-zero seed."""

        self.lfsr.reseed(new_seed)
