from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .shake_conditioner import ShakeConditioner
from .toeplitz_extractor import ToeplitzExtractor


@dataclass(frozen=True)
class ConditioningResult:
    """
    Je regroupe ici la sortie complète de la couche COND.

    Ce résultat me permet de conserver :
    - les données brutes utilisées ;
    - la sortie intermédiaire de Toeplitz ;
    - le contexte injecté ;
    - la graine finale `seedinit`.
    """

    raw_data: bytes
    toeplitz_seed: bytes
    toeplitz_output: bytes
    context_info: bytes
    seedinit: bytes
    input_bits: int
    output_bits: int


@dataclass
class EntropyMixer:
    """
    J'orchestre ici toute la couche COND.

    Mon rôle est de :
    1. récupérer l'entropie brute issue de SRC ;
    2. construire un extracteur de Toeplitz ;
    3. produire une sortie intermédiaire ;
    4. finaliser `Seedinit` via SHAKE-256.

    Important :
    cette couche vient avant le DRBG, car le DRBG ne doit jamais recevoir
    une graine brute, biaisée ou mal structurée.
    """

    toeplitz_output_bits: int = 256
    shake_output_bytes: int = 32
    domain_separator: bytes = b"PQC-RNG-COND-v1"

    def __post_init__(self) -> None:
        if self.toeplitz_output_bits <= 0:
            raise ValueError("toeplitz_output_bits doit être > 0.")
        if self.shake_output_bytes <= 0:
            raise ValueError("shake_output_bytes doit être > 0.")

        self.shake = ShakeConditioner(
            output_bytes=self.shake_output_bytes,
            domain_separator=self.domain_separator,
        )

    def build_context_info(
        self,
        *,
        metadata: Optional[Dict[str, Any]] = None,
        personalization: bytes = b"",
        label: str = "Seedinit",
        extra_context: bytes = b"",
    ) -> bytes:
        """
        Je construis ici un contexte stable à injecter dans SHAKE-256.

        J'y place :
        - un label logique ;
        - les métadonnées utiles de la couche SRC ;
        - un personalization string ;
        - un contexte additionnel facultatif.
        """
        metadata = metadata or {}

        serialized = json.dumps(
            {
                "label": label,
                "metadata": metadata,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return (
            b"CTX|"
            + serialized
            + b"|PERS|"
            + bytes(personalization)
            + b"|EXTRA|"
            + bytes(extra_context)
        )

    def derive_toeplitz_seed(
        self,
        *,
        input_bits: int,
        context_info: bytes,
        public_seed: Optional[bytes] = None,
    ) -> bytes:
        """
        Je dérive ici la graine publique de la matrice de Toeplitz.

        Point méthodologique important :
        - dans une démonstration idéale du Leftover Hash Lemma, la matrice doit être
          choisie indépendamment de la source brute ;
        - dans ce prototype logiciel, je dérive donc cette graine à partir d'un
          contexte public configurable, et non à partir de `raw_data` lui-même.

        Cela me donne un comportement :
        - déterministe ;
        - reproductible ;
        - propre pour les tests et le mémoire.
        """
        needed_bits = ToeplitzExtractor.seed_length_bits(
            input_bits=input_bits,
            output_bits=self.toeplitz_output_bits,
        )
        needed_bytes = (needed_bits + 7) // 8

        seed_material = (public_seed or b"PQC-RNG-TOEPLITZ-SEED") + bytes(context_info)
        return hashlib.shake_256(seed_material).digest(needed_bytes)

    def condition_raw_data(
        self,
        *,
        raw_data: bytes,
        metadata: Optional[Dict[str, Any]] = None,
        personalization: bytes = b"",
        extra_context: bytes = b"",
        toeplitz_public_seed: Optional[bytes] = None,
    ) -> ConditioningResult:
        """
        Je conditionne ici directement une source brute sous forme de bytes.

        Pipeline :
        1. construire `context_info` ;
        2. dériver une graine publique pour la matrice de Toeplitz ;
        3. appliquer Toeplitz(Raw_Data) ;
        4. dériver `Seedinit = SHAKE-256(Toeplitz(Raw_Data) || Context_Info)`.
        """
        if not isinstance(raw_data, (bytes, bytearray)):
            raise TypeError("raw_data doit être de type bytes.")
        raw_data = bytes(raw_data)

        if len(raw_data) == 0:
            raise ValueError("raw_data ne doit pas être vide.")

        input_bits = len(raw_data) * 8
        output_bits = self.toeplitz_output_bits

        context_info = self.build_context_info(
            metadata=metadata,
            personalization=personalization,
            extra_context=extra_context,
        )

        toeplitz_seed = self.derive_toeplitz_seed(
            input_bits=input_bits,
            context_info=context_info,
            public_seed=toeplitz_public_seed,
        )

        extractor = ToeplitzExtractor.from_seed_bytes(
            input_bits=input_bits,
            output_bits=output_bits,
            seed_bytes=toeplitz_seed,
        )

        toeplitz_output = extractor.extract_bytes(raw_data)
        seedinit = self.shake.derive_seed(
            toeplitz_output=toeplitz_output,
            context_info=context_info,
        )

        return ConditioningResult(
            raw_data=raw_data,
            toeplitz_seed=toeplitz_seed,
            toeplitz_output=toeplitz_output,
            context_info=context_info,
            seedinit=seedinit,
            input_bits=input_bits,
            output_bits=output_bits,
        )

    def condition_from_pool(
        self,
        pool: Any,
        *,
        personalization: bytes = b"",
        extra_context: bytes = b"",
        toeplitz_public_seed: Optional[bytes] = None,
    ) -> ConditioningResult:
        """
        Je conditionne ici directement un objet de type pool, à condition qu'il expose
        au moins :
        - `export_raw_bytes()`
        - `export_metadata()`

        Je reste volontairement souple sur le type exact du pool pour simplifier
        l'intégration avec ta couche SRC déjà codée.
        """
        if not hasattr(pool, "export_raw_bytes"):
            raise TypeError("Le pool doit exposer une méthode export_raw_bytes().")
        if not hasattr(pool, "export_metadata"):
            raise TypeError("Le pool doit exposer une méthode export_metadata().")

        raw_data = pool.export_raw_bytes()
        metadata = pool.export_metadata()

        return self.condition_raw_data(
            raw_data=raw_data,
            metadata=metadata,
            personalization=personalization,
            extra_context=extra_context,
            toeplitz_public_seed=toeplitz_public_seed,
        )
