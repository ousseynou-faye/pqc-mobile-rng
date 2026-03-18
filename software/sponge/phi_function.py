"""Definition of the prototype phi(l, n) selector.

The implementation keeps the mathematical relation intentionally simple:
``phi(l, n)`` is derived from bits previewed from the current state of the
recurrence sequence ``s`` without consuming it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..bit_utils import pack_bits
from ..lfsr.recurrence_sequences import RecurrenceSequence


@dataclass
class PhiFunction:
    """Prototype implementation of ``phi(l, n)``.

    Conventions:
    - if ``offsets`` is ``None``, phi reads a contiguous window of ``l`` bits
      starting at the current index of sequence ``s``;
    - otherwise phi reads the bits at the explicit offsets provided in
      ``offsets``;
    - ``msb_first=True`` means the first selected bit is the most significant
      bit of the resulting integer.

    The sequence is never consumed by ``compute()``.
    """

    sequence_s: RecurrenceSequence
    l: int
    offsets: Optional[tuple[int, ...]] = None
    msb_first: bool = True

    def __post_init__(self) -> None:
        """Validate ``l`` and the optional explicit offset schedule."""

        if self.l <= 0:
            raise ValueError("l doit etre > 0.")

        if self.offsets is not None:
            self.offsets = tuple(int(o) for o in self.offsets)
            if len(self.offsets) != self.l:
                raise ValueError("La taille de offsets doit etre egale a l.")
            if any(o < 0 for o in self.offsets):
                raise ValueError("Tous les offsets doivent etre >= 0.")

    def compute(self) -> int:
        """Compute the current value of ``phi(l, n)`` without mutating ``s``."""

        if self.offsets is None:
            bits = self.sequence_s.peek_bits(self.l, start_offset=0)
        else:
            bits = [self.sequence_s.peek_bit(offset=o) for o in self.offsets]

        return pack_bits(bits, msb_first=self.msb_first)
