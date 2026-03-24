from __future__ import annotations

import pytest

from software.api import (
    RNGNotInitializedError,
    RNGRestoreError,
    get_rng_service,
    rng_generate,
    rng_get_bytes,
    rng_health,
    rng_init,
    rng_reseed,
    rng_restore_state,
    rng_zeroize,
)


def test_api_init_then_generate_returns_bytes_and_ready_state(configure_rng_service):
    service = configure_rng_service("api_init_generate")

    assert rng_init() is True
    output = rng_get_bytes(64)
    status = rng_health()

    assert isinstance(output, bytes)
    assert len(output) == 64
    assert status["initialized"] is True
    assert status["instantiated"] is True
    assert status["lifecycle_state"] == "ready"
    assert service.drbg.export_state()["manager_state"]["active_engine"] == "module_lwr"


def test_api_generate_alias_matches_public_contract(configure_rng_service):
    configure_rng_service("api_generate_alias")
    rng_init()

    output = rng_generate(17)

    assert isinstance(output, bytes)
    assert len(output) == 17
    assert rng_health()["last_operation"] == "generate_bytes"


def test_api_generate_requires_init_and_keeps_service_coherent(configure_rng_service):
    configure_rng_service("api_requires_init")

    with pytest.raises(RNGNotInitializedError, match="rng_init\\(\\) avant rng_get_bytes\\(\\)"):
        rng_get_bytes(16)

    status = rng_health()
    assert status["initialized"] is False
    assert status["instantiated"] is False
    assert status["lifecycle_state"] is None


def test_api_reseed_keeps_service_ready_without_exposing_sensitive_state(configure_rng_service):
    service = configure_rng_service("api_reseed")
    rng_init()
    before = rng_get_bytes(32)

    assert rng_reseed() is True

    after = rng_get_bytes(32)
    status = rng_health()
    assert before != after
    assert status["initialized"] is True
    assert status["lifecycle_state"] == "ready"
    assert status["last_operation"] == "generate_bytes"
    assert "seedinit" not in status
    assert "drbg_state" not in status
    assert service.last_conditioning is not None


def test_api_health_reports_safe_lifecycle_transitions(configure_rng_service):
    service = configure_rng_service("api_health_lifecycle")

    before = rng_health()
    rng_init()
    after_init = rng_health()
    _ = rng_get_bytes(8)
    after_generate = rng_health()
    rng_reseed()
    after_reseed = rng_health()
    service.checkpoint_state()
    rng_zeroize()
    after_zeroize = rng_health()

    assert before["initialized"] is False
    assert after_init["initialized"] is True
    assert after_generate["last_operation"] == "generate_bytes"
    assert after_reseed["last_operation"] == "reseed_rng"
    assert after_zeroize["initialized"] is False
    assert after_zeroize["state_available"] is True
    for status in (before, after_init, after_generate, after_reseed, after_zeroize):
        assert "seedinit" not in status
        assert "raw_data" not in status
        assert "toeplitz_seed" not in status


def test_api_zeroize_forbids_generate_until_reinit(configure_rng_service):
    configure_rng_service("api_zeroize")
    rng_init()
    _ = rng_get_bytes(12)

    assert rng_zeroize() is True

    with pytest.raises(RNGNotInitializedError, match="rng_init\\(\\) avant rng_get_bytes\\(\\)"):
        rng_get_bytes(12)

    assert rng_health()["initialized"] is False


def test_api_restore_round_trip_recovers_valid_service_state(configure_rng_service):
    service = configure_rng_service("api_restore_round_trip")
    rng_init()
    _ = rng_get_bytes(24)
    service.checkpoint_state()
    rng_zeroize()

    assert rng_restore_state() is True

    restored = rng_get_bytes(24)
    status = rng_health()
    assert isinstance(restored, bytes)
    assert len(restored) == 24
    assert status["initialized"] is True
    assert status["state_available"] is True
    assert get_rng_service().drbg.export_state()["manager_state"]["active_engine"] == "module_lwr"


def test_api_restore_without_checkpoint_raises_administered_error(configure_rng_service):
    configure_rng_service("api_restore_missing")

    with pytest.raises(RNGRestoreError, match="La restauration de l'etat a echoue"):
        rng_restore_state()
