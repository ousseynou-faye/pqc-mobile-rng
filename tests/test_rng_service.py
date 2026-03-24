from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from software.api import get_rng_service
from software.api.rng_generate import generate_bytes
from software.api.rng_health import get_health_status
from software.api.rng_init import build_entropy_seed, instantiate_rng
from software.api.rng_reseed import checkpoint_state, reseed_rng, restore_state
from software.api.rng_service import RNGService, RNGServiceConfig, RNGServiceError, StateConfig


def build_runtime_dir(name: str) -> Path:
    root = Path("tests_runtime") / "rng_service" / f"{name}_{uuid4().hex[:8]}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def build_service(root_dir: Path) -> RNGService:
    config = RNGServiceConfig(
        state=StateConfig(
            root_dir=root_dir,
            device_id="service-test-device",
            namespace="service-test-namespace",
            blob_id="service-test-blob",
            checkpoint_metadata={"purpose": "service-test-checkpoint"},
        )
    )
    return RNGService(config=config)


def test_service_can_be_instantiated():
    service = build_service(build_runtime_dir("instantiate"))

    assert service.drbg is None
    assert service.last_conditioning is None


def test_build_entropy_seed_returns_seed_material():
    service = build_service(build_runtime_dir("build_seed"))

    result = service.build_entropy_seed()

    assert isinstance(result.seedinit, bytes)
    assert len(result.seedinit) == 32
    assert result.raw_data


def test_instantiate_rng_initializes_drbg():
    service = build_service(build_runtime_dir("init_rng"))

    drbg = service.instantiate_rng()

    assert drbg.export_state()["manager_state"]["initialized"] is True
    assert drbg.export_state()["manager_state"]["active_engine"] == "module_lwr"


def test_generate_bytes_returns_requested_length():
    service = build_service(build_runtime_dir("generate_bytes"))
    service.instantiate_rng()

    output = service.generate_bytes(48)

    assert isinstance(output, bytes)
    assert len(output) == 48


def test_generate_bytes_fails_before_instantiate():
    service = build_service(build_runtime_dir("generate_before_init"))

    with pytest.raises(RNGServiceError):
        service.generate_bytes(16)


def test_checkpoint_and_restore_round_trip():
    service = build_service(build_runtime_dir("checkpoint_restore"))
    service.instantiate_rng()
    _ = service.generate_bytes(24)

    blob = service.checkpoint_state()
    restored = service.restore_state()

    assert blob.blob_id == "service-test-blob"
    assert restored["manager_state"]["active_engine"] == "module_lwr"
    assert service.generate_bytes(24)


def test_reseed_refreshes_seed_material():
    service = build_service(build_runtime_dir("reseed"))
    service.instantiate_rng()

    first_seed = service.last_conditioning.seedinit
    reseed_result = service.reseed_rng()

    assert reseed_result.seedinit != b""
    assert service.last_conditioning.seedinit == reseed_result.seedinit
    assert first_seed != service.last_conditioning.seedinit


def test_wrappers_use_canonical_service():
    config = RNGServiceConfig(
        state=StateConfig(
            root_dir=build_runtime_dir("wrappers"),
            device_id="wrapper-device",
            namespace="wrapper-namespace",
            blob_id="wrapper-blob",
            checkpoint_metadata={"purpose": "wrapper-checkpoint"},
        )
    )
    service = get_rng_service(reset=True, config=config)

    seed = build_entropy_seed()
    drbg = instantiate_rng()
    output = generate_bytes(16)
    health = get_health_status()
    blob = checkpoint_state()
    restored = restore_state()
    reseed_result = reseed_rng()

    assert service is get_rng_service()
    assert len(seed.seedinit) == 32
    assert drbg.export_state()["manager_state"]["active_engine"] == "module_lwr"
    assert len(output) == 16
    assert health["instantiated"] is True
    assert blob.blob_id == "wrapper-blob"
    assert restored["manager_state"]["active_engine"] == "module_lwr"
    assert len(reseed_result.seedinit) == 32
