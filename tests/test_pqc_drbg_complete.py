import hashlib

import pytest

from software.conditioner import encode_conditioner_seed_for_drbg
from software.pqc_drbg.drbg_engine import PQCCompositeDRBG
from software.pqc_drbg.errors import DRBGError, FailStopError, ReseedRequiredError
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
def test_sponge_adapter_same_seed_same_output():
    a = MultiplexedSpongeAdapter(sponge_factory=dummy_sponge_factory)
    b = MultiplexedSpongeAdapter(sponge_factory=dummy_sponge_factory)

    seed = encode_conditioner_seed_for_drbg(b"seed-sponge-001")
    a.instantiate(seed)
    b.instantiate(seed)

    assert a.generate(64) == b.generate(64)


def test_sponge_adapter_reseed_changes_output(sponge_engine: MultiplexedSpongeAdapter):
    sponge_engine.instantiate(encode_conditioner_seed_for_drbg(b"seed-sponge-before"))

    out_before = sponge_engine.generate(64)
    sponge_engine.reseed(encode_conditioner_seed_for_drbg(b"seed-sponge-after"))
    out_after = sponge_engine.generate(64)

    assert out_before != out_after


def test_sponge_adapter_generate_length(sponge_engine: MultiplexedSpongeAdapter):
    sponge_engine.instantiate(encode_conditioner_seed_for_drbg(b"seed-sponge-length"))
    out = sponge_engine.generate(33)

    assert isinstance(out, bytes)
    assert len(out) == 33


def test_composite_uses_sponge_by_default():
    drbg = PQCCompositeDRBG()
    drbg.instantiate(encode_conditioner_seed_for_drbg(b"seed-default"))

    out = drbg.generate(32)
    exported = drbg.export_state()

    assert isinstance(out, bytes)
    assert len(out) == 32
    assert exported["manager_state"]["active_engine"] == "multiplexed_sponge"


def test_composite_export_state_is_structured():
    drbg = PQCCompositeDRBG()
    drbg.instantiate(encode_conditioner_seed_for_drbg(b"seed-export-composite"))

    state = drbg.export_state()

    assert "manager_state" in state
    assert "policy" in state
    assert "active_engine_state" in state
    assert state["manager_state"]["initialized"] is True
    assert state["policy"]["selection_mode"] == EngineSelectionMode.STRICT_SPONGE_ONLY.value


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
    drbg.instantiate(encode_conditioner_seed_for_drbg(b"seed-zeroize-manager"))
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
    drbg.instantiate(encode_conditioner_seed_for_drbg(b"seed-reseed-policy"))

    assert len(drbg.generate(16)) == 16

    with pytest.raises(ReseedRequiredError):
        drbg.generate(16)


def test_manual_reseed_clears_reseed_required_flag():
    policy = DRBGPolicy(
        selection_mode=EngineSelectionMode.STRICT_SPONGE_ONLY,
        reseed_interval_requests=1,
    )
    drbg = PQCCompositeDRBG(policy=policy)
    drbg.instantiate(encode_conditioner_seed_for_drbg(b"seed-manual-reseed"))
    _ = drbg.generate(16)

    with pytest.raises(ReseedRequiredError):
        drbg.generate(16)

    drbg.reseed(encode_conditioner_seed_for_drbg(b"fresh-seed"), reason="test_reseed")

    out = drbg.generate(16)
    assert len(out) == 16
    assert drbg.export_state()["manager_state"]["last_reseed_reason"] == "test_reseed"


def test_prediction_resistance_forces_reseed_immediately():
    policy = DRBGPolicy(
        selection_mode=EngineSelectionMode.STRICT_SPONGE_ONLY,
        prediction_resistance=True,
    )
    drbg = PQCCompositeDRBG(policy=policy)
    drbg.instantiate(encode_conditioner_seed_for_drbg(b"seed-prediction-resistance"))

    with pytest.raises(ReseedRequiredError):
        drbg.generate(16)


def test_fail_stop_if_active_engine_health_fails():
    drbg = PQCCompositeDRBG()
    drbg.instantiate(encode_conditioner_seed_for_drbg(b"seed-fail-stop"))

    drbg.sponge_engine.zeroize()

    with pytest.raises(FailStopError):
        drbg.generate(16)

    exported = drbg.export_state()
    assert exported["manager_state"]["flags"]["fail_stop"] is True


def test_strict_mode_enters_fail_stop_on_runtime_failure():
    sponge = MultiplexedSpongeAdapter(sponge_factory=dummy_sponge_factory)
    sponge.instantiate(encode_conditioner_seed_for_drbg(b"seed-sponge-ready"))

    policy = DRBGPolicy(selection_mode=EngineSelectionMode.STRICT_SPONGE_ONLY)
    drbg = PQCCompositeDRBG(sponge_engine=sponge, policy=policy)
    drbg.instantiate(encode_conditioner_seed_for_drbg(b"seed-strict-mode"))

    def failing_generate(nbytes, additional_input=b""):
        raise RuntimeError("panne technique simulee")

    drbg.sponge_engine.generate = failing_generate

    with pytest.raises(FailStopError):
        drbg.generate(16)

    exported = drbg.export_state()
    assert exported["manager_state"]["active_engine"] == "multiplexed_sponge"
    assert exported["manager_state"]["lifecycle_state"] == "fail_stop"


def test_runtime_failure_enters_fail_stop_without_fallback():
    drbg = PQCCompositeDRBG()
    drbg.instantiate(encode_conditioner_seed_for_drbg(b"seed-runtime-failure"))

    def failing_generate(nbytes, additional_input=b""):
        raise RuntimeError("indisponibilite technique simulee")

    drbg.sponge_engine.generate = failing_generate

    with pytest.raises(FailStopError):
        drbg.generate(24)

    exported = drbg.export_state()
    assert exported["manager_state"]["lifecycle_state"] == "fail_stop"


def test_sponge_adapter_rejects_seed_material_not_issued_by_conditioner():
    engine = MultiplexedSpongeAdapter(sponge_factory=dummy_sponge_factory)

    with pytest.raises(DRBGError, match="conditionneur"):
        engine.instantiate(b"seed-brut-interdit")
