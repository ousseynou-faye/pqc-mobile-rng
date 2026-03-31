from __future__ import annotations

"""Pont explicite entre la sortie COND et le materiau d'entree du DRBG."""

_DRBG_SEED_PREFIX = b"PQC-RNG-SEEDINIT:"


def encode_conditioner_seed_for_drbg(seedinit: bytes) -> bytes:
    """Encode `seedinit` pour un usage DRBG sans ambiguite de provenance."""

    if not isinstance(seedinit, (bytes, bytearray)):
        raise TypeError("seedinit doit etre de type bytes.")
    seedinit = bytes(seedinit)
    if not seedinit:
        raise ValueError("seedinit ne doit pas etre vide.")
    return _DRBG_SEED_PREFIX + seedinit


def decode_conditioner_seed_for_drbg(seed_material: bytes) -> bytes:
    """Valide et decode un seed material provenant explicitement de COND."""

    if not isinstance(seed_material, (bytes, bytearray)):
        raise TypeError("seed_material doit etre de type bytes.")
    seed_material = bytes(seed_material)
    if not seed_material.startswith(_DRBG_SEED_PREFIX):
        raise ValueError(
            "Le DRBG exige un seed material issu du conditionneur. "
            "Utilisez encode_conditioner_seed_for_drbg(seedinit)."
        )
    seedinit = seed_material[len(_DRBG_SEED_PREFIX):]
    if not seedinit:
        raise ValueError("Le seed material du conditionneur est invalide.")
    return seedinit
