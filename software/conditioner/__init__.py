"""
J'expose ici les composants publics de la couche COND.

Cette couche me sert à :
- prendre l'entropie brute issue de SRC ;
- appliquer un extracteur de Toeplitz sur GF(2) ;
- finaliser la graine par SHAKE-256 ;
- produire un `Seedinit` propre à injecter dans le DRBG.
"""

from .toeplitz_extractor import ToeplitzExtractor, bits_from_bytes, bytes_from_bits
from .shake_conditioner import ShakeConditioner
from .drbg_seed_material import decode_conditioner_seed_for_drbg, encode_conditioner_seed_for_drbg
from .entropy_mixer import ConditioningResult, EntropyMixer

__all__ = [
    "ToeplitzExtractor",
    "bits_from_bytes",
    "bytes_from_bits",
    "ShakeConditioner",
    "encode_conditioner_seed_for_drbg",
    "decode_conditioner_seed_for_drbg",
    "ConditioningResult",
    "EntropyMixer",
]
