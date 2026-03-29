from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from analysis.campaign_runner import CAMPAIGN_PRESETS, run_comparative_campaign
from analysis.statistical_tests import bytes_to_bits, run_sp800_22_inspired_suite
from benchmarks.common import build_composite_drbg
from benchmarks.config import BENCHMARK_PRESETS
from benchmarks.mobile_profile import run_mobile_profile
from benchmarks.performance_arm import run_performance_benchmark
from software.api import (
    get_rng_service,
    rng_get_bytes,
    rng_health,
    rng_init,
    rng_reseed,
    rng_restore_state,
    rng_zeroize,
)
from software.api.rng_service import RNGServiceConfig, StateConfig
from software.conditioner import EntropyMixer
from software.entropy import CPUJitterSource, EntropyPool, SensorEntropySource
from ui.utils.formatters import byte_histogram, decimal_rows, summarize_bytes
from ui.utils.security import preview_bits, preview_bytes, redact_state_payload, truncate_text


class ProjectFacade:
    """Facade UI orientee affichage sur des modules reels du projet."""

    def __init__(self, root_dir: str | Path | None = None) -> None:
        self.project_root = Path(__file__).resolve().parents[2]
        self.runtime_root = Path(root_dir or self.project_root / "tests_runtime" / "ui_dashboard")
        self.runtime_root.mkdir(parents=True, exist_ok=True)
        self._config = RNGServiceConfig(
            state=StateConfig(
                root_dir=self.runtime_root,
                device_id="ui-dashboard-device",
                namespace="ui-dashboard",
                blob_id="ui-dashboard-blob",
                checkpoint_metadata={"purpose": "ui-dashboard-checkpoint"},
            )
        )

    def ensure_service(self, *, reset: bool = False):
        return get_rng_service(reset=reset, config=self._config if reset else None)

    def architecture_cards(self) -> list[dict[str, str]]:
        return [
            {"name": "SRC", "status": "implemented", "title": "Collecte d'entropie", "body": "CPU jitter et source capteur simulee alimentent un pool prudent d'entropie brute."},
            {"name": "COND", "status": "implemented", "title": "Conditionnement", "body": "Le chemin officiel applique Toeplitz puis SHAKE-256 avant toute instanciation du DRBG."},
            {"name": "DRBG", "status": "implemented", "title": "Generation post-quantique", "body": "Module-LWR est nominal. Multiplexed Sponge reste un moteur secondaire de recherche."},
            {"name": "STATE", "status": "implemented", "title": "Etat et persistence", "body": "Machine a etats explicite, scellement simule et restauration administree du prototype."},
            {"name": "Mobile", "status": "experimental", "title": "Trajectoire mobile", "body": "Le depot expose une frontiere FFI de transition et un protocole de profilage, sans integration Android reelle."},
            {"name": "NTT", "status": "future", "title": "Optimisation future", "body": "La NTT est documentee comme piste d'optimisation, pas comme composant actif de la baseline executable."},
        ]

    def system_overview(self) -> dict[str, Any]:
        service = self.ensure_service()
        try:
            status = service.sdk_status()
        except Exception:
            status = {
                "initialized": False,
                "instantiated": False,
                "state_available": False,
                "reseed_supported": False,
                "last_operation": None,
                "profile": "baseline",
                "health_status": "warning",
                "lifecycle_state": None,
            }
        return {
            "project_title": "Deploiement d'un RNG Mobile Post-Quantique",
            "pipeline": "SRC -> COND -> DRBG -> STATE",
            "engines": ["module_lwr", "multiplexed_sponge"],
            "conditioner": "Toeplitz + SHAKE-256",
            "prototype_status": "Prototype academique local / SDK Python",
            "sdk_status": status,
        }

    def collect_entropy(
        self,
        *,
        use_cpu: bool = True,
        use_sensor: bool = True,
        cpu_sample_count: int = 512,
        sensor_frame_count: int = 128,
        cpu_lsb_count: int = 2,
        sensor_lsb_count: int = 2,
    ) -> dict[str, Any]:
        pool = EntropyPool()
        sources: list[dict[str, Any]] = []

        if use_cpu:
            chunk = CPUJitterSource(sample_count=cpu_sample_count, lsb_count=cpu_lsb_count).collect()
            report = pool.add_chunk(chunk)
            sources.append(self._serialize_chunk(chunk, report))
        if use_sensor:
            chunk = SensorEntropySource(frame_count=sensor_frame_count, lsb_count=sensor_lsb_count).collect()
            report = pool.add_chunk(chunk)
            sources.append(self._serialize_chunk(chunk, report))

        raw_data = pool.export_raw_bytes()
        return {
            "sources": sources,
            "pool": pool,
            "pool_summary": pool.export_metadata(),
            "raw_data": raw_data,
            "raw_preview_hex": preview_bytes(raw_data),
            "raw_preview_bits": preview_bits(raw_data),
            "symbol_histogram": self._build_symbol_histogram(sources),
        }

    def condition_entropy(
        self,
        raw_data: bytes,
        *,
        metadata: dict[str, Any] | None = None,
        personalization: bytes = b"",
        extra_context: bytes = b"",
    ) -> dict[str, Any]:
        mixer = EntropyMixer()
        result = mixer.condition_raw_data(
            raw_data=raw_data,
            metadata=metadata,
            personalization=personalization,
            extra_context=extra_context,
        )
        return {
            "result": result,
            "input_bits": result.input_bits,
            "output_bits": result.output_bits,
            "raw_preview_hex": preview_bytes(result.raw_data),
            "toeplitz_preview_hex": preview_bytes(result.toeplitz_output),
            "seed_preview_hex": preview_bytes(result.seedinit, head=6, tail=6),
            "context_preview": truncate_text(result.context_info.decode("utf-8", errors="ignore"), limit=180),
        }

    def instantiate_lab_engine(self, engine_name: str, *, seed_material: bytes, personalization: bytes = b""):
        drbg = build_composite_drbg(engine_name)
        drbg.instantiate(seed_material, personalization=personalization)
        return drbg

    def generate_with_engine(self, drbg: Any, *, length: int, additional_input: bytes = b"") -> dict[str, Any]:
        started = time.perf_counter_ns()
        data = drbg.generate(length, additional_input=additional_input)
        elapsed = time.perf_counter_ns() - started
        return {
            "data": data,
            "preview_hex": preview_bytes(data, head=12, tail=12),
            "preview_bits": preview_bits(data),
            "length": len(data),
            "elapsed_ns": elapsed,
            "decimal_rows": decimal_rows(data),
            "byte_histogram": byte_histogram(data),
            "byte_summary": summarize_bytes(data),
            "state": redact_state_payload(drbg.export_state()),
        }

    def compare_engines(self, *, length: int, seed_material: bytes, additional_input: bytes = b"") -> dict[str, Any]:
        comparison: dict[str, Any] = {}
        for engine_name in ("module_lwr", "multiplexed_sponge"):
            drbg = self.instantiate_lab_engine(engine_name, seed_material=seed_material)
            comparison[engine_name] = self.generate_with_engine(drbg, length=length, additional_input=additional_input)
        return comparison

    def instantiate_sdk(self, *, personalization: bytes = b"") -> dict[str, Any]:
        service = self.ensure_service(reset=True)
        service.instantiate_rng(personalization=personalization)
        return {"sdk_status": service.sdk_status(), "health_status": service.health_status()}

    def sdk_generate(self, length: int) -> dict[str, Any]:
        output = rng_get_bytes(length)
        return {
            "data": output,
            "preview_hex": preview_bytes(output, head=12, tail=12),
            "preview_bits": preview_bits(output),
            "decimal_rows": decimal_rows(output),
            "byte_histogram": byte_histogram(output),
            "byte_summary": summarize_bytes(output),
            "status": rng_health(),
        }

    def sdk_reseed(self) -> dict[str, Any]:
        rng_reseed()
        return {"status": rng_health()}

    def sdk_zeroize(self) -> dict[str, Any]:
        rng_zeroize()
        return {"status": rng_health()}

    def sdk_checkpoint(self) -> dict[str, Any]:
        service = self.ensure_service()
        blob = service.checkpoint_state()
        return {
            "status": service.sdk_status(),
            "blob": {
                "blob_id": blob.blob_id,
                "hardware_counter": blob.hardware_counter,
                "software_counter": blob.software_counter,
                "version": blob.version,
                "nonce_preview": truncate_text(blob.nonce_hex, limit=16),
                "tag_preview": truncate_text(blob.tag_hex, limit=16),
            },
        }

    def sdk_restore(self) -> dict[str, Any]:
        rng_restore_state()
        service = self.ensure_service()
        return {"status": service.sdk_status(), "health": service.health_status()}

    def sdk_state_details(self) -> dict[str, Any]:
        service = self.ensure_service()
        health = service.health_status()
        state = health.get("drbg_state")
        if isinstance(state, dict):
            state = redact_state_payload(state)
        return {"sdk_status": service.sdk_status(), "health_status": health, "drbg_state": state or {}}

    def run_validation_smoke(self) -> dict[str, Any]:
        results: list[dict[str, Any]] = []
        start = time.perf_counter_ns()
        rng_init(force_reinit=True)
        data = rng_get_bytes(32)
        api_status = rng_health()
        results.append({"name": "API publique", "success": len(data) == 32 and api_status["initialized"] is True, "duration_ms": (time.perf_counter_ns() - start) / 1_000_000, "details": api_status})

        start = time.perf_counter_ns()
        src = self.collect_entropy(use_cpu=True, use_sensor=True, cpu_sample_count=128, sensor_frame_count=32)
        pool_summary = src["pool_summary"]
        results.append({"name": "SRC / health checks", "success": pool_summary["accepted_chunks"] >= 1, "duration_ms": (time.perf_counter_ns() - start) / 1_000_000, "details": pool_summary})

        start = time.perf_counter_ns()
        bits = bytes_to_bits(data)
        suite = run_sp800_22_inspired_suite(bits, block_size=32, max_period=32)
        results.append({"name": "Suite statistique legere", "success": suite["summary"]["passed_tests"] >= 3, "duration_ms": (time.perf_counter_ns() - start) / 1_000_000, "details": suite["summary"]})

        return {"results": results, "warnings": ["Ces verifications sont des smoke tests locaux.", "Les tests statistiques affiches sont experimentaux et ne constituent pas une preuve cryptographique."]}

    def run_benchmark_smoke(self) -> dict[str, Any]:
        perf_report = run_performance_benchmark(BENCHMARK_PRESETS["smoke"])
        mobile_report = run_mobile_profile()
        return {"performance": perf_report, "mobile_profile": mobile_report, "warnings": ["Ces benchmarks mesurent le prototype local Python.", "Un hote non ARM ne permet pas de conclure sur une cible mobile reelle."]}

    def run_campaign_smoke(self) -> dict[str, Any]:
        report = run_comparative_campaign(CAMPAIGN_PRESETS["smoke"])
        return {
            "comparison": report["comparison"],
            "engines": {
                name: {
                    "bias_mean": engine["aggregates"]["bias"]["mean"],
                    "success_ratio_mean": engine["aggregates"]["suite_success_ratio"]["mean"],
                    "linear_complexity_mean": engine["aggregates"]["normalized_linear_complexity"]["mean"],
                }
                for name, engine in report["engines"].items()
            },
        }

    def _serialize_chunk(self, chunk: Any, report: Any) -> dict[str, Any]:
        return {
            "source_name": chunk.source_name,
            "sample_count": chunk.sample_count,
            "symbol_bits": chunk.symbol_bits,
            "raw_preview_hex": preview_bytes(chunk.raw_bytes),
            "raw_preview_bits": preview_bits(chunk.raw_bytes),
            "metadata": dict(chunk.metadata),
            "report": {
                "accepted": report.accepted,
                "most_common_value_probability": round(report.most_common_value_probability, 6),
                "min_entropy_per_symbol": round(report.min_entropy_per_symbol, 6),
                "repetition_count_ok": report.repetition_count_ok,
                "adaptive_proportion_ok": report.adaptive_proportion_ok,
                "warnings": list(report.warnings),
            },
            "symbols": list(chunk.symbols[:128]),
        }

    def _build_symbol_histogram(self, sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
        counts: dict[int, int] = {}
        for source in sources:
            for symbol in source["symbols"]:
                counts[int(symbol)] = counts.get(int(symbol), 0) + 1
        return [{"symbol": key, "count": counts[key]} for key in sorted(counts)]
