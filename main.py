from __future__ import annotations

"""
main.py — Démonstration canonique et pédagogique du projet
« Déploiement d'un RNG Mobile Post-Quantique »

Ce fichier montre, dans un seul point d'entrée, tout le pipeline :

    SRC -> COND -> DRBG -> STATE

avec :
- SRC  : CPU jitter + capteurs inertiels simulés
- COND : Toeplitz + SHAKE-256
- DRBG :
    * moteur nominal Module-LWR
    * moteur secondaire Multiplexed Sponge
    * gestionnaire composite PQCCompositeDRBG
- STATE : scellement / restauration via TEE simulé

Important :
- ce fichier est une démonstration intégrée, lisible et académique ;
- il n'est pas encore une API mobile finale ni un service web ;
- il sert à visualiser la chaîne complète du mémoire dans un seul exécutable.
"""

import hashlib
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Bootstrap du projet
# ---------------------------------------------------------------------------
PROJET_RACINE = Path(__file__).resolve().parent
if str(PROJET_RACINE) not in sys.path:
    sys.path.insert(0, str(PROJET_RACINE))

RUNTIME_DIR = PROJET_RACINE / "demo" / ".runtime" / "main_demo"
RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

from software.conditioner import ConditioningResult, EntropyMixer
from software.entropy import CPUJitterSource, EntropyPool, SensorEntropySource
from software.lfsr import RecurrenceSequence
from software.pqc_drbg import (
    DRBGPolicy,
    EngineSelectionMode,
    PQCCompositeDRBG,
)
from software.pqc_drbg.lwr_core import ModuleLWRCore
from software.pqc_drbg.sponge_core import MultiplexedSpongeAdapter
from software.sponge import MultiplexedSponge
from software.state_manager import SimulatedTEE, StateManager


# ---------------------------------------------------------------------------
# Configuration de démonstration
# ---------------------------------------------------------------------------
@dataclass(slots=True)
class DemoConfig:
    """Configuration unique et lisible de la démo complète."""

    cpu_sample_count: int = 64
    cpu_inner_loops: int = 64
    cpu_lsb_count: int = 2
    cpu_warmup_rounds: int = 8

    sensor_frame_count: int = 16
    sensor_lsb_count: int = 2

    pool_target_min_entropy_bits: float = 8.0
    pool_target_min_symbols: int = 32

    toeplitz_output_bits: int = 256
    shake_output_bytes: int = 32

    lfsr_degree: int = 16
    sponge_l: int = 4
    sponge_rate: int = 128
    sponge_capacity: int = 128

    lwr_output_bytes: int = 32
    sponge_output_bytes: int = 32
    composite_output_bytes: int = 24

    tee_namespace: str = "memoire-pqc"
    tee_device_id: str = "jury-device"


# ---------------------------------------------------------------------------
# Outils d'affichage
# ---------------------------------------------------------------------------
def hr(char: str = "=") -> None:
    print(char * 88)


def title(text: str) -> None:
    print()
    hr("=")
    print(text)
    hr("=")


def subtitle(text: str) -> None:
    print()
    hr("-")
    print(text)
    hr("-")


def line(label: str, value: Any) -> None:
    print(f"{label:<32}: {value}")


def short_hex(data: bytes | bytearray | None, max_bytes: int = 24) -> str:
    if not data:
        return ""
    data = bytes(data)
    if len(data) <= max_bytes:
        return data.hex()
    return f"{data[:max_bytes].hex()}... ({len(data)} octets)"


def short_json(value: Any, max_lines: int = 12) -> str:
    text = json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True)
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text
    return "\n".join(lines[:max_lines]) + "\n..."


# ---------------------------------------------------------------------------
# Construction du moteur sponge secondaire
# ---------------------------------------------------------------------------
def build_research_sponge(seed_digest: bytes, config: DemoConfig) -> MultiplexedSponge:
    """
    Construit une vraie instance du Multiplexed Sponge de recherche.

    On dérive deux séquences de récurrence depuis le digest, puis on absorbe
    un matériau initial afin de relier l'état du sponge à `Seedinit`.
    """

    max_seed = (1 << config.lfsr_degree) - 1
    graine_s = (int.from_bytes(seed_digest[:2], "big") % max_seed) + 1
    graine_t = (int.from_bytes(seed_digest[2:4], "big") % max_seed) + 1

    sequence_s = RecurrenceSequence(degree=config.lfsr_degree, seed=graine_s)
    sequence_t = RecurrenceSequence(degree=config.lfsr_degree, seed=graine_t)

    sponge = MultiplexedSponge(
        seq_s=sequence_s,
        seq_t=sequence_t,
        l=config.sponge_l,
        rate=config.sponge_rate,
        capacity=config.sponge_capacity,
    )

    material = hashlib.shake_256(b"main-demo-sponge:" + seed_digest).digest(32)
    blocks = [int.from_bytes(material[i:i + 8], "big") for i in range(0, 32, 8)]
    sponge.absorb_blocks(blocks, block_size=64)
    return sponge


def build_sponge_adapter(config: DemoConfig) -> MultiplexedSpongeAdapter:
    """Adaptateur DRBG pour le moteur secondaire Multiplexed Sponge."""

    return MultiplexedSpongeAdapter(
        sponge_factory=lambda seed_digest: build_research_sponge(seed_digest, config)
    )


# ---------------------------------------------------------------------------
# Étape SRC
# ---------------------------------------------------------------------------
def build_src_pool(config: DemoConfig) -> dict[str, Any]:
    """Collecte l'entropie brute depuis CPU jitter et capteurs simulés."""

    cpu = CPUJitterSource(
        sample_count=config.cpu_sample_count,
        inner_loops=config.cpu_inner_loops,
        lsb_count=config.cpu_lsb_count,
        warmup_rounds=config.cpu_warmup_rounds,
    )
    sensor = SensorEntropySource(
        frame_count=config.sensor_frame_count,
        lsb_count=config.sensor_lsb_count,
    )
    pool = EntropyPool(
        target_min_entropy_bits=config.pool_target_min_entropy_bits,
        target_min_symbols=config.pool_target_min_symbols,
    )

    cpu_chunk = cpu.collect()
    cpu_report = pool.add_chunk(cpu_chunk)

    sensor_chunk = sensor.collect()
    sensor_report = pool.add_chunk(sensor_chunk)

    snapshot = pool.snapshot()

    subtitle("1) SRC — Collecte de l'entropie brute")
    line("Architecture", "SRC -> COND -> DRBG -> STATE")
    line("Source 1", cpu_chunk.source_name)
    line("Source 1 : symboles", cpu_chunk.sample_count)
    line("Source 1 : octets bruts", len(cpu_chunk.raw_bytes))
    line("Source 1 : santé acceptée", cpu_report.accepted)
    line("Source 1 : min-entropie", round(cpu_report.min_entropy_per_symbol, 4))

    line("Source 2", sensor_chunk.source_name)
    line("Source 2 : symboles", sensor_chunk.sample_count)
    line("Source 2 : octets bruts", len(sensor_chunk.raw_bytes))
    line("Source 2 : santé acceptée", sensor_report.accepted)
    line("Source 2 : min-entropie", round(sensor_report.min_entropy_per_symbol, 4))

    line("Pool prêt ?", snapshot.ready)
    line("Pool : chunks acceptés", snapshot.accepted_chunks)
    line("Pool : total symboles", snapshot.total_symbols)
    line("Pool : total octets", snapshot.total_raw_bytes)
    line("Pool : min-entropie totale", round(snapshot.estimated_min_entropy_bits, 4))
    line("Aperçu raw_data", short_hex(pool.export_raw_bytes()))

    return {
        "cpu_chunk": cpu_chunk,
        "cpu_report": cpu_report,
        "sensor_chunk": sensor_chunk,
        "sensor_report": sensor_report,
        "pool": pool,
        "snapshot": snapshot,
    }


# ---------------------------------------------------------------------------
# Étape COND
# ---------------------------------------------------------------------------
def build_cond_seed(pool: EntropyPool, config: DemoConfig) -> ConditioningResult:
    """Conditionne le matériau brut via Toeplitz puis SHAKE-256."""

    mixer = EntropyMixer(
        toeplitz_output_bits=config.toeplitz_output_bits,
        shake_output_bytes=config.shake_output_bytes,
    )

    result = mixer.condition_from_pool(
        pool,
        personalization=b"memoire-rng-mobile-pqc",
        extra_context=b"main.py-canonical-demo",
    )

    subtitle("2) COND — Toeplitz + SHAKE-256")
    line("Raw_Data", short_hex(result.raw_data))
    line("Toeplitz seed", short_hex(result.toeplitz_seed))
    line("Toeplitz output", short_hex(result.toeplitz_output))
    line("Context_Info", result.context_info.decode("utf-8", errors="replace"))
    line("Seedinit", short_hex(result.seedinit))
    line("Input bits", result.input_bits)
    line("Output bits", result.output_bits)

    return result


# ---------------------------------------------------------------------------
# Étape DRBG — Module-LWR
# ---------------------------------------------------------------------------
def run_module_lwr(seedinit: bytes, config: DemoConfig) -> dict[str, Any]:
    """Montre le moteur nominal Module-LWR de bout en bout."""

    lwr = ModuleLWRCore()
    lwr.instantiate(seedinit, personalization=b"main-demo-lwr")

    before = lwr.generate(config.lwr_output_bytes)
    state_before = lwr.export_state()

    reseed_seed = hashlib.shake_256(seedinit + b"main-demo-lwr-reseed").digest(32)
    lwr.reseed(reseed_seed, additional_input=b"main-demo-reseed-context")
    after = lwr.generate(config.lwr_output_bytes)
    state_after = lwr.export_state()

    subtitle("3) DRBG nominal — Module-LWR")
    line("Sortie avant reseed", short_hex(before))
    line("Sortie après reseed", short_hex(after))
    line("Flux changé après reseed ?", before != after)
    line("Santé moteur", lwr.health().healthy)
    line("État exporté", short_json(state_after, max_lines=16))

    return {
        "engine": lwr,
        "output_before_reseed": before,
        "output_after_reseed": after,
        "state_before": state_before,
        "state_after": state_after,
    }


# ---------------------------------------------------------------------------
# Étape DRBG — Multiplexed Sponge
# ---------------------------------------------------------------------------
def run_multiplexed_sponge(seedinit: bytes, lwr_reference: bytes, config: DemoConfig) -> dict[str, Any]:
    """Montre le moteur secondaire Multiplexed Sponge."""

    sponge = build_sponge_adapter(config)
    sponge.instantiate(seedinit, personalization=b"main-demo-sponge")
    output = sponge.generate(config.sponge_output_bytes, additional_input=b"main-demo-research")
    state = sponge.export_state()

    subtitle("4) DRBG secondaire — Multiplexed Sponge")
    line("Sortie sponge", short_hex(output))
    line("Même flux que LWR ?", output == lwr_reference)
    line("Santé moteur", sponge.health().healthy)
    line("État exporté", short_json(state, max_lines=16))
    print("Remarque : ce moteur reste secondaire / recherche, pas nominal.")

    return {
        "engine": sponge,
        "output": output,
        "state": state,
    }


# ---------------------------------------------------------------------------
# Gestionnaire composite
# ---------------------------------------------------------------------------
def run_composite_manager(seedinit: bytes, config: DemoConfig) -> dict[str, Any]:
    """Compare les trois usages principaux du gestionnaire composite."""

    strict = PQCCompositeDRBG(
        sponge_engine=build_sponge_adapter(config),
        policy=DRBGPolicy(selection_mode=EngineSelectionMode.STRICT_LWR_ONLY),
    )
    strict.instantiate(seedinit)
    strict_output = strict.generate(config.composite_output_bytes)

    research = PQCCompositeDRBG(
        sponge_engine=build_sponge_adapter(config),
        policy=DRBGPolicy(selection_mode=EngineSelectionMode.FORCE_SPONGE_RESEARCH),
    )
    research.instantiate(seedinit)
    research_output = research.generate(config.composite_output_bytes)

    fallback = PQCCompositeDRBG(
        sponge_engine=build_sponge_adapter(config),
        policy=DRBGPolicy(
            selection_mode=EngineSelectionMode.ALLOW_EXPERIMENTAL_SPONGE_FALLBACK,
            allow_fallback_on_unavailability_only=True,
        ),
    )
    fallback.sponge_engine.instantiate(
        hashlib.shake_256(seedinit + b"fallback-sponge-ready").digest(32),
        personalization=b"main-demo-fallback-ready",
    )
    fallback.instantiate(seedinit)

    # Simule une indisponibilité technique du moteur LWR pour démontrer le fallback.
    def unavailable_generate(nbytes: int, additional_input: bytes = b"") -> bytes:
        raise RuntimeError("Indisponibilité technique simulée du moteur LWR.")

    fallback.lwr_engine.generate = unavailable_generate  # type: ignore[method-assign]
    fallback_output = fallback.generate(config.composite_output_bytes)

    subtitle("5) Gestionnaire composite — modes de politique")
    line("Mode strict : moteur actif", strict.export_state()["manager_state"]["active_engine"])
    line("Mode strict : sortie", short_hex(strict_output, max_bytes=16))
    line("Mode recherche : moteur actif", research.export_state()["manager_state"]["active_engine"])
    line("Mode recherche : sortie", short_hex(research_output, max_bytes=16))
    line("Mode fallback : moteur actif", fallback.export_state()["manager_state"]["active_engine"])
    line("Mode fallback : sortie", short_hex(fallback_output, max_bytes=16))

    return {
        "strict": strict.export_state(),
        "research": research.export_state(),
        "fallback": fallback.export_state(),
    }


# ---------------------------------------------------------------------------
# Étape STATE
# ---------------------------------------------------------------------------
def run_state_layer(seedinit: bytes, config: DemoConfig) -> dict[str, Any]:
    """Scelle et restaure un payload simple puis un état complet de DRBG."""

    tee_root = RUNTIME_DIR / "state_demo"
    tee = SimulatedTEE(
        root_dir=tee_root,
        device_id=config.tee_device_id,
        namespace=config.tee_namespace,
    )

    # A. Payload simple
    payload_manager = StateManager(tee=tee, blob_id="demo_payload")
    simple_payload = {
        "pipeline": "SRC->COND->DRBG->STATE",
        "active_engine": "module_lwr",
        "seedinit_prefix": seedinit[:8].hex(),
        "demo": True,
    }
    simple_metadata = {"purpose": "simple-payload"}
    blob_simple = payload_manager.seal_payload(simple_payload, payload_metadata=simple_metadata)
    restored_simple = payload_manager.unseal_payload(payload_metadata=simple_metadata)

    # B. Checkpoint complet du DRBG composite
    drbg = PQCCompositeDRBG(
        sponge_engine=build_sponge_adapter(config),
        policy=DRBGPolicy(selection_mode=EngineSelectionMode.STRICT_LWR_ONLY),
    )
    drbg.instantiate(seedinit)
    _ = drbg.generate(16)

    drbg_manager = StateManager(tee=tee, blob_id="demo_drbg")
    blob_drbg = drbg_manager.checkpoint_drbg(drbg, payload_metadata={"purpose": "drbg-checkpoint"})

    restored_drbg = PQCCompositeDRBG(
        sponge_engine=build_sponge_adapter(config),
        policy=DRBGPolicy(selection_mode=EngineSelectionMode.STRICT_LWR_ONLY),
    )
    restored_payload = drbg_manager.restore_drbg(
        restored_drbg,
        payload_metadata={"purpose": "drbg-checkpoint"},
    )

    subtitle("6) STATE — Seal / Unseal / Restore")
    line("TEE device_id", tee.device_id)
    line("TEE namespace", tee.namespace)
    line("Compteur matériel", tee.hardware_counter)
    line("Blob payload simple", blob_simple.blob_id)
    line("Payload restauré", restored_simple)
    line("Blob DRBG", blob_drbg.blob_id)
    line("DRBG restauré : moteur actif", restored_payload["manager_state"]["active_engine"])
    line("DRBG restauré : état", restored_drbg.export_state()["manager_state"]["lifecycle_state"])

    return {
        "tee_status": asdict(tee.status()),
        "simple_blob_id": blob_simple.blob_id,
        "simple_payload_restored": restored_simple,
        "drbg_blob_id": blob_drbg.blob_id,
        "drbg_restored_state": restored_drbg.export_state(),
    }


# ---------------------------------------------------------------------------
# Résumé final
# ---------------------------------------------------------------------------
def print_summary(summary: dict[str, Any]) -> None:
    subtitle("7) Résumé final")
    print(short_json(summary, max_lines=40))


# ---------------------------------------------------------------------------
# Programme principal
# ---------------------------------------------------------------------------
def main() -> None:
    """Exécute toute la démonstration de bout en bout."""

    config = DemoConfig()

    title("DEMONSTRATION COMPLETE — RNG MOBILE POST-QUANTIQUE")
    print("Objectif : visualiser clairement SRC -> COND -> DRBG -> STATE dans un seul main.py")
    print("Moteur nominal   : Module-LWR")
    print("Moteur secondaire: Multiplexed Sponge")
    print("Conditionneur    : Toeplitz + SHAKE-256")
    print("STATE            : TEE simulé + scellement / restauration")

    src = build_src_pool(config)
    cond = build_cond_seed(src["pool"], config)
    lwr = run_module_lwr(cond.seedinit, config)
    sponge = run_multiplexed_sponge(cond.seedinit, lwr["output_after_reseed"], config)
    composite = run_composite_manager(cond.seedinit, config)
    state = run_state_layer(cond.seedinit, config)

    summary = {
        "architecture": "SRC -> COND -> DRBG -> STATE",
        "seedinit_hex": cond.seedinit.hex(),
        "module_lwr": {
            "output_before_reseed_hex": lwr["output_before_reseed"].hex(),
            "output_after_reseed_hex": lwr["output_after_reseed"].hex(),
            "exported_state": lwr["state_after"],
        },
        "multiplexed_sponge": {
            "output_hex": sponge["output"].hex(),
            "exported_state": sponge["state"],
        },
        "composite_manager": composite,
        "state_layer": state,
    }
    print_summary(summary)


if __name__ == "__main__":
    main()
