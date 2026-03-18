from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class ShakeConditioner:
    """
    J'utilise ici SHAKE-256 comme dernière étape de conditionnement.

    Mon objectif est simple :
    - prendre la sortie de l'extracteur de Toeplitz ;
    - y ajouter un contexte explicite ;
    - dériver un `Seedinit` de longueur choisie.

    Pourquoi cette étape est utile :
    - elle finalise l'uniformisation ;
    - elle me donne une graine de taille stable ;
    - elle s'aligne sur la forme :
      Seedinit = SHAKE-256(Toeplitz(Raw_Data) || Context_Info).
    """

    output_bytes: int = 32
    domain_separator: bytes = b"PQC-RNG-COND-v1"

    def __post_init__(self) -> None:
        if self.output_bytes <= 0:
            raise ValueError("output_bytes doit être > 0.")

    def derive_seed(self, toeplitz_output: bytes, context_info: bytes = b"") -> bytes:
        """
        Je dérive ici la graine finale du conditionneur.

        Structure injectée dans SHAKE-256 :
        domain_separator || len(toeplitz_output) || toeplitz_output || context_info

        Le séparateur de domaine me permet d'éviter que cette construction
        soit confondue avec une autre dérivation SHAKE dans le projet.
        """
        if not isinstance(toeplitz_output, (bytes, bytearray)):
            raise TypeError("toeplitz_output doit être de type bytes.")
        if not isinstance(context_info, (bytes, bytearray)):
            raise TypeError("context_info doit être de type bytes.")

        payload = (
            self.domain_separator
            + len(toeplitz_output).to_bytes(4, "big")
            + bytes(toeplitz_output)
            + bytes(context_info)
        )

        return hashlib.shake_256(payload).digest(self.output_bytes)
