"""Binary LFSR core used by the Multiplexed Sponge prototype.

Bit convention used throughout this module:
- the internal state is stored as an integer on ``degree`` bits;
- the output bit of one step is the current most significant bit (MSB);
- the register shifts to the right at each step;
- the feedback bit is inserted back into the MSB position.

This convention is preserved as-is because the existing tests and prototype
logic already depend on it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..bit_utils import pack_bits
from .primitive_polynomials import get_polynomial


@dataclass
class LFSR:
    """Mutable binary LFSR with explicit MSB-oriented stepping semantics."""

    degree: int
    seed: int
    taps: Optional[tuple[int, ...]] = None

    def __post_init__(self) -> None:
        """Validate the configuration and initialise the masked internal state."""

        if self.degree <= 0:
            raise ValueError("degree doit etre strictement positif.")

        if self.taps is None:
            poly = get_polynomial(self.degree)
            self.taps = tuple(poly.taps)
        else:
            self.taps = tuple(int(t) for t in self.taps)

        if any(t < 1 or t > self.degree for t in self.taps):
            raise ValueError("Tous les taps doivent etre dans [1, degree].")

        self.mask = (1 << self.degree) - 1
        self.state = self.seed & self.mask

        if self.state == 0:
            raise ValueError("Seed invalide : l'etat nul est interdit.")

    def clone(self) -> "LFSR":
        """Return a new LFSR carrying the exact current state and tap set."""

        return LFSR(degree=self.degree, seed=self.state, taps=self.taps)

    def snapshot(self) -> int:
        """Return the current raw integer state."""

        return self.state

    def restore(self, snapshot: int) -> None:
        """Restore a previously captured raw state."""

        self.state = snapshot & self.mask
        if self.state == 0:
            raise ValueError("Snapshot invalide : l'etat nul est interdit.")

    def max_period(self) -> int:
        """Return the maximal period associated with a primitive polynomial."""

        return (1 << self.degree) - 1

    def _feedback(self) -> int:
        """Compute the feedback bit from the configured taps."""

        feedback = 0
        for tap in self.taps:
            bit = (self.state >> (self.degree - tap)) & 1
            feedback ^= bit
        return feedback & 1

    def step(self) -> int:
        """Advance the register by one step and return the emitted MSB bit."""

        output = (self.state >> (self.degree - 1)) & 1
        feedback = self._feedback()

        self.state >>= 1
        self.state |= feedback << (self.degree - 1)
        self.state &= self.mask

        return output

    def advance(self, steps: int) -> None:
        """Advance the LFSR by ``steps`` transitions."""

        if steps < 0:
            raise ValueError("steps doit etre >= 0.")
        for _ in range(steps):
            self.step()

    def peek_bit(self, offset: int = 0) -> int:
        """Return the bit emitted after ``offset`` future steps without mutation."""

        if offset < 0:
            raise ValueError("offset doit etre >= 0.")

        tmp = self.clone()
        tmp.advance(offset)
        return tmp.step()

    def peek_bits(self, length: int, start_offset: int = 0) -> list[int]:
        """Preview a contiguous future bit window without changing the state."""

        if length < 0:
            raise ValueError("length doit etre >= 0.")
        if start_offset < 0:
            raise ValueError("start_offset doit etre >= 0.")

        tmp = self.clone()
        tmp.advance(start_offset)
        return [tmp.step() for _ in range(length)]

    def generate_bits(self, n: int) -> list[int]:
        """Generate ``n`` successive output bits destructively."""

        if n < 0:
            raise ValueError("n doit etre >= 0.")
        return [self.step() for _ in range(n)]

    def generate_bytes(self, n: int, lsb_first: bool = True) -> bytes:
        """Generate ``n`` bytes directly from successive LFSR bits.

        Historical convention preserved for compatibility:
        - when ``lsb_first=True`` (default), the first emitted bit becomes bit 0
          of the output byte;
        - when ``lsb_first=False``, the first emitted bit becomes bit 7.
        """

        if n < 0:
            raise ValueError("n doit etre >= 0.")

        data = bytearray()
        for _ in range(n):
            bits = [self.step() for _ in range(8)]
            data.append(pack_bits(bits, msb_first=not lsb_first))

        return bytes(data)

    def reseed(self, new_seed: int) -> None:
        """Replace the current state with a new non-zero seed."""

        self.state = new_seed & self.mask
        if self.state == 0:
            raise ValueError("Seed invalide : l'etat nul est interdit.")
