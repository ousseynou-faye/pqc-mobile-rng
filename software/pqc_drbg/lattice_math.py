from __future__ import annotations
from hashlib import shake_256
from typing import List

"""Je regroupe ici les opérations arithmétiques utiles au prototype Module-LWR."""

Vector = List[List[int]]
Matrix = List[List[List[int]]]


def polynomial_add(a: List[int], b: List[int], q: int) -> List[int]:
    if len(a) != len(b):
        raise ValueError("Les deux polynômes doivent avoir la même taille.")
    return [((x + y) % q) for x, y in zip(a, b)]


def polynomial_mul_mod_xn1(a: List[int], b: List[int], q: int) -> List[int]:
    if len(a) != len(b):
        raise ValueError("Les polynômes doivent avoir la même longueur.")
    n = len(a)
    out = [0] * n
    for i, ai in enumerate(a):
        for j, bj in enumerate(b):
            idx = i + j
            coeff = ai * bj
            if idx < n:
                out[idx] += coeff
            else:
                out[idx - n] -= coeff
    return [x % q for x in out]


def matrix_vector_mul(matrix_a: Matrix, vector_s: Vector, q: int) -> Vector:
    k = len(matrix_a)
    if k != len(vector_s):
        raise ValueError("La taille de la matrice et du vecteur doit être cohérente.")
    result: Vector = []
    for i in range(k):
        acc = [0] * len(vector_s[0])
        for j in range(k):
            prod = polynomial_mul_mod_xn1(matrix_a[i][j], vector_s[j], q)
            acc = polynomial_add(acc, prod, q)
        result.append(acc)
    return result


def apply_lwr_rounding(vector: Vector, p: int, q: int) -> Vector:
    if p <= 0 or q <= 0 or p >= q:
        raise ValueError("Je dois avoir 0 < p < q.")
    return [[((p * coeff) // q) % p for coeff in poly] for poly in vector]


def expand_seed_to_bytes(seed: bytes, nbytes: int, domain: bytes = b"") -> bytes:
    if nbytes < 0:
        raise ValueError("nbytes doit être >= 0.")
    return shake_256(domain + seed).digest(nbytes)


def sample_ternary_vector(seed: bytes, k: int, n: int, bound: int = 1) -> Vector:
    if bound != 1:
        raise ValueError("Ce prototype gère ici uniquement le cas ternaire {-1,0,1}.")
    raw = expand_seed_to_bytes(seed, k * n, domain=b"sample_ternary:")
    out: Vector = []
    idx = 0
    for _ in range(k):
        poly = []
        for _ in range(n):
            value = raw[idx] % 3
            idx += 1
            poly.append(-1 if value == 0 else 0 if value == 1 else 1)
        out.append(poly)
    return out


def seed_to_matrix(seed_a: bytes, k: int, n: int, q: int) -> Matrix:
    needed = k * k * n * 2
    raw = expand_seed_to_bytes(seed_a, needed, domain=b"matrix_a:")
    idx = 0
    matrix: Matrix = []
    for _ in range(k):
        row = []
        for _ in range(k):
            poly = []
            for _ in range(n):
                coeff = ((raw[idx] << 8) | raw[idx + 1]) % q
                idx += 2
                poly.append(coeff)
            row.append(poly)
        matrix.append(row)
    return matrix


def encode_vector(vector: Vector, modulus: int) -> bytes:
    out = bytearray()
    for poly in vector:
        for coeff in poly:
            c = coeff % modulus
            out.extend(int(c).to_bytes(2, 'big'))
    return bytes(out)
