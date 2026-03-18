from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Callable, Iterable, List, Optional

from .models import EntropyChunk, SensorFrame


@dataclass
class SensorEntropySource:
    """
    J'utilise ici une source secondaire basée sur les capteurs inertiels.

    En pratique mobile, cette source devra être branchée à un adaptateur réel
    Android / Linux embarqué.
    Pour le prototype actuel, je propose :
    - soit un mode simulation ;
    - soit l'injection d'un adaptateur externe ;
    - soit le traitement direct d'une liste de `SensorFrame`.

    Je conserve seulement les bits de poids faible (LSB),
    conformément à l'idée que les MSB sont trop corrélés aux mouvements
    macroscopiques prédictibles.
    """

    frame_count: int = 128
    lsb_count: int = 2
    adapter: Optional[Callable[[int], List[SensorFrame]]] = None

    def __post_init__(self) -> None:
        if self.frame_count <= 0:
            raise ValueError("frame_count doit être > 0.")
        if self.lsb_count <= 0 or self.lsb_count > 8:
            raise ValueError("lsb_count doit être compris entre 1 et 8.")

    def _simulate_frame(self, index: int) -> SensorFrame:
        """
        Je simule ici une lecture inertielle de démonstration.

        Important :
        cette simulation n'est pas une vraie source capteur.
        Elle me permet seulement de développer et tester la couche SRC
        sur une machine non mobile.
        """
        t = time.perf_counter_ns()

        # Signal lent + petite perturbation temporelle.
        ax = int(1000 * math.sin(index / 9.0) + ((t >> 1) & 0x1F) - 16)
        ay = int(1000 * math.cos(index / 7.0) + ((t >> 3) & 0x1F) - 16)
        az = int(980 + ((t >> 5) & 0x0F) - 8)

        gx = int(120 * math.sin(index / 5.0) + ((t >> 2) & 0x07) - 3)
        gy = int(120 * math.cos(index / 6.0) + ((t >> 4) & 0x07) - 3)
        gz = int(60 * math.sin(index / 8.0) + ((t >> 6) & 0x07) - 3)

        return SensorFrame(
            ax=ax,
            ay=ay,
            az=az,
            gx=gx,
            gy=gy,
            gz=gz,
            timestamp_ns=t,
        )

    def _frame_to_symbols(self, frame: SensorFrame) -> List[int]:
        """
        Je transforme ici une lecture capteur en une petite liste de symboles.

        Je prends les LSB de chaque canal :
        - ax, ay, az
        - gx, gy, gz
        """
        mask = (1 << self.lsb_count) - 1
        values = [frame.ax, frame.ay, frame.az, frame.gx, frame.gy, frame.gz]
        return [value & mask for value in values]

    def collect_from_frames(self, frames: Iterable[SensorFrame]) -> EntropyChunk:
        """
        Je collecte l'entropie à partir d'un ensemble explicite de frames.

        Cette méthode est très utile :
        - pour les tests ;
        - pour une future intégration avec une vraie couche mobile ;
        - pour rejouer un scénario expérimental.
        """
        symbols: List[int] = []
        frame_counter = 0

        for frame in frames:
            symbols.extend(self._frame_to_symbols(frame))
            frame_counter += 1

        return EntropyChunk(
            source_name="inertial_sensors",
            symbols=symbols,
            symbol_bits=self.lsb_count,
            metadata={
                "frame_count": frame_counter,
                "channels_per_frame": 6,
                "lsb_count": self.lsb_count,
                "mode": "external_frames",
            },
        )

    def collect(self) -> EntropyChunk:
        """
        Je collecte ici un bloc d'entropie capteur.

        Deux modes sont possibles :
        - si un adaptateur est fourni, je l'utilise ;
        - sinon, je passe par une simulation locale.
        """
        if self.adapter is not None:
            frames = self.adapter(self.frame_count)
            mode = "adapter"
        else:
            frames = [self._simulate_frame(i) for i in range(self.frame_count)]
            mode = "simulation"

        chunk = self.collect_from_frames(frames)
        chunk.metadata["mode"] = mode
        return chunk