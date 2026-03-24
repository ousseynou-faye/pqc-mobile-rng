from __future__ import annotations

from software.api import get_rng_service, rng_get_bytes, rng_health, rng_init, rng_restore_state, rng_zeroize
from software.pqc_drbg import DRBGPolicy, EngineSelectionMode


def test_end_to_end_nominal_pipeline(configure_rng_service):
    service = configure_rng_service("e2e_nominal_pipeline")

    assert rng_init() is True
    first = rng_get_bytes(96)
    checkpoint = service.checkpoint_state()
    before_zeroize = rng_health()

    assert rng_zeroize() is True
    assert rng_restore_state() is True

    second = rng_get_bytes(96)
    after_restore = rng_health()
    manager_state = get_rng_service().drbg.export_state()["manager_state"]

    assert checkpoint.blob_id == "e2e_nominal_pipeline-blob"
    assert len(first) == 96
    assert len(second) == 96
    assert before_zeroize["initialized"] is True
    assert after_restore["initialized"] is True
    assert after_restore["state_available"] is True
    assert manager_state["active_engine"] == "module_lwr"
    assert manager_state["lifecycle_state"] == "ready"


def test_end_to_end_baseline_keeps_official_src_cond_drbg_state_chain(configure_rng_service):
    service = configure_rng_service("e2e_baseline_chain")

    rng_init()
    _ = rng_get_bytes(32)

    conditioning = service.last_conditioning
    exported = service.drbg.export_state()

    assert conditioning is not None
    assert len(conditioning.seedinit) == 32
    assert len(conditioning.toeplitz_output) == 32
    assert exported["manager_state"]["active_engine"] == "module_lwr"
    assert exported["policy"]["selection_mode"] == EngineSelectionMode.STRICT_LWR_ONLY.value
    assert service.last_operation == "generate_bytes"


def test_end_to_end_research_engine_can_be_enabled_without_affecting_baseline_service(configure_rng_service):
    policy = DRBGPolicy(selection_mode=EngineSelectionMode.FORCE_SPONGE_RESEARCH)
    research = configure_rng_service("e2e_research_mode", policy=policy)

    assert rng_init() is True

    output = rng_get_bytes(40)
    exported = research.drbg.export_state()
    assert len(output) == 40
    assert exported["manager_state"]["active_engine"] == "multiplexed_sponge"
    assert exported["manager_state"]["flags"]["degraded_research"] is True

    baseline = configure_rng_service("e2e_research_mode_baseline")
    assert rng_init() is True
    _ = rng_get_bytes(40)
    assert baseline.drbg.export_state()["manager_state"]["active_engine"] == "module_lwr"
