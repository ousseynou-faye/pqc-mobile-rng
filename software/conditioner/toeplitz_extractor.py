from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


def bits_from_bytes(data: bytes, *, msb_first: bool = True) -> List[int]:
    """
    Je convertis ici une suite d'octets en liste de bits.

    Convention retenue :
    - par défaut, je lis les bits du plus significatif vers le moins significatif ;
    - cela me permet de garder une convention stable dans toute la couche COND.

    Exemple :
    0xA0 -> [1, 0, 1, 0, 0, 0, 0, 0] si `msb_first=True`.
    """
    bits: List[int] = []

    for byte in data:
        if msb_first:
            for shift in range(7, -1, -1):
                bits.append((byte >> shift) & 1)
        else:
            for shift in range(0, 8):
                bits.append((byte >> shift) & 1)

    return bits


def bytes_from_bits(bits: Iterable[int], *, msb_first: bool = True) -> bytes:
    """
    Je regroupe ici une liste de bits en octets.

    Si le nombre de bits n'est pas multiple de 8, je complète le dernier octet
    avec des zéros.

    Convention retenue :
    - par défaut, le premier bit rencontré devient le bit de poids fort de l'octet.
    """
    normalized = [int(bit) & 1 for bit in bits]
    out = bytearray()

    for i in range(0, len(normalized), 8):
        chunk = normalized[i:i + 8]
        if len(chunk) < 8:
            chunk = chunk + [0] * (8 - len(chunk))

        value = 0
        if msb_first:
            for bit in chunk:
                value = (value << 1) | bit
        else:
            for idx, bit in enumerate(chunk):
                value |= bit << idx

        out.append(value)

    return bytes(out)


def _parity(x: int) -> int:
    """
    Je calcule ici la parité binaire de `x`.

    La sortie vaut :
    - 0 si le nombre de bits à 1 est pair,
    - 1 sinon.

    Cette fonction me sert à calculer rapidement un produit matriciel sur GF(2).
    """
    return x.bit_count() & 1


@dataclass(frozen=True)
class ToeplitzExtractor:
    """
    J'implémente ici un extracteur de Toeplitz binaire sur GF(2).

    Idée mathématique :
    - je considère une matrice T de taille (m x n) ;
    - cette matrice est entièrement définie par ses diagonales ;
    - je calcule Y = T * X sur GF(2), où X est l'entropie brute binaire.

    Pourquoi ce choix :
    - il correspond à ton chapitre 4 ;
    - il permet une extraction d'aléa plus rigoureuse qu'un simple mélange ad hoc ;
    - il prépare correctement le `Seedinit` avant le DRBG.

    Convention de représentation de la matrice :
    - je fournis `seed_bits` de longueur `input_bits + output_bits - 1` ;
    - l'élément T[i, j] vaut `seed_bits[(j - i) + (output_bits - 1)]`.
    """

    input_bits: int
    output_bits: int
    seed_bits: tuple[int, ...]

    def __post_init__(self) -> None:
        if self.input_bits <= 0:
            raise ValueError("input_bits doit être > 0.")
        if self.output_bits <= 0:
            raise ValueError("output_bits doit être > 0.")

        expected = self.seed_length_bits(self.input_bits, self.output_bits)
        if len(self.seed_bits) != expected:
            raise ValueError(
                f"seed_bits doit contenir exactement {expected} bits pour cette matrice."
            )
        if any(bit not in (0, 1) for bit in self.seed_bits):
            raise ValueError("seed_bits doit être une suite de bits 0/1.")

    @staticmethod
    def seed_length_bits(input_bits: int, output_bits: int) -> int:
        """
        Je retourne ici le nombre de bits nécessaires pour définir entièrement
        une matrice de Toeplitz de taille (output_bits x input_bits).
        """
        if input_bits <= 0 or output_bits <= 0:
            raise ValueError("input_bits et output_bits doivent être > 0.")
        return input_bits + output_bits - 1

    @classmethod
    def from_seed_bytes(
        cls,
        *,
        input_bits: int,
        output_bits: int,
        seed_bytes: bytes,
        msb_first: bool = True,
    ) -> "ToeplitzExtractor":
        """
        Je construis ici l'extracteur à partir d'une suite d'octets.

        Si `seed_bytes` contient plus de bits que nécessaire, je tronque.
        Si elle en contient moins, je lève une erreur.
        """
        seed_bits = bits_from_bytes(seed_bytes, msb_first=msb_first)
        expected = cls.seed_length_bits(input_bits, output_bits)

        if len(seed_bits) < expected:
            raise ValueError(
                "seed_bytes ne contient pas assez de bits pour paramétrer la matrice de Toeplitz."
            )

        return cls(
            input_bits=input_bits,
            output_bits=output_bits,
            seed_bits=tuple(seed_bits[:expected]),
        )

    def _row_mask(self, row_index: int) -> int:
        """
        Je construis ici le masque binaire correspondant à une ligne de la matrice.

        Ce masque me permet ensuite de calculer le bit de sortie comme une parité
        de l'intersection entre :
        - la ligne de Toeplitz,
        - le vecteur d'entrée.
        """
        if not (0 <= row_index < self.output_bits):
            raise IndexError("row_index hors bornes.")

        mask = 0
        for col in range(self.input_bits):
            value = self.seed_bits[(col - row_index) + (self.output_bits - 1)]
            if value:
                mask |= 1 << (self.input_bits - 1 - col)

        return mask

    def extract_bits(self, raw_bits: Iterable[int]) -> List[int]:
        """
        J'applique ici l'extracteur sur une entrée binaire `raw_bits`.

        Hypothèse :
        - `raw_bits` doit contenir exactement `input_bits` bits.
        """
        bits = [int(bit) & 1 for bit in raw_bits]
        if len(bits) != self.input_bits:
            raise ValueError(
                f"Je dois recevoir exactement {self.input_bits} bits d'entrée."
            )

        x = 0
        for bit in bits:
            x = (x << 1) | bit

        out: List[int] = []
        for row in range(self.output_bits):
            mask = self._row_mask(row)
            out.append(_parity(x & mask))

        return out

    def extract_bytes(self, raw_bytes: bytes, *, msb_first: bool = True) -> bytes:
        """
        J'applique ici l'extracteur directement sur des octets.

        Attention :
        - le nombre de bits utiles de `raw_bytes` doit correspondre à `input_bits` ;
        - si `raw_bytes` contient plus de bits, je tronque ;
        - si `raw_bytes` n'en contient pas assez, je refuse l'opération.
        """
        raw_bits = bits_from_bytes(raw_bytes, msb_first=msb_first)

        if len(raw_bits) < self.input_bits:
            raise ValueError(
                "raw_bytes ne contient pas assez de bits pour la taille d'entrée demandée."
            )

        raw_bits = raw_bits[: self.input_bits]
        return bytes_from_bits(self.extract_bits(raw_bits), msb_first=msb_first)
