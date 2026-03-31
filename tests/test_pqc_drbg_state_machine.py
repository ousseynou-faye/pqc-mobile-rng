import pytest

from software.pqc_drbg.drbg_engine import PQCCompositeDRBG
from software.pqc_drbg.errors import DRBGError, FailStopError, ReseedRequiredError
from software.pqc_drbg.policy import DRBGPolicy, EngineSelectionMode
from software.pqc_drbg.sponge_core import MultiplexedSpongeAdapter
from software.pqc_drbg.state import DRBGLifecycleState


class DummySponge:
    """Moteur sponge minimal pour tester la machine a etats."""

    def __init__(self, seed_digest: bytes):
        self._seed = seed_digest

    def squeeze_bytes(self, nbytes: int) -> bytes:
        return (self._seed * ((nbytes // len(self._seed)) + 1))[:nbytes]


def dummy_sponge_factory(seed_digest: bytes):
    return DummySponge(seed_digest)


def test_initial_state_is_uninitialized():
    drbg = PQCCompositeDRBG()
    assert drbg.state.lifecycle_state == DRBGLifecycleState.UNINITIALIZED


def test_instantiate_moves_to_ready():
    drbg = PQCCompositeDRBG()
    drbg.instantiate(b"seed-1")
    assert drbg.state.lifecycle_state == DRBGLifecycleState.READY


def test_reseed_limit_moves_to_need_reseed():
    policy = DRBGPolicy(
        selection_mode=EngineSelectionMode.STRICT_SPONGE_ONLY,
        reseed_interval_requests=1,
    )
    drbg = PQCCompositeDRBG(policy=policy)
    drbg.instantiate(b"seed-2")

    _ = drbg.generate(8)

    with pytest.raises(ReseedRequiredError):
        drbg.generate(8)

    assert drbg.state.lifecycle_state == DRBGLifecycleState.NEED_RESEED


def test_reseed_returns_to_ready():
    policy = DRBGPolicy(
        selection_mode=EngineSelectionMode.STRICT_SPONGE_ONLY,
        reseed_interval_requests=1,
    )
    drbg = PQCCompositeDRBG(policy=policy)
    drbg.instantiate(b"seed-3")

    _ = drbg.generate(8)

    with pytest.raises(ReseedRequiredError):
        drbg.generate(8)

    drbg.reseed(b"fresh-seed")
    assert drbg.state.lifecycle_state == DRBGLifecycleState.READY


def test_health_failure_moves_to_fail_stop():
    drbg = PQCCompositeDRBG()
    drbg.instantiate(b"seed-4")
    drbg.sponge_engine.zeroize()

    with pytest.raises(FailStopError):
        drbg.generate(8)

    assert drbg.state.lifecycle_state == DRBGLifecycleState.FAIL_STOP


def test_fail_stop_blocks_generation():
    drbg = PQCCompositeDRBG()
    drbg.instantiate(b"seed-5")
    drbg.signal_integrity_failure("test integrity break")

    with pytest.raises(FailStopError):
        drbg.generate(8)


def test_zeroize_moves_to_zeroized():
    drbg = PQCCompositeDRBG()
    drbg.instantiate(b"seed-6")
    drbg.zeroize()

    assert drbg.state.lifecycle_state == DRBGLifecycleState.ZEROIZED


def test_invalid_reseed_from_uninitialized_is_rejected():
    drbg = PQCCompositeDRBG()

    with pytest.raises(DRBGError):
        drbg.reseed(b"fresh-seed")


def test_reset_from_fail_stop_returns_to_uninitialized():
    drbg = PQCCompositeDRBG()
    drbg.instantiate(b"seed-7")
    drbg.signal_integrity_failure("manual fail stop")

    assert drbg.state.lifecycle_state == DRBGLifecycleState.FAIL_STOP

    drbg.reset_from_fail_stop("operator reset")
    assert drbg.state.lifecycle_state == DRBGLifecycleState.UNINITIALIZED


def test_force_lwr_research_starts_in_ready():
    sponge = MultiplexedSpongeAdapter(sponge_factory=dummy_sponge_factory)
    policy = DRBGPolicy(selection_mode=EngineSelectionMode.FORCE_LWR_RESEARCH)
    drbg = PQCCompositeDRBG(sponge_engine=sponge, policy=policy)

    drbg.instantiate(b"seed-8")
    assert drbg.state.lifecycle_state == DRBGLifecycleState.READY
    assert drbg.state.flags.degraded_research is True
