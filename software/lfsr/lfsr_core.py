from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .primitive_polynomials import get_polynomial


@dataclass
class LFSR:
    """
    LFSR binaire à état mutable.

    Convention retenue :
    - sortie = bit de poids fort (MSB)
    - décalage à droite
    - rétroaction insérée sur le MSB

    Cette convention est cohérente et suffisante pour notre prototype mathématique.
    """

    degree: int
    seed: int
    taps: Optional[tuple[int, ...]] = None

    def __post_init__(self) -> None:
        if self.degree <= 0:
            raise ValueError("degree doit être strictement positif.")

        if self.taps is None:
            poly = get_polynomial(self.degree)
            self.taps = tuple(poly.taps)
        else:
            self.taps = tuple(int(t) for t in self.taps)

        if any(t < 1 or t > self.degree for t in self.taps):
            raise ValueError("Tous les taps doivent être dans [1, degree].")

        self.mask = (1 << self.degree) - 1
        self.state = self.seed & self.mask

        if self.state == 0:
            raise ValueError("Seed invalide : l'état nul est interdit.")

    def clone(self) -> "LFSR":
        return LFSR(degree=self.degree, seed=self.state, taps=self.taps)

    def snapshot(self) -> int:
        return self.state

    def restore(self, snapshot: int) -> None:
        self.state = snapshot & self.mask
        if self.state == 0:
            raise ValueError("Snapshot invalide : l'état nul est interdit.")

    def max_period(self) -> int:
        # Valable si les taps correspondent bien à un polynôme primitif.
        return (1 << self.degree) - 1

    def _feedback(self) -> int:
        feedback = 0
        for tap in self.taps:
            bit = (self.state >> (self.degree - tap)) & 1
            feedback ^= bit
        return feedback & 1

    def step(self) -> int:
        output = (self.state >> (self.degree - 1)) & 1
        feedback = self._feedback()

        self.state >>= 1
        self.state |= (feedback << (self.degree - 1))
        self.state &= self.mask

        return output

    def advance(self, steps: int) -> None:
        if steps < 0:
            raise ValueError("steps doit être >= 0.")
        for _ in range(steps):
            self.step()

    def peek_bit(self, offset: int = 0) -> int:
        if offset < 0:
            raise ValueError("offset doit être >= 0.")

        tmp = self.clone()
        tmp.advance(offset)
        return tmp.step()

    def peek_bits(self, length: int, start_offset: int = 0) -> list[int]:
        if length < 0:
            raise ValueError("length doit être >= 0.")
        if start_offset < 0:
            raise ValueError("start_offset doit être >= 0.")

        tmp = self.clone()
        tmp.advance(start_offset)
        return [tmp.step() for _ in range(length)]

    def generate_bits(self, n: int) -> list[int]:
        if n < 0:
            raise ValueError("n doit être >= 0.")
        return [self.step() for _ in range(n)]

    def generate_bytes(self, n: int, lsb_first: bool = True) -> bytes:
        if n < 0:
            raise ValueError("n doit être >= 0.")

        data = bytearray()

        for _ in range(n):
            byte = 0
            if lsb_first:
                for i in range(8):
                    byte |= self.step() << i
            else:
                for _ in range(8):
                    byte = (byte << 1) | self.step()
            data.append(byte)

        return bytes(data)

    def reseed(self, new_seed: int) -> None:
        self.state = new_seed & self.mask
        if self.state == 0:
            raise ValueError("Seed invalide : l'état nul est interdit.")