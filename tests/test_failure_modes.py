from __future__ import annotations

import json

import pytest

from software.api import (
    RNGInvalidLengthError,
    RNGNotInitializedError,
    RNGRestoreError,
    rng_get_bytes,
    rng_health,
    rng_init,
    rng_reseed,
    rng_restore_state,
    rng_zeroize,
)


@pytest.mark.parametrize(
    ("length", "message"),
    [
        (0, "length doit etre > 0."),
        (-1, "length doit etre > 0."),
        (True, "length doit etre un entier strictement positif."),
        ("8", "length doit etre un entier strictement positif."),
    ],
)
def test_failure_invalid_public_lengths_are_rejected_with_clear_message(
    configure_rng_service,
    length,
    message,
):
    configure_rng_service("failure_invalid_lengths")
    rng_init()

    with pytest.raises(RNGInvalidLengthError, match=message):
        rng_get_bytes(length)

    assert rng_health()["initialized"] is True


def test_failure_reseed_requires_init_and_does_not_corrupt_service(configure_rng_service):
    configure_rng_service("failure_reseed_requires_init")

    with pytest.raises(RNGNotInitializedError, match="rng_init\\(\\) avant rng_reseed\\(\\)"):
        rng_reseed()

    status = rng_health()
    assert status["initialized"] is False
    assert status["last_operation"] is None


def test_failure_restore_rejects_tampered_state_and_service_stays_zeroized(configure_rng_service):
    service = configure_rng_service("failure_tampered_restore")
    rng_init()
    _ = rng_get_bytes(16)
    blob = service.checkpoint_state()
    blob_path = service._state_manager.tee._blob_path(blob.blob_id)

    serialized = json.loads(blob_path.read_text(encoding="utf-8"))
    corrupted = serialized["ciphertext_hex"]
    serialized["ciphertext_hex"] = ("0" if corrupted[0] != "0" else "1") + corrupted[1:]
    blob_path.write_text(json.dumps(serialized, indent=2), encoding="utf-8")

    rng_zeroize()

    with pytest.raises(RNGRestoreError, match="alt.ration d'int.grit."):
        rng_restore_state()

    status = rng_health()
    assert status["initialized"] is False
    assert status["state_available"] is True


def test_failure_restore_rejects_rollback_blob_explicitly(configure_rng_service):
    service = configure_rng_service("failure_rollback_restore")
    rng_init()
    _ = rng_get_bytes(16)
    first_blob = service.checkpoint_state()
    first_snapshot = first_blob.to_dict()
    _ = rng_get_bytes(16)
    latest_blob = service.checkpoint_state()
    blob_path = service._state_manager.tee._blob_path(latest_blob.blob_id)
    blob_path.write_text(json.dumps(first_snapshot, indent=2), encoding="utf-8")

    rng_zeroize()

    with pytest.raises(RNGRestoreError, match="rollback"):
        rng_restore_state()

    assert rng_health()["initialized"] is False


def test_failure_zeroize_is_idempotent_and_generate_remains_blocked(configure_rng_service):
    configure_rng_service("failure_zeroize_idempotent")
    rng_init()
    assert rng_zeroize() is True
    assert rng_zeroize() is True

    with pytest.raises(RNGNotInitializedError):
        rng_get_bytes(8)


def test_failure_wrong_restore_metadata_is_rejected_cleanly(configure_rng_service):
    service = configure_rng_service("wrong_restore_meta")
    rng_init()
    _ = rng_get_bytes(12)
    service.checkpoint_state(payload_metadata={"purpose": "expected-metadata"})
    rng_zeroize()

    with pytest.raises(RNGRestoreError, match="donn.es associ.es attendues"):
        rng_restore_state(payload_metadata={"purpose": "wrong-metadata"})
