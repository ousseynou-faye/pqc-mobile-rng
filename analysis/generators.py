"""Je rassemble ici les fonctions utilitaires qui produisent des bits a analyser."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any


def _validate_bits(bits: Iterable[int]) -> list[int]:
    """Je verifie que l'echantillon contient uniquement des bits 0 ou 1."""

    validated = [int(bit) for bit in bits]
    if any(bit not in (0, 1) for bit in validated):
        raise ValueError("Je demande un echantillon binaire compose uniquement de 0 et de 1.")
    return validated


def bits_from_iterable(bits: Iterable[int]) -> list[int]:
    """J'utilise cette fonction pour figer un iterable de bits en liste verifiee."""

    return _validate_bits(bits)


def bits_from_object(source: Any, n_bits: int) -> list[int]:
    """Je genere un echantillon de bits depuis un objet deja present dans le prototype.

    Je privilegie d'abord une methode ``generate_bits`` si elle existe.
    Sinon, je me rabats sur des appels repetes a ``next_bit``.
    """

    if n_bits < 0:
        raise ValueError("Je demande un nombre de bits n_bits >= 0.")

    if hasattr(source, "generate_bits"):
        return _validate_bits(source.generate_bits(n_bits))

    if hasattr(source, "next_bit"):
        return _validate_bits(source.next_bit() for _ in range(n_bits))

    raise TypeError("Je ne sais pas extraire des bits depuis cet objet.")


def bits_from_sponge(sponge: Any, n_bits: int) -> list[int]:
    """J'utilise cette fonction pour extraire directement des bits depuis un sponge."""

    if not hasattr(sponge, "squeeze_bits"):
        raise TypeError("Je demande un objet compatible avec la methode squeeze_bits.")
    return _validate_bits(sponge.squeeze_bits(n_bits))


def bits_to_string(bits: Sequence[int]) -> str:
    """Je convertis un echantillon binaire en chaine compacte pour certaines analyses."""

    validated = _validate_bits(bits)
    return "".join(str(bit) for bit in validated)
