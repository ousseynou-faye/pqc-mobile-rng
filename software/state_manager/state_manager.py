from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .models import SealedBlob
from .tee_simulator import SimulatedTEE


@dataclass
class StateManager:
    """
    Je gère ici le cycle de vie d'un blob d'état scellé.
    """

    tee: SimulatedTEE
    blob_id: str = "drbg_state"

    def _encode_payload(self, payload: dict[str, Any]) -> bytes:
        """
        Je sérialise ici le payload dans un format JSON déterministe.
        """

        return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def _decode_payload(self, payload_bytes: bytes) -> dict[str, Any]:
        """
        Je reconstruis ici le dictionnaire Python à partir du payload sérialisé.
        """

        return json.loads(payload_bytes.decode("utf-8"))

    def _make_aad(self, payload_metadata: dict[str, Any] | None = None) -> bytes:
        """
        Je construis ici les données associées authentifiées du blob.

        J'y lie le blob à :
        - son identifiant logique ;
        - son namespace ;
        - son périphérique ;
        - ses métadonnées applicatives.
        """

        payload_metadata = payload_metadata or {}
        aad = {
            "blob_id": self.blob_id,
            "namespace": self.tee.namespace,
            "device_id": self.tee.device_id,
            "meta": payload_metadata,
        }
        return json.dumps(aad, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def seal_payload(
        self,
        payload: dict[str, Any],
        payload_metadata: dict[str, Any] | None = None,
    ) -> SealedBlob:
        """
        Je scelle ici un dictionnaire Python sérialisable.

        Cette méthode me fournit le point d'entrée principal quand je veux
        persister un état applicatif sans exposer les détails du TEE simulé.
        """

        plaintext = self._encode_payload(payload)
        aad = self._make_aad(payload_metadata)
        return self.tee.seal_and_store(self.blob_id, plaintext, aad=aad)

    def unseal_payload(
        self,
        payload_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Je restaure ici le dictionnaire Python sérialisé après contrôle du blob.
        """

        aad = self._make_aad(payload_metadata)
        plaintext = self.tee.load_and_unseal(self.blob_id, expected_aad=aad)
        return self._decode_payload(plaintext)

    def checkpoint_drbg(
        self,
        drbg: Any,
        payload_metadata: dict[str, Any] | None = None,
    ) -> SealedBlob:
        """
        Je scelle ici l'état exporté du DRBG si celui-ci expose la bonne interface.

        Je garde ainsi la couche STATE découplée du moteur DRBG lui-même :
        le DRBG exporte, puis la couche STATE protège.
        """

        if not hasattr(drbg, "export_sealable_state"):
            raise TypeError("Le DRBG fourni ne supporte pas export_sealable_state().")
        payload = drbg.export_sealable_state()
        return self.seal_payload(payload, payload_metadata=payload_metadata)

    def restore_drbg(
        self,
        drbg: Any,
        payload_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Je restaure ici un état scellé dans le DRBG si celui-ci expose la bonne interface.

        Si le blob est valide, je réinjecte ensuite le payload dans le DRBG
        via son interface d'import d'état scellable.
        """

        if not hasattr(drbg, "import_sealable_state"):
            raise TypeError("Le DRBG fourni ne supporte pas import_sealable_state().")
        payload = self.unseal_payload(payload_metadata=payload_metadata)
        drbg.import_sealable_state(payload)
        return payload
