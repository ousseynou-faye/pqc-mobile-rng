"""Deterministic bridge from conditioned seed material to LFSR seeds.

This module keeps the bridge explicit between the conditioner output
(`seedinit`, or a deterministic digest derived from it at DRBG level) and the
two recurrence sequences consumed by the Multiplexed Sponge prototype.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import shake_256
from math import ceil


_DERIVATION_DOMAIN = b"PQC-RNG-SPONGE-LFSR-v1"
_SEQ_S_LABEL = b"SEQ_S"
_SEQ_T_LABEL = b"SEQ_T"


@dataclass(frozen=True)
class DerivedLFSRSeeds:
    """Container for the two non-zero LFSR seeds used by the sponge."""

    seed_s: int
    seed_t: int
    degree_s: int
    degree_t: int


def _encode_field(value: bytes) -> bytes:
    """Prefix one field with its length to keep the derivation stable."""

    return len(value).to_bytes(4, "big") + value


def derive_lfsr_seed(
    seed_material: bytes,
    *,
    degree: int,
    domain_label: bytes,
    context: bytes = b"",
) -> int:
    """Derive one non-zero LFSR state from canonical seed material.

    The derivation is intentionally conservative:
    - SHAKE-256 provides deterministic domain-separated material;
    - the resulting integer is reduced into ``[1, 2**degree - 1]``;
    - the all-zero state is therefore impossible after reduction.
    """

    if not isinstance(seed_material, (bytes, bytearray)):
        raise TypeError("seed_material doit etre de type bytes.")
    if not isinstance(domain_label, (bytes, bytearray)):
        raise TypeError("domain_label doit etre de type bytes.")
    if not isinstance(context, (bytes, bytearray)):
        raise TypeError("context doit etre de type bytes.")
    if degree <= 0:
        raise ValueError("degree doit etre > 0.")

    seed_material = bytes(seed_material)
    if not seed_material:
        raise ValueError("seed_material ne doit pas etre vide.")

    valid_state_count = (1 << degree) - 1
    output_bytes = max(ceil(degree / 8), 16)

    payload = (
        _encode_field(_DERIVATION_DOMAIN)
        + _encode_field(bytes(domain_label))
        + _encode_field(degree.to_bytes(4, "big"))
        + _encode_field(bytes(context))
        + _encode_field(seed_material)
    )
    candidate = int.from_bytes(shake_256(payload).digest(output_bytes), "big")
    return (candidate % valid_state_count) + 1


def derive_sponge_lfsr_seeds(
    seed_material: bytes,
    *,
    degree_s: int,
    degree_t: int,
    context: bytes = b"",
) -> DerivedLFSRSeeds:
    """Derive the two domain-separated LFSR seeds for ``S_n`` and ``T_n``."""

    return DerivedLFSRSeeds(
        seed_s=derive_lfsr_seed(
            seed_material,
            degree=degree_s,
            domain_label=_SEQ_S_LABEL,
            context=context,
        ),
        seed_t=derive_lfsr_seed(
            seed_material,
            degree=degree_t,
            domain_label=_SEQ_T_LABEL,
            context=context,
        ),
        degree_s=degree_s,
        degree_t=degree_t,
    )
