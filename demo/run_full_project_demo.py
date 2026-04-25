from __future__ import annotations

"""Demonstration complete et presentable du pipeline SRC -> COND -> DRBG -> STATE."""

import json
import sys
from dataclasses import asdict, dataclass
from hashlib import shake_256
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT_STR = str(PROJECT_ROOT)
if PROJECT_ROOT_STR not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_STR)

from analysis.entropy_validation import compare_before_after_conditioning
from demo.demo_utils import (
    afficher_ligne,
    afficher_sous_titre,
    afficher_texte,
    afficher_titre,
    format_bits,
    format_hex,
    format_json,
    format_liste,
)
from software.api.output_formats import format_output_bytes
from software.api.rng_service import ConditionerConfig, RNGService, RNGServiceConfig, StateConfig
from software.conditioner import EntropyMixer
from software.entropy import CPUJitterSource, EntropyPool, SensorEntropySource
from software.lfsr import RecurrenceSequence
from software.pqc_drbg.sponge_core import build_reference_sponge
from software.sponge import MultiplexedSequence, derive_sponge_lfsr_seeds
from software.sponge.phi_function import PhiFunction
from software.state_manager import SimulatedTEE


@dataclass(slots=True)
class FullDemoConfig:
    output_bytes: int = 32
    preview_bytes: int = 16
    preview_bits: int = 64
    phi_width: int = 4
    phi_steps: int = 8
    mux_bits: int = 16
    sponge_trace_steps: int = 4
    root_dir: str = "demo/.runtime/full_project_demo"


def _build_runtime_service(config: FullDemoConfig) -> RNGService:
    return RNGService(
        config=RNGServiceConfig(
            conditioner=ConditionerConfig(
                personalization=b"memoire-demo-pqc-mobile-rng",
                extra_context=b"SRC-COND-DRBG-STATE-demo",
                toeplitz_public_seed=b"memoire-demo-toeplitz-public-seed",
            ),
            state=StateConfig(
                root_dir=Path(config.root_dir),
                device_id="memoire-demo-device",
                namespace="memoire-demo",
                blob_id="memoire-demo-blob",
                checkpoint_metadata={"purpose": "memoire_demo_checkpoint"},
            ),
        )
    )


def _json_ready_output(bundle: dict[str, Any]) -> dict[str, Any]:
    serializable = dict(bundle)
    serializable.pop("raw_bytes", None)
    return serializable


def _preview_bytes(data: bytes, *, size: int) -> bytes:
    return bytes(data[:size])


def _format_int_views(value: int, *, bit_width: int | None = None) -> dict[str, Any]:
    width = max(1, bit_width or max(1, value.bit_length()))
    hex_width = max(1, (width + 3) // 4)
    return {
        "decimal": value,
        "hex": f"0x{value:0{hex_width}x}",
        "binary": f"{value:0{width}b}",
    }


def _summarize_bytes(data: bytes, *, preview_bytes: int, preview_bits: int) -> dict[str, Any]:
    return {
        "length_bytes": len(data),
        "length_bits": len(data) * 8,
        "hex": data.hex(),
        "hex_preview": format_hex(data, max_octets=preview_bytes),
        "bits_preview": format_bits(data, max_bits=preview_bits),
        "decimal": int.from_bytes(data, "big", signed=False),
        "raw_byte_values_preview": list(data[:preview_bytes]),
    }


def _build_phi_trace(seed_s: int, seed_t: int, *, degree: int, l: int, steps: int) -> list[dict[str, Any]]:
    seq_s = RecurrenceSequence(degree=degree, seed=seed_s)
    seq_t = RecurrenceSequence(degree=degree, seed=seed_t)
    phi = PhiFunction(sequence_s=seq_s, l=l)

    trace: list[dict[str, Any]] = []
    for index in range(steps):
        s_window = seq_s.peek_bits(l)
        phi_value = phi.compute()
        t_bit = seq_t.peek_bit(offset=phi_value % seq_t.period)
        trace.append(
            {
                "n": index,
                "s_bits": s_window,
                "phi_decimal": phi_value,
                "phi_hex": f"0x{phi_value:x}",
                "phi_binary": f"{phi_value:0{l}b}",
                "selected_t_bit": t_bit,
            }
        )
        seq_s.advance(1)
        seq_t.advance(1)
    return trace


def _build_sponge_trace(seed_digest: bytes, *, steps: int) -> list[dict[str, Any]]:
    sponge = build_reference_sponge(seed_digest)
    trace: list[dict[str, Any]] = []
    for index in range(steps):
        before = sponge.state.get_state()
        block = sponge.squeezer.squeeze_block(8)
        after = sponge.state.get_state()
        trace.append(
            {
                "step": index,
                "state_before_hex": f"0x{before:064x}",
                "block_hex": f"0x{block:02x}",
                "block_decimal": block,
                "block_binary": f"{block:08b}",
                "state_after_hex": f"0x{after:064x}",
            }
        )
    return trace


def run_full_project_demo(config: FullDemoConfig | None = None) -> dict[str, Any]:
    cfg = config or FullDemoConfig()
    service = _build_runtime_service(cfg)

    entropy_cfg = service.config.entropy
    conditioner_cfg = service.config.conditioner

    cpu_chunk = CPUJitterSource(
        sample_count=entropy_cfg.cpu_sample_count,
        inner_loops=entropy_cfg.cpu_inner_loops,
        lsb_count=entropy_cfg.cpu_lsb_count,
        warmup_rounds=entropy_cfg.cpu_warmup_rounds,
    ).collect()
    sensor_chunk = SensorEntropySource(
        frame_count=entropy_cfg.sensor_frame_count,
        lsb_count=entropy_cfg.sensor_lsb_count,
    ).collect()

    pool = EntropyPool(
        target_min_entropy_bits=entropy_cfg.pool_target_min_entropy_bits,
        target_min_symbols=entropy_cfg.pool_target_min_symbols,
        reject_on_fail=entropy_cfg.pool_reject_on_fail,
    )
    cpu_report = pool.add_chunk(cpu_chunk)
    sensor_report = pool.add_chunk(sensor_chunk)

    raw_data = pool.export_raw_bytes()
    conditioner = EntropyMixer(
        toeplitz_output_bits=conditioner_cfg.toeplitz_output_bits,
        shake_output_bytes=conditioner_cfg.shake_output_bytes,
    )
    conditioning = conditioner.condition_from_pool(
        pool,
        personalization=conditioner_cfg.personalization,
        extra_context=conditioner_cfg.extra_context,
        toeplitz_public_seed=conditioner_cfg.toeplitz_public_seed,
    )

    entropy_comparison = compare_before_after_conditioning(
        raw_data,
        conditioner=conditioner,
        personalization=conditioner_cfg.personalization,
        extra_context=conditioner_cfg.extra_context,
        toeplitz_public_seed=conditioner_cfg.toeplitz_public_seed,
    )

    drbg_personalization = service.config.drbg.personalization
    seed_digest = shake_256(b"sponge_init:" + drbg_personalization + conditioning.seedinit).digest(64)
    derived = derive_sponge_lfsr_seeds(
        seed_digest,
        degree_s=16,
        degree_t=16,
        context=b"build_reference_sponge",
    )

    seq_s_preview = RecurrenceSequence(degree=16, seed=derived.seed_s).peek_bits(cfg.mux_bits)
    seq_t_preview = RecurrenceSequence(degree=16, seed=derived.seed_t).peek_bits(cfg.mux_bits)
    phi_trace = _build_phi_trace(
        derived.seed_s,
        derived.seed_t,
        degree=16,
        l=cfg.phi_width,
        steps=cfg.phi_steps,
    )
    multiplexed_bits = MultiplexedSequence(
        seq_s=RecurrenceSequence(degree=16, seed=derived.seed_s),
        seq_t=RecurrenceSequence(degree=16, seed=derived.seed_t),
        l=cfg.phi_width,
    ).generate_bits(cfg.mux_bits)
    sponge_trace = _build_sponge_trace(seed_digest, steps=cfg.sponge_trace_steps)

    drbg = service.instantiate_rng(seed_result=conditioning)
    state_before_generation = drbg.export_state()
    generated = service.generate_output_bundle(cfg.output_bytes, additional_input=b"memoire-demo-generate-1")
    state_after_generation = drbg.export_state()
    reseed_result = service.reseed_rng(additional_input=b"memoire-demo-reseed")
    state_after_reseed = drbg.export_state()
    generated_after_reseed = service.generate_output_bundle(cfg.output_bytes, additional_input=b"memoire-demo-generate-2")

    checkpoint = service.checkpoint_state()
    restored_payload = service.restore_state()
    restored_output = service.generate_output_bundle(cfg.output_bytes, additional_input=b"memoire-demo-restored")

    tee = SimulatedTEE(
        root_dir=service.config.state.root_dir,
        device_id=service.config.state.device_id,
        namespace=service.config.state.namespace,
    )
    tee_status = asdict(tee.status())

    return {
        "config": asdict(cfg),
        "architecture": "SRC -> COND -> DRBG -> STATE",
        "entropy": {
            "cpu_source": {
                "source_name": cpu_chunk.source_name,
                "symbol_bits": cpu_chunk.symbol_bits,
                "sample_count": cpu_chunk.sample_count,
                "metadata": cpu_chunk.metadata,
                "raw_preview": _summarize_bytes(
                    _preview_bytes(cpu_chunk.raw_bytes, size=cfg.preview_bytes),
                    preview_bytes=cfg.preview_bytes,
                    preview_bits=cfg.preview_bits,
                ),
                "health_report": asdict(cpu_report),
            },
            "sensor_source": {
                "source_name": sensor_chunk.source_name,
                "symbol_bits": sensor_chunk.symbol_bits,
                "sample_count": sensor_chunk.sample_count,
                "metadata": sensor_chunk.metadata,
                "raw_preview": _summarize_bytes(
                    _preview_bytes(sensor_chunk.raw_bytes, size=cfg.preview_bytes),
                    preview_bytes=cfg.preview_bytes,
                    preview_bits=cfg.preview_bits,
                ),
                "health_report": asdict(sensor_report),
            },
            "pool": {
                "snapshot": asdict(pool.snapshot()),
                "metadata": pool.export_metadata(),
                "raw_preview": _summarize_bytes(
                    _preview_bytes(raw_data, size=cfg.preview_bytes),
                    preview_bytes=cfg.preview_bytes,
                    preview_bits=cfg.preview_bits,
                ),
            },
            "comparison_before_after_conditioning": entropy_comparison,
        },
        "conditioning": {
            "input_bits": conditioning.input_bits,
            "output_bits": conditioning.output_bits,
            "context_info_utf8": conditioning.context_info.decode("utf-8", errors="replace"),
            "toeplitz_seed": _summarize_bytes(
                conditioning.toeplitz_seed,
                preview_bytes=cfg.preview_bytes,
                preview_bits=cfg.preview_bits,
            ),
            "toeplitz_output": _summarize_bytes(
                conditioning.toeplitz_output,
                preview_bytes=cfg.preview_bytes,
                preview_bits=cfg.preview_bits,
            ),
            "shake_seedinit": _summarize_bytes(
                conditioning.seedinit,
                preview_bytes=cfg.preview_bytes,
                preview_bits=cfg.preview_bits,
            ),
        },
        "drbg_derivation": {
            "seed_digest": _summarize_bytes(
                seed_digest,
                preview_bytes=cfg.preview_bytes,
                preview_bits=cfg.preview_bits,
            ),
            "seed_s": _format_int_views(derived.seed_s, bit_width=16),
            "seed_t": _format_int_views(derived.seed_t, bit_width=16),
            "sequence_s_preview": seq_s_preview,
            "sequence_t_preview": seq_t_preview,
            "phi_trace": phi_trace,
            "multiplexed_sequence_preview": multiplexed_bits,
            "sponge_trace": sponge_trace,
        },
        "rng_outputs": {
            "state_before_generation": state_before_generation,
            "generated_output_1": _json_ready_output(generated),
            "reseed_conditioning": {
                "input_bits": reseed_result.input_bits,
                "output_bits": reseed_result.output_bits,
                "seedinit_hex": reseed_result.seedinit.hex(),
            },
            "state_after_generation": state_after_generation,
            "state_after_reseed": state_after_reseed,
            "generated_output_2": _json_ready_output(generated_after_reseed),
            "restored_output": _json_ready_output(restored_output),
        },
        "state": {
            "checkpoint_blob": checkpoint.to_dict(),
            "restored_manager_state": restored_payload["manager_state"],
            "restored_sponge_private_state": restored_payload.get("sponge_private_state"),
            "tee_status": tee_status,
            "sdk_status": service.sdk_status(),
        },
    }


def _print_output_bundle(title: str, bundle: dict[str, Any]) -> None:
    afficher_sous_titre(title)
    afficher_ligne("Longueur", f"{bundle['length_bytes']} octets / {bundle['length_bits']} bits")
    afficher_ligne("Hexadecimal", bundle["hex"])
    afficher_ligne("Binaire", bundle["binary_grouped"])
    afficher_ligne("Decimal", bundle["decimal"])
    afficher_ligne("Octets", bundle["raw_byte_values"])


def _print_checkpoint_blob(blob: dict[str, Any]) -> None:
    afficher_sous_titre("Checkpoint scelle")
    afficher_ligne("Blob ID", blob["blob_id"])
    afficher_ligne("Version", blob["version"])
    afficher_ligne("Compteur materiel", blob["hardware_counter"])
    afficher_ligne("Compteur logiciel", blob["software_counter"])
    afficher_ligne("Nonce", blob["nonce_hex"])
    afficher_ligne("Tag d'integrite", blob["tag_hex"])
    afficher_ligne(
        "AAD (hex)",
        format_hex(bytes.fromhex(blob["aad_hex"]), max_octets=24),
    )
    afficher_ligne(
        "Ciphertext (hex)",
        format_hex(bytes.fromhex(blob["ciphertext_hex"]), max_octets=24),
    )


def render_full_project_demo(config: FullDemoConfig | None = None) -> dict[str, Any]:
    result = run_full_project_demo(config)

    afficher_titre("DEMONSTRATION COMPLETE DU PIPELINE SRC -> COND -> DRBG -> STATE")
    afficher_texte(
        """
Cette demonstration expose toutes les couches importantes du generateur :
source d'entropie, estimation de min-entropie, conditionnement Toeplitz + SHAKE-256,
derivation DRBG, sequence multiplexee, sponge, generation finale et gestion de l'etat.
        """
    )

    afficher_sous_titre("Configuration")
    afficher_ligne("Architecture", result["architecture"])
    afficher_ligne("Parametres", format_json(result["config"], max_lignes=20))

    entropy = result["entropy"]
    afficher_titre("1. SOURCE D'ENTROPIE (SRC)")
    for key, title in (("cpu_source", "Source CPU Jitter"), ("sensor_source", "Source capteurs inertiels")):
        source = entropy[key]
        report = source["health_report"]
        afficher_sous_titre(title)
        afficher_ligne("Source", source["source_name"])
        afficher_ligne("Sample count", source["sample_count"])
        afficher_ligne("Bits par symbole", source["symbol_bits"])
        afficher_ligne("Metadata", format_json(source["metadata"], max_lignes=12))
        afficher_ligne("Octets bruts (hex)", source["raw_preview"]["hex_preview"])
        afficher_ligne("Octets bruts (binaire)", source["raw_preview"]["bits_preview"])
        afficher_ligne("Min-entropy / symbole", f"{report['min_entropy_per_symbol']:.6f}")
        afficher_ligne(
            "Min-entropy totale estimee",
            f"{report['min_entropy_per_symbol'] * source['sample_count']:.6f} bits",
        )
        afficher_ligne("MCV p_max", f"{report['most_common_value_probability']:.6f}")
        afficher_ligne("Repetition count", report["repetition_count_ok"])
        afficher_ligne("Adaptive proportion", report["adaptive_proportion_ok"])
        afficher_ligne("Bloc accepte", report["accepted"])
        if report["warnings"]:
            afficher_ligne("Avertissements", format_liste(report["warnings"], max_items=6))

    afficher_sous_titre("Pool d'entropie")
    afficher_ligne("Snapshot", format_json(entropy["pool"]["snapshot"], max_lignes=12))
    afficher_ligne("Metadata", format_json(entropy["pool"]["metadata"], max_lignes=12))
    afficher_ligne("Pool brut (hex)", entropy["pool"]["raw_preview"]["hex_preview"])
    afficher_ligne("Pool brut (binaire)", entropy["pool"]["raw_preview"]["bits_preview"])
    afficher_ligne(
        "Min-entropy brute estimee",
        f"{entropy['pool']['snapshot']['estimated_min_entropy_bits']:.6f} bits",
    )

    comparison = entropy["comparison_before_after_conditioning"]
    afficher_sous_titre("Comparaison avant / apres conditionnement")
    afficher_ligne(
        "Raw bits min-entropy",
        f"{comparison['raw_bit_assessment']['health_report']['min_entropy_per_symbol']:.6f}",
    )
    afficher_ligne(
        "Toeplitz bits min-entropy",
        f"{comparison['toeplitz_bit_assessment']['health_report']['min_entropy_per_symbol']:.6f}",
    )
    afficher_ligne(
        "Seedinit bits min-entropy",
        f"{comparison['seed_bit_assessment']['health_report']['min_entropy_per_symbol']:.6f}",
    )

    conditioning = result["conditioning"]
    afficher_titre("2. CONDITIONNEUR (COND)")
    afficher_ligne("Input bits", conditioning["input_bits"])
    afficher_ligne("Output bits Toeplitz", conditioning["output_bits"])
    afficher_ligne("Context info", conditioning["context_info_utf8"])
    afficher_ligne("Toeplitz seed (hex)", conditioning["toeplitz_seed"]["hex"])
    afficher_ligne("Toeplitz seed (binaire)", conditioning["toeplitz_seed"]["bits_preview"])
    afficher_ligne("Toeplitz seed (decimal)", conditioning["toeplitz_seed"]["decimal"])
    afficher_ligne("Toeplitz output (hex)", conditioning["toeplitz_output"]["hex"])
    afficher_ligne("Toeplitz output (binaire)", conditioning["toeplitz_output"]["bits_preview"])
    afficher_ligne("Toeplitz output (decimal)", conditioning["toeplitz_output"]["decimal"])
    afficher_ligne("SHAKE-256 Seedinit (hex)", conditioning["shake_seedinit"]["hex"])
    afficher_ligne("SHAKE-256 Seedinit (binaire)", conditioning["shake_seedinit"]["bits_preview"])
    afficher_ligne("SHAKE-256 Seedinit (decimal)", conditioning["shake_seedinit"]["decimal"])

    derivation = result["drbg_derivation"]
    afficher_titre("3. DERIVATION DU DRBG ET MULTIPLEXED SPONGE")
    afficher_ligne("Seed digest (hex)", derivation["seed_digest"]["hex"])
    afficher_ligne("Seed digest (binaire)", derivation["seed_digest"]["bits_preview"])
    afficher_ligne("Seed S", format_json(derivation["seed_s"], max_lignes=8))
    afficher_ligne("Seed T", format_json(derivation["seed_t"], max_lignes=8))
    afficher_ligne("Sequence S_n", format_liste(derivation["sequence_s_preview"], max_items=32))
    afficher_ligne("Sequence T_n", format_liste(derivation["sequence_t_preview"], max_items=32))
    afficher_ligne("Sequence multiplexee", format_liste(derivation["multiplexed_sequence_preview"], max_items=32))

    afficher_sous_titre("Trace de phi(l,n)")
    for row in derivation["phi_trace"]:
        afficher_ligne(
            f"n={row['n']}",
            f"S={row['s_bits']} | phi(dec)={row['phi_decimal']} | phi(hex)={row['phi_hex']} | "
            f"phi(bin)={row['phi_binary']} | bit selectionne dans T={row['selected_t_bit']}",
        )

    afficher_sous_titre("Trace du sponge")
    for row in derivation["sponge_trace"]:
        afficher_ligne(
            f"Etape {row['step']}",
            f"state_avant={row['state_before_hex']} | bloc={row['block_hex']} / {row['block_decimal']} / "
            f"{row['block_binary']} | state_apres={row['state_after_hex']}",
        )

    outputs = result["rng_outputs"]
    afficher_titre("4. RNG FINAL")
    afficher_ligne("Etat DRBG avant generation", format_json(outputs["state_before_generation"], max_lignes=18))
    _print_output_bundle("Sortie 1", outputs["generated_output_1"])
    afficher_ligne("Etat DRBG apres generation", format_json(outputs["state_after_generation"], max_lignes=18))
    afficher_ligne("Reseed - nouveau Seedinit", outputs["reseed_conditioning"]["seedinit_hex"])
    afficher_ligne("Etat DRBG apres reseed", format_json(outputs["state_after_reseed"], max_lignes=18))
    _print_output_bundle("Sortie 2 apres reseed", outputs["generated_output_2"])
    _print_output_bundle("Sortie apres restauration de l'etat", outputs["restored_output"])

    state = result["state"]
    afficher_titre("5. STATE")
    _print_checkpoint_blob(state["checkpoint_blob"])
    afficher_ligne("Etat manager restaure", format_json(state["restored_manager_state"], max_lignes=18))
    afficher_ligne("Etat prive sponge restaure", format_json(state["restored_sponge_private_state"], max_lignes=18))
    afficher_ligne("TEE status", format_json(state["tee_status"], max_lignes=12))
    afficher_ligne("SDK status", format_json(state["sdk_status"], max_lignes=12))

    return result


if __name__ == "__main__":
    render_full_project_demo()
