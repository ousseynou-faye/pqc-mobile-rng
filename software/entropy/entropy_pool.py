from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

from .health_estimator import HealthEstimator
from .models import EntropyChunk, HealthReport, PoolSnapshot


@dataclass
class EntropyPool:
    """
    J'accumule ici des blocs d'entropie brute provenant de plusieurs sources.

    Le rôle du pool n'est pas encore de conditionner l'entropie.
    Je m'en sers plutôt pour :
    - stocker des chunks validés ;
    - suivre une estimation prudente de min-entropie ;
    - décider si j'ai assez de matériau brut pour alimenter la couche COND.
    """

    target_min_entropy_bits: float = 256.0
    target_min_symbols: int = 512
    reject_on_fail: bool = True
    estimator: HealthEstimator = field(default_factory=HealthEstimator)

    def __post_init__(self) -> None:
        if self.target_min_entropy_bits <= 0:
            raise ValueError("target_min_entropy_bits doit être > 0.")
        if self.target_min_symbols <= 0:
            raise ValueError("target_min_symbols doit être > 0.")

        self._accepted_chunks: List[EntropyChunk] = []
        self._rejected_chunks: List[Tuple[EntropyChunk, HealthReport]] = []
        self._reports: List[HealthReport] = []

    def add_chunk(self, chunk: EntropyChunk) -> HealthReport:
        """
        J'ajoute ici un bloc au pool après évaluation.

        Si `reject_on_fail=True`, je rejette les blocs dont la santé échoue.
        """
        report = self.estimator.evaluate_chunk(chunk)
        self._reports.append(report)

        if self.reject_on_fail and not report.accepted:
            self._rejected_chunks.append((chunk, report))
            return report

        self._accepted_chunks.append(chunk)
        return report

    def total_symbols(self) -> int:
        """
        Je retourne le nombre total de symboles acceptés.
        """
        return sum(chunk.sample_count for chunk in self._accepted_chunks)

    def total_raw_bytes(self) -> int:
        """
        Je retourne la taille brute totale actuellement stockée.
        """
        return sum(len(chunk.raw_bytes) for chunk in self._accepted_chunks)

    def estimated_min_entropy_bits(self) -> float:
        """
        Je somme ici les estimations prudentes de min-entropie des blocs acceptés.
        """
        return sum(chunk.estimated_total_min_entropy_bits for chunk in self._accepted_chunks)

    def is_ready(self) -> bool:
        """
        Je décide ici si le pool est prêt à alimenter le conditionneur.

        Je demande deux conditions :
        - assez de symboles accumulés ;
        - assez de min-entropie estimée.
        """
        return (
            self.total_symbols() >= self.target_min_symbols
            and self.estimated_min_entropy_bits() >= self.target_min_entropy_bits
        )

    def snapshot(self) -> PoolSnapshot:
        """
        Je fournis ici un résumé instantané de l'état du pool.
        """
        return PoolSnapshot(
            accepted_chunks=len(self._accepted_chunks),
            rejected_chunks=len(self._rejected_chunks),
            total_symbols=self.total_symbols(),
            total_raw_bytes=self.total_raw_bytes(),
            estimated_min_entropy_bits=self.estimated_min_entropy_bits(),
            ready=self.is_ready(),
        )

    def export_raw_bytes(self, max_bytes: int | None = None) -> bytes:
        """
        J'exporte ici les octets bruts acceptés, dans l'ordre d'insertion.

        Cette sortie est destinée à être utilisée par la couche COND.
        """
        data = b"".join(chunk.raw_bytes for chunk in self._accepted_chunks)
        if max_bytes is not None:
            if max_bytes < 0:
                raise ValueError("max_bytes doit être >= 0.")
            return data[:max_bytes]
        return data

    def export_metadata(self) -> dict:
        """
        J'exporte ici des métadonnées utiles pour le conditionneur ou les logs.
        """
        return {
            "accepted_chunks": len(self._accepted_chunks),
            "rejected_chunks": len(self._rejected_chunks),
            "total_symbols": self.total_symbols(),
            "total_raw_bytes": self.total_raw_bytes(),
            "estimated_min_entropy_bits": self.estimated_min_entropy_bits(),
            "ready": self.is_ready(),
            "sources": [chunk.source_name for chunk in self._accepted_chunks],
        }

    @property
    def accepted_chunks(self) -> List[EntropyChunk]:
        """
        Je retourne la liste des blocs acceptés.
        """
        return list(self._accepted_chunks)

    @property
    def rejected_chunks(self) -> List[Tuple[EntropyChunk, HealthReport]]:
        """
        Je retourne la liste des blocs rejetés avec leur rapport.
        """
        return list(self._rejected_chunks)

    @property
    def reports(self) -> List[HealthReport]:
        """
        Je retourne l'historique des rapports générés.
        """
        return list(self._reports)