from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


def pack_symbols_to_bytes(symbols: List[int], symbol_bits: int) -> bytes:
    """
    Je convertis ici une liste de symboles en flux d'octets.

    Hypothèses :
    - chaque symbole occupe `symbol_bits` bits ;
    - l'empilement est fait de gauche à droite dans un flux binaire ;
    - si le dernier octet est incomplet, je le complète à droite avec des zéros.

    Cette fonction me permet d'exporter une entropie brute sous forme de bytes,
    même si les symboles d'origine ne font que 1, 2, 3 ou 4 bits.
    """
    if symbol_bits <= 0:
        raise ValueError("symbol_bits doit être strictement positif.")

    if any(value < 0 or value >= (1 << symbol_bits) for value in symbols):
        raise ValueError("Un symbole dépasse la taille autorisée par symbol_bits.")

    out = bytearray()
    buffer = 0
    buffered_bits = 0

    for value in symbols:
        buffer = (buffer << symbol_bits) | value
        buffered_bits += symbol_bits

        while buffered_bits >= 8:
            shift = buffered_bits - 8
            out.append((buffer >> shift) & 0xFF)
            buffer &= (1 << shift) - 1 if shift > 0 else 0
            buffered_bits -= 8

    if buffered_bits > 0:
        out.append((buffer << (8 - buffered_bits)) & 0xFF)

    return bytes(out)


@dataclass
class SensorFrame:
    """
    Je représente ici une lecture inertielle élémentaire.

    Les champs correspondent à :
    - accéléromètre : ax, ay, az
    - gyroscope : gx, gy, gz
    - timestamp_ns : horodatage en nanosecondes
    """

    ax: int
    ay: int
    az: int
    gx: int
    gy: int
    gz: int
    timestamp_ns: int


@dataclass
class EntropyChunk:
    """
    Je regroupe ici un bloc d'entropie brute issu d'une source.

    - `symbols` contient les symboles extraits ;
    - `symbol_bits` décrit la largeur de chaque symbole ;
    - `source_name` identifie la source ;
    - `metadata` transporte les paramètres de capture ;
    - `estimated_min_entropy_per_symbol` peut être rempli plus tard
      par l'estimateur de santé.
    """

    source_name: str
    symbols: List[int]
    symbol_bits: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    estimated_min_entropy_per_symbol: float | None = None

    @property
    def sample_count(self) -> int:
        return len(self.symbols)

    @property
    def raw_bytes(self) -> bytes:
        return pack_symbols_to_bytes(self.symbols, self.symbol_bits)

    @property
    def estimated_total_min_entropy_bits(self) -> float:
        if self.estimated_min_entropy_per_symbol is None:
            return 0.0
        return self.estimated_min_entropy_per_symbol * self.sample_count


@dataclass
class HealthReport:
    """
    Je résume ici le résultat d'une vérification de santé.

    Cette structure me permet de savoir :
    - si le bloc semble exploitable ;
    - quelle est la borne prudente de min-entropie ;
    - si certains signaux d'alerte apparaissent.
    """

    source_name: str
    sample_count: int
    symbol_bits: int
    most_common_value_probability: float
    min_entropy_per_symbol: float
    repetition_count_ok: bool
    adaptive_proportion_ok: bool
    accepted: bool
    warnings: List[str] = field(default_factory=list)


@dataclass
class PoolSnapshot:
    """
    Je décris ici l'état courant du réservoir d'entropie.

    Cette vue me sert à savoir si j'ai déjà accumulé suffisamment de matériau
    brut pour passer à l'étape de conditionnement.
    """

    accepted_chunks: int
    rejected_chunks: int
    total_symbols: int
    total_raw_bytes: int
    estimated_min_entropy_bits: float
    ready: bool