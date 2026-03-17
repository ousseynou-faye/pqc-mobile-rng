from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .lfsr_core import LFSR


@dataclass
class RecurrenceSequence:
    """
    Façade propre autour du LFSR pour le prototype mathématique.
    """

    degree: int
    seed: int
    taps: Optional[tuple[int, ...]] = None

    def __post_init__(self) -> None:
        self.lfsr = LFSR(degree=self.degree, seed=self.seed, taps=self.taps)

    @property # Expose la période maximale du LFSR, qui est aussi la période de la suite générée.
    def period(self) -> int:
        return self.lfsr.max_period()

    def clone(self) -> "RecurrenceSequence":
        return RecurrenceSequence(
            degree=self.degree,
            seed=self.lfsr.state,
            taps=self.lfsr.taps,
        )

    def next_bit(self) -> int:
        return self.lfsr.step() 

    def advance(self, steps: int) -> None:
        self.lfsr.advance(steps)

    def peek_bit(self, offset: int = 0) -> int:
        # Réduction modulo la période pour rester sur la suite cyclique.
        offset %= self.period
        return self.lfsr.peek_bit(offset=offset)

    def peek_bits(self, length: int, start_offset: int = 0) -> list[int]:
        if length < 0:
            raise ValueError("length doit être >= 0.")
        return [self.peek_bit(start_offset + i) for i in range(length)]

    def generate_sequence(self, length: int) -> list[int]:
        if length < 0:
            raise ValueError("length doit être >= 0.")
        return [self.next_bit() for _ in range(length)]

    def generate_block(self, block_size: int, msb_first: bool = True) -> int:
        if block_size <= 0:
            raise ValueError("block_size doit être > 0.")

        bits = [self.next_bit() for _ in range(block_size)]

        value = 0
        if msb_first:
            for bit in bits:
                value = (value << 1) | bit
        else:
            for i, bit in enumerate(bits):
                value |= bit << i
        return value

    def peek_block(self, block_size: int, start_offset: int = 0, msb_first: bool = True) -> int:
        if block_size <= 0:
            raise ValueError("block_size doit être > 0.")

        bits = self.peek_bits(block_size, start_offset=start_offset)

        value = 0
        if msb_first:
            for bit in bits:
                value = (value << 1) | bit
        else:
            for i, bit in enumerate(bits):
                value |= bit << i
        return value

    def get_state(self) -> int:
        return self.lfsr.state

    def reseed(self, new_seed: int) -> None:
        self.lfsr.reseed(new_seed)