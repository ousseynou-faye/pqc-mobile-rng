import hashlib
import pytest

from software.pqc_drbg.drbg_engine import PQCCompositeDRBG
from software.pqc_drbg.errors import DRBGError, FailStopError, ReseedRequiredError
from software.pqc_drbg.lwr_core import ModuleLWRCore
from software.pqc_drbg.policy import DRBGPolicy, EngineSelectionMode
from software.pqc_drbg.sponge_core import MultiplexedSpongeAdapter
from software.pqc_drbg.state import DRBGState, DRBGStatus


class DummySponge:
    """
    Je simule ici un moteur sponge minimal pour tester l'adaptateur DRBG.

    Cette classe ne remplace pas mon vrai Multiplexed Sponge.
    Je m'en sers seulement pour vérifier :
    - l'initialisation,
    - le déterminisme,
    - la génération,
    - le reseed,
    - l'intégration avec le gestionnaire composite.
    """

    def __init__(self, seed_digest: bytes):
        self._seed = seed_digest
        self._counter = 0

    def squeeze_bytes(self, nbytes: int) -> bytes:
        """
        Je génère ici un flux déterministe à partir de la seed.
        """
        if nbytes < 0:
            raise ValueError("nbytes doit être >= 0.")

        out = bytearray()

        while len(out) < nbytes:
            block = hashlib.shake_256(
                b"dummy_sponge_block:"
                + self._seed
                + self._counter.to_bytes(8, "big")
            ).digest(32)
            out.extend(block)
            self._counter += 1

        return bytes(out[:nbytes])


def dummy_sponge_factory(seed_digest: bytes) -> DummySponge:
    """
    Je construis ici une instance DummySponge pour les tests.
    """
    return DummySponge(seed_digest)


@pytest.fixture
def sponge_engine() -> MultiplexedSpongeAdapter:
    """
    Je fournis ici un moteur sponge réutilisable dans plusieurs tests.
    """
    return MultiplexedSpongeAdapter(sponge_factory=dummy_sponge_factory)


# ============================================================
# Tests du moteur Module-LWR seul
# ============================================================

def test_lwr_same_seed_same_output():
    """
    Je vérifie ici que le moteur Module-LWR est déterministe :
    même seed => même flux.
    """
    a = ModuleLWRCore()
    b = ModuleLWRCore()

    seed = b"seed-lwr-001"
    a.instantiate(seed)
    b.instantiate(seed)

    out_a = a.generate(64)
    out_b = b.generate(64)

    assert out_a == out_b


def test_lwr_different_seed_different_output():
    """
    Je vérifie ici que deux seeds différentes donnent des sorties différentes.
    """
    a = ModuleLWRCore()
    b = ModuleLWRCore()

    a.instantiate(b"seed-lwr-A")
    b.instantiate(b"seed-lwr-B")

    out_a = a.generate(64)
    out_b = b.generate(64)

    assert out_a != out_b


def test_lwr_generate_returns_expected_length():
    """
    Je vérifie ici que la longueur de sortie demandée est bien respectée.
    """
    engine = ModuleLWRCore()
    engine.instantiate(b"seed-length")

    out = engine.generate(100)

    assert isinstance(out, bytes)
    assert len(out) == 100


def test_lwr_reseed_changes_stream():
    """
    Je vérifie ici qu'un reseed modifie effectivement le flux produit.
    """
    engine = ModuleLWRCore()
    engine.instantiate(b"seed-before-reseed")

    out_before = engine.generate(64)
    engine.reseed(b"seed-after-reseed")
    out_after = engine.generate(64)

    assert out_before != out_after


def test_lwr_zeroize_blocks_generation():
    """
    Je vérifie ici qu'après zeroize, le moteur n'est plus utilisable
    tant qu'il n'a pas été réinitialisé.
    """
    engine = ModuleLWRCore()
    engine.instantiate(b"seed-zeroize")
    engine.zeroize()

    with pytest.raises(DRBGError):
        engine.generate(16)


def test_lwr_export_state_contains_expected_fields():
    """
    Je vérifie ici que l'état exporté contient bien les champs essentiels.
    """
    engine = ModuleLWRCore()
    engine.instantiate(b"seed-export")

    state = engine.export_state()

    assert state["name"] == "module_lwr"
    assert state["initialized"] is True
    assert "counter" in state
    assert "modulus_q" in state
    assert "rounding_modulus_p" in state


# ============================================================
# Tests du moteur Multiplexed Sponge via l'adaptateur
# ============================================================

def test_sponge_adapter_same_seed_same_output(sponge_engine: MultiplexedSpongeAdapter):
    """
    Je vérifie ici que l'adaptateur sponge reste déterministe :
    même seed => même sortie.
    """
    a = MultiplexedSpongeAdapter(sponge_factory=dummy_sponge_factory)
    b = MultiplexedSpongeAdapter(sponge_factory=dummy_sponge_factory)

    seed = b"seed-sponge-001"
    a.instantiate(seed)
    b.instantiate(seed)

    out_a = a.generate(64)
    out_b = b.generate(64)

    assert out_a == out_b


def test_sponge_adapter_reseed_changes_output(sponge_engine: MultiplexedSpongeAdapter):
    """
    Je vérifie ici qu'un reseed modifie la sortie du moteur sponge.
    """
    sponge_engine.instantiate(b"seed-sponge-before")

    out_before = sponge_engine.generate(64)
    sponge_engine.reseed(b"seed-sponge-after")
    out_after = sponge_engine.generate(64)

    assert out_before != out_after


def test_sponge_adapter_generate_length(sponge_engine: MultiplexedSpongeAdapter):
    """
    Je vérifie ici que l'adaptateur sponge retourne la bonne longueur.
    """
    sponge_engine.instantiate(b"seed-sponge-length")

    out = sponge_engine.generate(33)

    assert isinstance(out, bytes)
    assert len(out) == 33


# ============================================================
# Tests du gestionnaire composite
# ============================================================

def test_composite_uses_lwr_by_default():
    """
    Je vérifie ici que le moteur nominal est bien Module-LWR par défaut.
    """
    drbg = PQCCompositeDRBG()
    drbg.instantiate(b"seed-default")

    out = drbg.generate(32)
    exported = drbg.export_state()

    assert isinstance(out, bytes)
    assert len(out) == 32
    assert exported["manager_state"]["active_engine"] == "module_lwr"


def test_composite_export_state_is_structured():
    """
    Je vérifie ici que l'état exporté du gestionnaire composite est bien structuré.
    """
    drbg = PQCCompositeDRBG()
    drbg.instantiate(b"seed-export-composite")

    state = drbg.export_state()

    assert "manager_state" in state
    assert "policy" in state
    assert "active_engine_state" in state
    assert state["manager_state"]["initialized"] is True


def test_state_initialized_setter_stays_backward_compatible():
    """
    Je vérifie ici que l'ancien code peut encore écrire `state.initialized`.
    """
    state = DRBGState()

    state.initialized = True
    assert state.initialized is True
    assert state.status == DRBGStatus.READY

    state.initialized = False
    assert state.initialized is False
    assert state.status == DRBGStatus.UNINITIALIZED


def test_composite_zeroize_resets_manager_state():
    """
    Je vérifie ici que zeroize remet le gestionnaire dans un état propre.
    """
    drbg = PQCCompositeDRBG()
    drbg.instantiate(b"seed-zeroize-manager")
    _ = drbg.generate(16)

    drbg.zeroize()
    state = drbg.export_state()

    assert state["manager_state"]["initialized"] is False
    assert state["manager_state"]["active_engine"] is None


def test_reseed_interval_requests_forces_reseed():
    """
    Je vérifie ici qu'une politique de reseed par compteur est bien respectée.
    """
    policy = DRBGPolicy(
        selection_mode=EngineSelectionMode.STRICT_LWR_ONLY,
        reseed_interval_requests=1,
    )
    drbg = PQCCompositeDRBG(policy=policy)
    drbg.instantiate(b"seed-reseed-policy")

    # Première requête : autorisée
    out1 = drbg.generate(16)
    assert len(out1) == 16

    # Deuxième requête : doit forcer un reseed
    with pytest.raises(ReseedRequiredError):
        drbg.generate(16)


def test_manual_reseed_clears_reseed_required_flag():
    """
    Je vérifie ici qu'un reseed remet le compteur dans un état exploitable.
    """
    policy = DRBGPolicy(
        selection_mode=EngineSelectionMode.STRICT_LWR_ONLY,
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
    """
    Je vérifie ici qu'en mode prediction resistance, une génération sans reseed
    préalable est refusée.
    """
    policy = DRBGPolicy(
        selection_mode=EngineSelectionMode.STRICT_LWR_ONLY,
        prediction_resistance=True,
    )
    drbg = PQCCompositeDRBG(policy=policy)
    drbg.instantiate(b"seed-prediction-resistance")

    with pytest.raises(ReseedRequiredError):
        drbg.generate(16)


def test_force_sponge_research_mode_uses_sponge_engine(sponge_engine: MultiplexedSpongeAdapter):
    """
    Je vérifie ici que le mode de recherche force bien le moteur sponge.
    """
    policy = DRBGPolicy(
        selection_mode=EngineSelectionMode.FORCE_SPONGE_RESEARCH,
    )
    drbg = PQCCompositeDRBG(
        sponge_engine=sponge_engine,
        policy=policy,
    )

    drbg.instantiate(b"seed-force-sponge")
    out = drbg.generate(20)

    assert len(out) == 20
    assert drbg.export_state()["manager_state"]["active_engine"] == "multiplexed_sponge"


def test_fail_stop_if_active_engine_health_fails():
    """
    Je vérifie ici qu'un moteur actif non sain déclenche bien FAIL_STOP.
    """
    drbg = PQCCompositeDRBG()
    drbg.instantiate(b"seed-fail-stop")

    # Je rends volontairement le moteur LWR non sain.
    drbg.lwr_engine.zeroize()

    with pytest.raises(FailStopError):
        drbg.generate(16)

    exported = drbg.export_state()
    assert exported["manager_state"]["flags"]["fail_stop"] is True


def test_strict_mode_does_not_silently_fallback_to_sponge():
    """
    Je vérifie ici qu'en mode strict, un problème technique du moteur nominal
    n'entraîne pas de bascule silencieuse vers sponge.
    """
    sponge = MultiplexedSpongeAdapter(sponge_factory=dummy_sponge_factory)
    sponge.instantiate(b"seed-sponge-ready")

    policy = DRBGPolicy(
        selection_mode=EngineSelectionMode.STRICT_LWR_ONLY,
    )
    drbg = PQCCompositeDRBG(
        sponge_engine=sponge,
        policy=policy,
    )
    drbg.instantiate(b"seed-strict-mode")

    def failing_generate(nbytes, additional_input=b""):
        raise RuntimeError("panne technique simulée")

    drbg.lwr_engine.generate = failing_generate  # monkey patch de test

    with pytest.raises(RuntimeError):
        drbg.generate(16)

    assert drbg.export_state()["manager_state"]["active_engine"] == "module_lwr"


def test_experimental_mode_allows_controlled_fallback_on_runtime_failure():
    """
    Je vérifie ici qu'en mode expérimental, une indisponibilité technique
    non critique peut permettre une bascule contrôlée vers sponge.
    """
    sponge = MultiplexedSpongeAdapter(sponge_factory=dummy_sponge_factory)
    sponge.instantiate(b"seed-sponge-fallback")

    policy = DRBGPolicy(
        selection_mode=EngineSelectionMode.ALLOW_EXPERIMENTAL_SPONGE_FALLBACK,
        allow_fallback_on_unavailability_only=True,
    )
    drbg = PQCCompositeDRBG(
        sponge_engine=sponge,
        policy=policy,
    )
    drbg.instantiate(b"seed-lwr-fallback")

    def failing_generate(nbytes, additional_input=b""):
        raise RuntimeError("indisponibilité technique simulée")

    drbg.lwr_engine.generate = failing_generate  # monkey patch de test

    out = drbg.generate(24)

    assert isinstance(out, bytes)
    assert len(out) == 24
    assert drbg.export_state()["manager_state"]["active_engine"] == "multiplexed_sponge"
