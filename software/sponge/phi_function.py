from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..lfsr.recurrence_sequences import RecurrenceSequence


@dataclass
class PhiFunction:
    """
    Fonction phi(l, n).

    Remarque importante :
    le Multiplexed Sponge définit phi comme une fonction probabiliste obtenue
    par sélection de l bits dans S(N,l), mais sans imposer une seule
    règle algorithmique de codage.

    Convention retenue pour ce prototype :
    - si offsets est None :
        phi lit une fenêtre contiguë de l bits à partir de la position courante
    - si offsets est fourni :
        phi lit les bits aux décalages explicitement demandés
    """

    sequence_s: RecurrenceSequence
    l: int
    offsets: Optional[tuple[int, ...]] = None
    msb_first: bool = True

    def __post_init__(self) -> None:
        if self.l <= 0:
            raise ValueError("l doit être > 0.")

        if self.offsets is not None:
            self.offsets = tuple(int(o) for o in self.offsets)
            if len(self.offsets) != self.l:
                raise ValueError("La taille de offsets doit être égale à l.")
            if any(o < 0 for o in self.offsets):
                raise ValueError("Tous les offsets doivent être >= 0.")

    def compute(self) -> int:
        if self.offsets is None: # Lecture d'une fenêtre contiguë de l bits à partir de la position courante.
            bits = self.sequence_s.peek_bits(self.l, start_offset=0)
        else:
            bits = [self.sequence_s.peek_bit(offset=o) for o in self.offsets]

        if not self.msb_first:
            bits = list(reversed(bits)) # On inverse l'ordre des bits pour que le bit à offset 0 soit le LSB.

        value = 0
        for bit in bits:
            value = (value << 1) | bit 

        return value