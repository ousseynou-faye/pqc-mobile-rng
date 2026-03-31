import hashlib

import pytest

from software.pqc_drbg.drbg_engine import PQCCompositeDRBG
from software.pqc_drbg.errors import DRBGError, FailStopError, ReseedRequiredError
from software.pqc_drbg.lwr_core import ModuleLWRCore
from software.pqc_drbg.policy import DRBGPolicy, EngineSelectionMode
from software.pqc_drbg.sponge_core import MultiplexedSpongeAdapter
from software.pqc_drbg.state import DRBGState, DRBGStatus


class DummySponge:
    """Moteur sponge minimal pour verifier l'adaptateur et l'orchestrateur."""

    def __init__(self, seed_digest: bytes):
        self._seed = seed_digest
        self._counter = 0

    def squeeze_bytes(self, nbytes: int) -> bytes:
        if nbytes < 0:
            raise ValueError("nbytes doit etre >= 0.")

        out = bytearray()
        while len(out) < nbytes:
            block = hashlib.shake_256(
                b"dummy_sponge_block:" + self._seed + self._counter.to_bytes(8, "big")
            ).digest(32)
            out.extend(block)
            self._counter += 1
        return bytes(out[:nbytes])


def dummy_sponge_factory(seed_digest: bytes) -> DummySponge:
    return DummySponge(seed_digest)


@pytest.fixture
def sponge_engine() -> MultiplexedSpongeAdapter:
    return MultiplexedSpongeAdapter(sponge_factory=dummy_sponge_factory)


def test_lwr_same_seed_same_output():
    a = ModuleLWRCore()
    b = ModuleLWRCore()

    seed = b"seed-lwr-001"
    a.instantiate(seed)
    b.instantiate(seed)

    assert a.generate(64) == b.generate(64)


def test_lwr_different_seed_different_output():
    a = ModuleLWRCore()
    b = ModuleLWRCore()

    a.instantiate(b"seed-lwr-A")
    b.instantiate(b"seed-lwr-B")

    assert a.generate(64) != b.generate(64)


def test_lwr_generate_returns_expected_length():
    engine = ModuleLWRCore()
    engine.instantiate(b"seed-length")
    out = engine.generate(100)

    assert isinstance(out, bytes)
    assert len(out) == 100


def test_lwr_reseed_changes_stream():
    engine = ModuleLWRCore()
    engine.instantiate(b"seed-before-reseed")

    out_before = engine.generate(64)
    engine.reseed(b"seed-after-reseed")
    out_after = engine.generate(64)

    assert out_before != out_after


def test_lwr_zeroize_blocks_generation():
    engine = ModuleLWRCore()
    engine.instantiate(b"seed-zeroize")
    engine.zeroize()

    with pytest.raises(DRBGError):
        engine.generate(16)


def test_lwr_export_state_contains_expected_fields():
    engine = ModuleLWRCore()
    engine.instantiate(b"seed-export")
    state = engine.export_state()

    assert state["name"] == "module_lwr"
    assert state["initialized"] is True
    assert "counter" in state
    assert "modulus_q" in state
    assert "rounding_modulus_p" in state


def test_sponge_adapter_same_seed_same_output():
    a = MultiplexedSpongeAdapter(sponge_factory=dummy_sponge_factory)
    b = MultiplexedSpongeAdapter(sponge_factory=dummy_sponge_factory)

    seed = b"seed-sponge-001"
    a.instantiate(seed)
    b.instantiate(seed)

    assert a.generate(64) == b.generate(64)


def test_sponge_adapter_reseed_changes_output(sponge_engine: MultiplexedSpongeAdapter):
    sponge_engine.instantiate(b"seed-sponge-before")

    out_before = sponge_engine.generate(64)
    sponge_engine.reseed(b"seed-sponge-after")
    out_after = sponge_engine.generate(64)

    assert out_before != out_after


def test_sponge_adapter_generate_length(sponge_engine: MultiplexedSpongeAdapter):
    sponge_engine.instantiate(b"seed-sponge-length")
    out = sponge_engine.generate(33)

    assert isinstance(out, bytes)
    assert len(out) == 33


def test_composite_uses_sponge_by_default():
    drbg = PQCCompositeDRBG()
    drbg.instantiate(b"seed-default")

    out = drbg.generate(32)
    exported = drbg.export_state()

    assert isinstance(out, bytes)
    assert len(out) == 32
    assert exported["manager_state"]["active_engine"] == "multiplexed_sponge"


def test_composite_export_state_is_structured():
    drbg = PQCCompositeDRBG()
    drbg.instantiate(b"seed-export-composite")

    state = drbg.export_state()

    assert "manager_state" in state
    assert "policy" in state
    assert "active_engine_state" in state
    assert state["manager_state"]["initialized"] is True


def test_state_initialized_setter_stays_backward_compatible():
    state = DRBGState()

    state.initialized = True
    assert state.initialized is True
    assert state.status == DRBGStatus.READY

    state.initialized = False
    assert state.initialized is False
    assert state.status == DRBGStatus.UNINITIALIZED


def test_composite_zeroize_resets_manager_state():
    drbg = PQCCompositeDRBG()
    drbg.instantiate(b"seed-zeroize-manager")
    _ = drbg.generate(16)

    drbg.zeroize()
    state = drbg.export_state()

    assert state["manager_state"]["initialized"] is False
    assert state["manager_state"]["active_engine"] is None


def test_reseed_interval_requests_forces_reseed():
    policy = DRBGPolicy(
        selection_mode=EngineSelectionMode.STRICT_SPONGE_ONLY,
        reseed_interval_requests=1,
    )
    drbg = PQCCompositeDRBG(policy=policy)
    drbg.instantiate(b"seed-reseed-policy")

    assert len(drbg.generate(16)) == 16

    with pytest.raises(ReseedRequiredError):
        drbg.generate(16)


def test_manual_reseed_clears_reseed_required_flag():
    policy = DRBGPolicy(
        selection_mode=EngineSelectionMode.STRICT_SPONGE_ONLY,
        reseed_interval_requests=1,
    )
    drbg = PQCCompositeDRBG(policy=policy)
    drbg.instantiate(b"seed-manual-reseed")
    _ = drbg.generate(16)

    with pytest.raises(ReseedRequiredError):
        drbg.generate(16)

    drbg.reseed(b"fresh-seed", reason="test_reseed")

    out = drbg.generate(16)
    assert len(out) == 16
    assert drbg.export_state()["manager_state"]["last_reseed_reason"] == "test_reseed"


def test_prediction_resistance_forces_reseed_immediately():
    policy = DRBGPolicy(
        selection_mode=EngineSelectionMode.STRICT_SPONGE_ONLY,
        prediction_resistance=True,
    )
    drbg = PQCCompositeDRBG(policy=policy)
    drbg.instantiate(b"seed-prediction-resistance")

    with pytest.raises(ReseedRequiredError):
        drbg.generate(16)


def test_force_lwr_research_mode_uses_lwr_engine(sponge_engine: MultiplexedSpongeAdapter):
    policy = DRBGPolicy(selection_mode=EngineSelectionMode.FORCE_LWR_RESEARCH)
    drbg = PQCCompositeDRBG(sponge_engine=sponge_engine, policy=policy)

    drbg.instantiate(b"seed-force-lwr")
    out = drbg.generate(20)

    assert len(out) == 20
    assert drbg.export_state()["manager_state"]["active_engine"] == "module_lwr"
    assert drbg.export_state()["manager_state"]["flags"]["degraded_research"] is True


def test_fail_stop_if_active_engine_health_fails():
    drbg = PQCCompositeDRBG()
    drbg.instantiate(b"seed-fail-stop")

    drbg.sponge_engine.zeroize()

    with pytest.raises(FailStopError):
        drbg.generate(16)

    exported = drbg.export_state()
    assert exported["manager_state"]["flags"]["fail_stop"] is True


def test_strict_mode_does_not_silently_fallback_to_lwr():
    sponge = MultiplexedSpongeAdapter(sponge_factory=dummy_sponge_factory)
    sponge.instantiate(b"seed-sponge-ready")

    policy = DRBGPolicy(selection_mode=EngineSelectionMode.STRICT_SPONGE_ONLY)
    drbg = PQCCompositeDRBG(sponge_engine=sponge, policy=policy)
    drbg.instantiate(b"seed-strict-mode")

    def failing_generate(nbytes, additional_input=b""):
        raise RuntimeError("panne technique simulee")

    drbg.sponge_engine.generate = failing_generate

    with pytest.raises(RuntimeError):
        drbg.generate(16)

    assert drbg.export_state()["manager_state"]["active_engine"] == "multiplexed_sponge"


def test_experimental_mode_allows_controlled_fallback_on_runtime_failure():
    sponge = MultiplexedSpongeAdapter(sponge_factory=dummy_sponge_factory)
    sponge.instantiate(b"seed-sponge-fallback")

    policy = DRBGPolicy(
        selection_mode=EngineSelectionMode.ALLOW_EXPERIMENTAL_LWR_FALLBACK,
        allow_fallback_on_unavailability_only=True,
    )
    drbg = PQCCompositeDRBG(sponge_engine=sponge, policy=policy)
    drbg.instantiate(b"seed-sponge-fallback-main")

    def failing_generate(nbytes, additional_input=b""):
        raise RuntimeError("indisponibilite technique simulee")

    drbg.sponge_engine.generate = failing_generate

    out = drbg.generate(24)

    assert isinstance(out, bytes)
    assert len(out) == 24
    assert drbg.export_state()["manager_state"]["active_engine"] == "module_lwr"
