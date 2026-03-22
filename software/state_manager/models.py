from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class SealedBlob:
    """
    Je représente ici un blob scellé stocké par la couche STATE.
    """

    blob_id: str
    hardware_counter: int
    software_counter: int
    nonce_hex: str
    ciphertext_hex: str
    tag_hex: str
    aad_hex: str
    version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "SealedBlob":
        return SealedBlob(
            blob_id=data["blob_id"],
            hardware_counter=int(data["hardware_counter"]),
            software_counter=int(data["software_counter"]),
            nonce_hex=data["nonce_hex"],
            ciphertext_hex=data["ciphertext_hex"],
            tag_hex=data["tag_hex"],
            aad_hex=data.get("aad_hex", ""),
            version=int(data.get("version", 1)),
        )


@dataclass
class TeeDeviceStatus:
    """
    Je fournis ici une vue simple de l'état du TEE simulé.
    """

    device_id: str
    namespace: str
    hardware_counter: int
    has_huk: bool
