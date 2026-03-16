from __future__ import annotations


def _rotl(x: int, r: int, size: int) -> int:
    mask = (1 << size) - 1
    r %= size
    return ((x << r) & mask) | ((x & mask) >> (size - r))


def default_permutation(state: int, size: int) -> int:
    """
    Permutation éducative et déterministe pour le prototype mathématique.

    Important :
    - ce n'est pas encore la primitive finale de production ;
    - elle sert à modéliser la diffusion du sponge de manière propre.
    """

    if size <= 0:
        raise ValueError("size doit être > 0.")

    mask = (1 << size) - 1
    x = state & mask

    x ^= _rotl(x, 7, size)
    x ^= (x >> 11)
    x = (x * 0x9E3779B185EBCA87) & mask
    x ^= _rotl(x, 13, size)
    x ^= (x >> 17)
    x = _rotl(x, 3, size)

    return x & mask