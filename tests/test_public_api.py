from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from software.api import (
    RNGInvalidLengthError,
    RNGNotInitializedError,
    get_rng_service,
    rng_generate,
    rng_get_bytes,
    rng_health,
    rng_init,
    rng_reseed,
    rng_restore_state,
    rng_zeroize,
)
from software.api.rng_service import RNGServiceConfig, StateConfig


def build_runtime_dir(name: str) -> Path:
    root = Path("tests_runtime") / "public_api" / f"{name}_{uuid4().hex[:8]}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def configure_public_service(name: str):
    config = RNGServiceConfig(
        state=StateConfig(
            root_dir=build_runtime_dir(name),
            device_id=f"{name}-device",
            namespace=f"{name}-namespace",
            blob_id=f"{name}-blob",
            checkpoint_metadata={"purpose": f"{name}-checkpoint"},
        )
    )
    return get_rng_service(reset=True, config=config)


def test_rng_init_and_get_bytes_work():
    configure_public_service("init_and_get_bytes")

    assert rng_init(force_reinit=True) is True
    data = rng_get_bytes(32)

    assert isinstance(data, bytes)
    assert len(data) == 32


def test_rng_generate_is_public_alias():
    configure_public_service("generate_alias")
    rng_init(force_reinit=True)

    data = rng_generate(24)

    assert isinstance(data, bytes)
    assert len(data) == 24


def test_rng_health_is_sanitized():
    configure_public_service("health")
    rng_init(force_reinit=True)

    status = rng_health()

    assert status["initialized"] is True
    assert status["instantiated"] is True
    assert status["health_status"] in {"ok", "warning", "error"}
    assert "seedinit" not in status
    assert "entropy_pool" not in status
    assert "drbg_state" not in status


def test_rng_reseed_works_after_init():
    configure_public_service("reseed")
    rng_init(force_reinit=True)

    assert rng_reseed() is True
    assert rng_health()["last_operation"] == "reseed_rng"


def test_rng_get_bytes_requires_init():
    configure_public_service("requires_init")
    rng_zeroize()

    with pytest.raises(RNGNotInitializedError):
        rng_get_bytes(16)


def test_rng_get_bytes_rejects_invalid_length():
    configure_public_service("invalid_length")
    rng_init(force_reinit=True)

    with pytest.raises(RNGInvalidLengthError):
        rng_get_bytes(0)

    with pytest.raises(RNGInvalidLengthError):
        rng_get_bytes(4097)


def test_rng_zeroize_clears_initialized_state():
    configure_public_service("zeroize")
    rng_init(force_reinit=True)

    assert rng_zeroize() is True
    status = rng_health()

    assert status["initialized"] is False
    assert status["instantiated"] is False


def test_rng_restore_state_is_supported_after_checkpoint():
    configure_public_service("restore")
    rng_init(force_reinit=True)
    service = get_rng_service()
    _ = rng_get_bytes(16)
    service.checkpoint_state()
    rng_zeroize()

    assert rng_restore_state() is True
    assert rng_health()["state_available"] is True
