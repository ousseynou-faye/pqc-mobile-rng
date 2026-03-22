import json
from pathlib import Path

import pytest

from software.pqc_drbg.drbg_engine import PQCCompositeDRBG
from software.pqc_drbg.policy import DRBGPolicy, EngineSelectionMode
from software.pqc_drbg.sponge_core import MultiplexedSpongeAdapter
from software.state_manager import (
    IntegrityError,
    RollbackDetectedError,
    SimulatedTEE,
    StateManager,
)


class DummySponge:
    def __init__(self, seed_digest: bytes):
        self._seed = seed_digest

    def squeeze_bytes(self, nbytes: int) -> bytes:
        return (self._seed * ((nbytes // len(self._seed)) + 1))[:nbytes]


def dummy_sponge_factory(seed_digest: bytes) -> DummySponge:
    return DummySponge(seed_digest)


def build_manager(tmp_path: Path) -> StateManager:
    tee = SimulatedTEE(root_dir=tmp_path, device_id="device-test", namespace="rng-test")
    return StateManager(tee=tee, blob_id="drbg_state")


def test_seal_unseal_round_trip(tmp_path: Path):
    manager = build_manager(tmp_path)
    payload = {"counter": 7, "active_engine": "module_lwr"}

    manager.seal_payload(payload, payload_metadata={"purpose": "round_trip"})
    restored = manager.unseal_payload(payload_metadata={"purpose": "round_trip"})

    assert restored == payload


def test_integrity_tampering_is_detected(tmp_path: Path):
    manager = build_manager(tmp_path)
    payload = {"counter": 8, "active_engine": "module_lwr"}

    blob = manager.seal_payload(payload, payload_metadata={"purpose": "tamper"})
    blob_path = manager.tee._blob_path(blob.blob_id)

    data = json.loads(blob_path.read_text(encoding="utf-8"))
    corrupted = data["ciphertext_hex"]
    data["ciphertext_hex"] = ("0" if corrupted[0] != "0" else "1") + corrupted[1:]
    blob_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    with pytest.raises(IntegrityError):
        manager.unseal_payload(payload_metadata={"purpose": "tamper"})


def test_rollback_is_detected(tmp_path: Path):
    manager = build_manager(tmp_path)

    old_blob = manager.seal_payload({"epoch": 1}, payload_metadata={"purpose": "rollback"})
    manager.seal_payload({"epoch": 2}, payload_metadata={"purpose": "rollback"})

    with pytest.raises(RollbackDetectedError):
        manager.tee.unseal(old_blob, expected_aad=manager._make_aad({"purpose": "rollback"}))


def test_checkpoint_and_restore_drbg(tmp_path: Path):
    sponge = MultiplexedSpongeAdapter(sponge_factory=dummy_sponge_factory)
    drbg = PQCCompositeDRBG(
        sponge_engine=sponge,
        policy=DRBGPolicy(selection_mode=EngineSelectionMode.STRICT_LWR_ONLY),
    )
    drbg.instantiate(b"seed-state-test")
    _ = drbg.generate(16)

    manager = build_manager(tmp_path)
    manager.checkpoint_drbg(drbg, payload_metadata={"purpose": "checkpoint"})

    restored = PQCCompositeDRBG(
        sponge_engine=MultiplexedSpongeAdapter(sponge_factory=dummy_sponge_factory),
        policy=DRBGPolicy(selection_mode=EngineSelectionMode.STRICT_LWR_ONLY),
    )
    payload = manager.restore_drbg(restored, payload_metadata={"purpose": "checkpoint"})

    assert payload["manager_state"]["active_engine"] == "module_lwr"
    assert restored.export_state()["manager_state"]["active_engine"] == "module_lwr"
