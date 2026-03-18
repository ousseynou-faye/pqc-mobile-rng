"""Educational permutation used by the prototype sponge state."""

from __future__ import annotations


def _rotl(x: int, r: int, size: int) -> int:
    """Rotate ``x`` to the left on a fixed ``size``-bit space."""

    mask = (1 << size) - 1
    r %= size
    return ((x << r) & mask) | ((x & mask) >> (size - r))


def default_permutation(state: int, size: int) -> int:
    """Apply a deterministic diffusion-oriented permutation to the sponge state.

    This is a pedagogical placeholder for the research prototype. It is kept
    deterministic and simple on purpose and must not be interpreted as the
    final production primitive.
    """

    if size <= 0:
        raise ValueError("size doit etre > 0.")

    mask = (1 << size) - 1
    x = state & mask

    x ^= _rotl(x, 7, size)
    x ^= x >> 11
    x = (x * 0x9E3779B185EBCA87) & mask
    x ^= _rotl(x, 13, size)
    x ^= x >> 17
    x = _rotl(x, 3, size)

    return x & mask
