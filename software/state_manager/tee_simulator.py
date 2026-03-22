from __future__ import annotations

import hmac
import json
import secrets
from hashlib import sha256, shake_256
from pathlib import Path

from .errors import IntegrityError, RollbackDetectedError, SealedBlobNotFoundError
from .models import SealedBlob, TeeDeviceStatus


class SimulatedTEE:
    """
    J'implémente ici une simulation logicielle du TEE.

    Important :
    - ceci n'est pas un vrai TrustZone / RPMB ;
    - je simule seulement les mécanismes essentiels pour mon mémoire :
      - Seal / Unseal
      - intégrité
      - compteur monotone
      - anti-rollback
    """

    def __init__(
        self,
        root_dir: str | Path = "state_data",
        device_id: str = "dev-001",
        namespace: str = "pqc_rng",
    ) -> None:
        self.root_dir = Path(root_dir)
        self.device_id = device_id
        self.namespace = namespace

        self.device_dir = self.root_dir / self.namespace / self.device_id
        self.device_dir.mkdir(parents=True, exist_ok=True)

        self._meta_path = self.device_dir / "device_meta.json"
        self._blobs_dir = self.device_dir / "blobs"
        self._blobs_dir.mkdir(parents=True, exist_ok=True)

        self._load_or_init_device_meta()

    def _load_or_init_device_meta(self) -> None:
        """
        Je charge ici l'identité persistante du périphérique simulé.

        Si aucun contexte n'existe encore, je crée :
        - une HUK simulée ;
        - un compteur matériel initialisé à zéro.
        """

        if self._meta_path.exists():
            data = json.loads(self._meta_path.read_text(encoding="utf-8"))
            self._huk_hex = data["huk_hex"]
            self._hardware_counter = int(data["hardware_counter"])
            return

        self._huk_hex = secrets.token_hex(32)
        self._hardware_counter = 0
        self._persist_meta()

    def _persist_meta(self) -> None:
        """
        Je persiste ici les métadonnées minimales du périphérique simulé.
        """

        payload = {
            "huk_hex": self._huk_hex,
            "hardware_counter": self._hardware_counter,
        }
        self._meta_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @property
    def huk(self) -> bytes:
        return bytes.fromhex(self._huk_hex)

    @property
    def hardware_counter(self) -> int:
        return self._hardware_counter

    def status(self) -> TeeDeviceStatus:
        return TeeDeviceStatus(
            device_id=self.device_id,
            namespace=self.namespace,
            hardware_counter=self._hardware_counter,
            has_huk=bool(self._huk_hex),
        )

    def _increment_hardware_counter(self) -> int:
        """
        J'incrémente ici le compteur monotone matériel simulé avant scellement.
        """

        self._hardware_counter += 1
        self._persist_meta()
        return self._hardware_counter

    def _blob_path(self, blob_id: str) -> Path:
        return self._blobs_dir / f"{blob_id}.json"

    def _derive_keys(self, blob_id: str, software_counter: int) -> tuple[bytes, bytes]:
        """
        Je dérive ici les clés de scellement et d'authentification.

        Je lie volontairement ces clés au contexte du blob et au compteur
        logiciel pour éviter qu'un blob soit réutilisable hors de son cadre.
        """

        context = (
            f"{self.namespace}|{self.device_id}|{blob_id}|{software_counter}"
        ).encode("utf-8")
        material = hmac.new(self.huk, context, sha256).digest()
        seal_key = hmac.new(material, b"seal_key", sha256).digest()
        auth_key = hmac.new(material, b"auth_key", sha256).digest()
        return seal_key, auth_key

    def _xor_stream_cipher(self, plaintext: bytes, seal_key: bytes, nonce: bytes) -> bytes:
        """
        Je simule ici un chiffrement par flot à but pédagogique.

        Cette construction reste une approximation logicielle du scellement.
        Dans un vrai TEE, je remplacerai ce point par une primitive native
        et standardisée de chiffrement authentifié.
        """

        stream = shake_256(seal_key + nonce).digest(len(plaintext))
        return bytes(a ^ b for a, b in zip(plaintext, stream))

    def seal(self, blob_id: str, plaintext: bytes, aad: bytes = b"") -> SealedBlob:
        """
        Je scelle ici un état sensible.

        Je fais successivement :
        - l'incrément du compteur monotone ;
        - la copie vers le compteur logiciel du blob ;
        - la dérivation des clés ;
        - le chiffrement du payload ;
        - le calcul du tag d'intégrité ;
        - la construction du blob scellé.
        """

        hw_counter = self._increment_hardware_counter()
        sw_counter = hw_counter

        seal_key, auth_key = self._derive_keys(blob_id, sw_counter)
        nonce = secrets.token_bytes(16)
        ciphertext = self._xor_stream_cipher(plaintext, seal_key, nonce)

        header = f"{blob_id}|{hw_counter}|{sw_counter}|1".encode("utf-8")
        tag = hmac.new(auth_key, header + aad + nonce + ciphertext, sha256).digest()

        return SealedBlob(
            blob_id=blob_id,
            hardware_counter=hw_counter,
            software_counter=sw_counter,
            nonce_hex=nonce.hex(),
            ciphertext_hex=ciphertext.hex(),
            tag_hex=tag.hex(),
            aad_hex=aad.hex(),
            version=1,
        )

    def save_blob(self, blob: SealedBlob) -> None:
        """
        Je persiste ici le blob scellé au format JSON.
        """

        self._blob_path(blob.blob_id).write_text(
            json.dumps(blob.to_dict(), indent=2),
            encoding="utf-8",
        )

    def load_blob(self, blob_id: str) -> SealedBlob:
        """
        Je charge ici un blob scellé déjà persisté.
        """

        path = self._blob_path(blob_id)
        if not path.exists():
            raise SealedBlobNotFoundError(
                f"Aucun blob scellé trouvé pour blob_id={blob_id}."
            )
        data = json.loads(path.read_text(encoding="utf-8"))
        return SealedBlob.from_dict(data)

    def unseal(self, blob: SealedBlob, expected_aad: bytes = b"") -> bytes:
        """
        Je restaure ici un blob scellé après vérifications.

        Je refuse la restauration si :
        - la version du blob n'est pas supportée ;
        - le compteur logiciel est plus ancien que le compteur matériel ;
        - les AAD ne correspondent pas ;
        - le tag d'intégrité n'est pas valide.
        """

        if blob.version != 1:
            raise IntegrityError("Version de blob non supportée.")

        current_hw = self.hardware_counter
        if blob.software_counter < current_hw:
            raise RollbackDetectedError(
                "Je détecte un rollback : le compteur logiciel du blob est plus ancien que le compteur matériel."
            )
        if blob.software_counter > current_hw:
            raise IntegrityError(
                "Le compteur logiciel du blob dépasse le compteur matériel courant."
            )
        if blob.hardware_counter != blob.software_counter:
            raise IntegrityError(
                "Le blob scellé porte des compteurs matériel et logiciel incohérents."
            )

        aad = bytes.fromhex(blob.aad_hex)
        if aad != expected_aad:
            raise IntegrityError(
                "Les données associées attendues ne correspondent pas au blob."
            )

        seal_key, auth_key = self._derive_keys(blob.blob_id, blob.software_counter)
        nonce = bytes.fromhex(blob.nonce_hex)
        ciphertext = bytes.fromhex(blob.ciphertext_hex)
        tag = bytes.fromhex(blob.tag_hex)

        header = (
            f"{blob.blob_id}|{blob.hardware_counter}|{blob.software_counter}|{blob.version}"
        ).encode("utf-8")
        expected_tag = hmac.new(auth_key, header + aad + nonce + ciphertext, sha256).digest()
        if not hmac.compare_digest(tag, expected_tag):
            raise IntegrityError("Je détecte une altération d'intégrité du blob scellé.")

        return self._xor_stream_cipher(ciphertext, seal_key, nonce)

    def seal_and_store(self, blob_id: str, plaintext: bytes, aad: bytes = b"") -> SealedBlob:
        """
        Je combine ici le scellement logique et la persistance du blob.
        """

        blob = self.seal(blob_id=blob_id, plaintext=plaintext, aad=aad)
        self.save_blob(blob)
        return blob

    def load_and_unseal(self, blob_id: str, expected_aad: bytes = b"") -> bytes:
        """
        Je combine ici le chargement du blob et sa restauration contrôlée.
        """

        blob = self.load_blob(blob_id)
        return self.unseal(blob, expected_aad=expected_aad)
