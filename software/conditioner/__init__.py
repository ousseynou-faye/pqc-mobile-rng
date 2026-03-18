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
from .entropy_mixer import ConditioningResult, EntropyMixer

__all__ = [
    "ToeplitzExtractor",
    "bits_from_bytes",
    "bytes_from_bits",
    "ShakeConditioner",
    "ConditioningResult",
    "EntropyMixer",
]
