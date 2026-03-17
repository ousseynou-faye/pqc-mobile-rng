from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ..lfsr.recurrence_sequences import RecurrenceSequence
from .phi_function import PhiFunction


@dataclass
class MultiplexedSequence:
    """
    Implémente correctement :
        u_n = t_{n + phi(l,n)}

    Point essentiel :
    - on NE décale PAS réellement seq_t de "shift" pas de façon destructive ;
    - on lit le bit t_{n+shift} par anticipation (peek),
      puis on avance seq_s et seq_t d'un seul pas.
    """

    seq_s: RecurrenceSequence
    seq_t: RecurrenceSequence
    l: int
    phi_offsets: Optional[tuple[int, ...]] = None
    msb_first: bool = True
    phi: PhiFunction = field(init=False)

    def __post_init__(self) -> None: # Initialisation de la fonction phi après que les autres champs soient initialisés.
        self.phi = PhiFunction(
            sequence_s=self.seq_s,
            l=self.l,
            offsets=self.phi_offsets,
            msb_first=self.msb_first,
        )

    def next_bit(self) -> int:
        shift = self.phi.compute()
        bit = self.seq_t.peek_bit(offset=shift % self.seq_t.period)

        # Passage à l'itération suivante : n -> n+1
        self.seq_s.advance(1)
        self.seq_t.advance(1)

        return bit

    def generate_bits(self, n: int) -> list[int]:
        if n < 0:
            raise ValueError("n doit être >= 0.")
        return [self.next_bit() for _ in range(n)]

    def next_block(self, block_size: int, msb_first: bool = True) -> int:
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

    def generate_bytes(self, n: int, msb_first: bool = True) -> bytes:
        if n < 0:
            raise ValueError("n doit être >= 0.")

        out = bytearray()
        for _ in range(n):
            out.append(self.next_block(8, msb_first=msb_first))
        return bytes(out)