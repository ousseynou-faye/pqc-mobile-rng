from __future__ import annotations

import time
from dataclasses import dataclass

from .models import EntropyChunk


@dataclass
class CPUJitterSource:
    """
    J'utilise ici les variations fines du temps d'exécution du processeur
    comme source primaire d'entropie.

    Idée :
    - j'exécute une boucle dense ;
    - je mesure la durée en nanosecondes ;
    - je conserve surtout les bits faibles de la mesure,
      car ce sont eux qui reflètent le plus les micro-variations.

    Cette source n'est pas une preuve formelle d'entropie à elle seule.
    Elle me sert à collecter un bruit brut prudent, qui sera ensuite
    estimé puis conditionné.
    """

    sample_count: int = 512
    inner_loops: int = 256
    lsb_count: int = 2
    warmup_rounds: int = 32

    def __post_init__(self) -> None:
        if self.sample_count <= 0:
            raise ValueError("sample_count doit être > 0.")
        if self.inner_loops <= 0:
            raise ValueError("inner_loops doit être > 0.")
        if self.lsb_count <= 0 or self.lsb_count > 8:
            raise ValueError("lsb_count doit être compris entre 1 et 8.")
        if self.warmup_rounds < 0:
            raise ValueError("warmup_rounds doit être >= 0.")

    def _busy_loop(self) -> int:
        """
        Je crée ici une petite charge CPU volontaire.

        Le résultat numérique n'est pas important.
        Ce qui m'intéresse, c'est la variabilité temporelle de l'exécution.
        """
        acc = 0x12345678
        for i in range(self.inner_loops):
            acc ^= ((acc << 5) + i + (acc >> 2)) & 0xFFFFFFFF
            acc &= 0xFFFFFFFF
        return acc

    def _measure_delta_ns(self) -> int:
        """
        Je mesure ici la durée d'une exécution de la boucle dense.
        """
        start = time.perf_counter_ns()
        _ = self._busy_loop()
        end = time.perf_counter_ns()
        return max(0, end - start)

    def _extract_symbol(self, delta_ns: int, previous_delta_ns: int) -> int:
        """
        Je mélange légèrement la mesure courante avec la mesure précédente,
        puis je conserve seulement les `lsb_count` bits faibles.
        """
        mask = (1 << self.lsb_count) - 1
        mixed = delta_ns ^ (delta_ns >> 7) ^ previous_delta_ns ^ (previous_delta_ns >> 3)
        return mixed & mask

    def collect(self) -> EntropyChunk:
        """
        Je collecte un bloc d'entropie brute depuis le CPU jitter.

        La sortie est un `EntropyChunk` qui pourra ensuite être évalué
        par l'estimateur de santé puis injecté dans le pool.
        """
        for _ in range(self.warmup_rounds):
            self._measure_delta_ns()

        symbols = []
        previous = 0

        for _ in range(self.sample_count):
            delta = self._measure_delta_ns()
            symbol = self._extract_symbol(delta, previous)
            symbols.append(symbol)
            previous = delta

        return EntropyChunk(
            source_name="cpu_jitter",
            symbols=symbols,
            symbol_bits=self.lsb_count,
            metadata={
                "sample_count": self.sample_count,
                "inner_loops": self.inner_loops,
                "lsb_count": self.lsb_count,
                "warmup_rounds": self.warmup_rounds,
            },
        )