"""
./software/lfsr/lfsr_core.py

Implémentation du moteur LFSR utilisé dans le RNG
Mobile Post-Quantique.

Fonctionnalités :
- génération de bits
- génération de bytes
- mise à jour du registre
- reseeding

Dépendances :
primitive_polynomials.py
"""

from .primitive_polynomials import get_polynomial


class LFSR:

    def __init__(self, degree: int, seed: int):

        poly = get_polynomial(degree)

        self.degree = degree
        self.taps = poly.taps
        self.state = seed & ((1 << degree) - 1)

        if self.state == 0:
            raise ValueError("Seed invalide (état nul interdit)")

    # -----------------------------------------------------

    def _feedback(self): 

        feedback = 0

        for tap in self.taps:

            bit = (self.state >> (self.degree - tap)) & 1
            feedback ^= bit

        return feedback

    # -----------------------------------------------------
    
    def max_period(self):
        return (1 << self.degree) - 1
    
    # -----------------------------------------------------

    def step(self): 

        feedback = self._feedback()

        output = (self.state >> (self.degree - 1)) & 1

        self.state >>= 1
        self.state |= (feedback << (self.degree - 1))

        return output

    # -----------------------------------------------------

    def generate_bits(self, n):

        result = []

        for _ in range(n):
            result.append(self.step())

        return result

    # -----------------------------------------------------

    def generate_bytes(self, n):

        data = bytearray()

        for _ in range(n):

            byte = 0

            for i in range(8):
                bit = self.step()
                byte |= bit << i

            data.append(byte)

        return bytes(data)

    # -----------------------------------------------------

    def reseed(self, new_seed):

        self.state = new_seed & ((1 << self.degree) - 1)

        if self.state == 0:
            raise ValueError("Seed invalide")