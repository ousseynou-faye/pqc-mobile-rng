"""
./software/lfsr/recurrence_sequences.py

Génération des séquences de récurrence linéaire
basées sur LFSR.

Utilisé pour le Multiplexed Sponge RNG.
"""

from .lfsr_core import LFSR


class RecurrenceSequence:

    def __init__(self, degree, seed):

        self.lfsr = LFSR(degree, seed)
        self.degree = degree

    # -------------------------------------------------

    def next_bit(self):

        return self.lfsr.step()

    # -------------------------------------------------

    def generate_sequence(self, length):

        seq = []

        for _ in range(length):
            seq.append(self.next_bit())

        return seq

    # -------------------------------------------------

    def generate_block(self, block_size):

        block = 0

        for i in range(block_size):
            bit = self.next_bit()
            block |= bit << i

        return block

    # -------------------------------------------------

    def generate_blocks(self, block_size, n_blocks):

        blocks = []

        for _ in range(n_blocks):

            blocks.append(
                self.generate_block(block_size)
            )

        return blocks

    # -------------------------------------------------

    def get_state(self):

        return self.lfsr.state