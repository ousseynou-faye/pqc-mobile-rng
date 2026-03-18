from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from typing import List

from .models import EntropyChunk, HealthReport


@dataclass
class HealthEstimator:
    """
    J'implémente ici une estimation prudente de santé de la source.

    Ce module n'est pas une implémentation complète de toutes les procédures
    normatives avancées.
    En revanche, il me fournit déjà une base sérieuse et prudente pour :
    - éviter de surestimer l'entropie ;
    - rejeter des séquences manifestement gelées ;
    - alimenter le pool avec une estimation exploitable.
    """

    repetition_limit: int = 32
    adaptive_window_size: int = 64
    adaptive_max_proportion: float = 0.75

    def __post_init__(self) -> None:
        if self.repetition_limit <= 1:
            raise ValueError("repetition_limit doit être > 1.")
        if self.adaptive_window_size <= 1:
            raise ValueError("adaptive_window_size doit être > 1.")
        if not (0.0 < self.adaptive_max_proportion <= 1.0):
            raise ValueError("adaptive_max_proportion doit être dans ]0, 1].")

    def _most_common_value_probability(self, symbols: List[int]) -> float:
        """
        Je calcule la probabilité empirique de la valeur la plus fréquente.
        """
        if not symbols:
            return 1.0
        counts = Counter(symbols)
        return max(counts.values()) / len(symbols)

    def _min_entropy_from_pmax(self, p_max: float) -> float:
        """
        Je déduis ici une borne prudente de min-entropie par symbole.
        """
        if p_max <= 0.0:
            return 0.0
        return -math.log2(p_max)

    def _repetition_count_test(self, symbols: List[int]) -> bool:
        """
        Je vérifie ici qu'une même valeur ne se répète pas trop longtemps
        sans interruption.

        Si une valeur se répète sur une très longue séquence, c'est un signal
        d'alarme fort.
        """
        if not symbols:
            return False

        run = 1
        previous = symbols[0]

        for value in symbols[1:]:
            if value == previous:
                run += 1
                if run >= self.repetition_limit:
                    return False
            else:
                run = 1
                previous = value

        return True

    def _adaptive_proportion_test(self, symbols: List[int]) -> bool:
        """
        Je vérifie ici qu'aucune fenêtre locale ne soit dominée de manière
        excessive par une même valeur.

        Ce test est utile pour détecter :
        - une source qui se fige partiellement ;
        - un biais local trop marqué.
        """
        if len(symbols) < self.adaptive_window_size:
            return True

        window = self.adaptive_window_size
        for start in range(0, len(symbols) - window + 1):
            chunk = symbols[start:start + window]
            counts = Counter(chunk)
            local_pmax = max(counts.values()) / window
            if local_pmax > self.adaptive_max_proportion:
                return False

        return True

    def evaluate_symbols(
        self,
        symbols: List[int],
        symbol_bits: int,
        source_name: str = "unknown",
    ) -> HealthReport:
        """
        J'évalue ici un ensemble de symboles indépendamment de leur source.

        Je calcule :
        - la valeur la plus fréquente ;
        - une borne prudente de min-entropie ;
        - un test de répétition ;
        - un test de proportion adaptative.
        """
        warnings = []

        p_max = self._most_common_value_probability(symbols)
        h_min = self._min_entropy_from_pmax(p_max)

        repetition_ok = self._repetition_count_test(symbols)
        adaptive_ok = self._adaptive_proportion_test(symbols)

        if not repetition_ok:
            warnings.append(
                "Je détecte une répétition trop longue d'une même valeur dans la séquence."
            )

        if not adaptive_ok:
            warnings.append(
                "Je détecte une domination locale excessive d'une même valeur."
            )

        if h_min <= 0.0:
            warnings.append(
                "La borne de min-entropie estimée est nulle ou quasi nulle."
            )

        accepted = repetition_ok and adaptive_ok and (h_min > 0.0)

        return HealthReport(
            source_name=source_name,
            sample_count=len(symbols),
            symbol_bits=symbol_bits,
            most_common_value_probability=p_max,
            min_entropy_per_symbol=h_min,
            repetition_count_ok=repetition_ok,
            adaptive_proportion_ok=adaptive_ok,
            accepted=accepted,
            warnings=warnings,
        )

    def evaluate_chunk(self, chunk: EntropyChunk) -> HealthReport:
        """
        J'évalue ici directement un `EntropyChunk`.
        """
        report = self.evaluate_symbols(
            symbols=chunk.symbols,
            symbol_bits=chunk.symbol_bits,
            source_name=chunk.source_name,
        )
        chunk.estimated_min_entropy_per_symbol = report.min_entropy_per_symbol
        return report