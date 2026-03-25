"""Validation experimentale prudente de la source d'entropie."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from math import log2
from typing import Any

from software.conditioner import EntropyMixer
from software.entropy import HealthEstimator


def _validate_symbols(symbols: Sequence[int]) -> list[int]:
    sample = [int(symbol) for symbol in symbols]
    if not sample:
        raise ValueError("La sequence de symboles ne doit pas etre vide.")
    return sample


def _bytes_to_bits(data: bytes) -> list[int]:
    return [((byte >> shift) & 1) for byte in data for shift in range(7, -1, -1)]


def estimate_mcv_min_entropy(symbols: Sequence[int]) -> dict[str, Any]:
    """Estime une borne prudente par la frequence de la valeur la plus courante."""

    sample = _validate_symbols(symbols)
    counts = Counter(sample)
    most_common_symbol, most_common_count = counts.most_common(1)[0]
    p_max = most_common_count / len(sample)

    return {
        "method": "most_common_value",
        "sample_count": len(sample),
        "alphabet_size": len(counts),
        "most_common_symbol": most_common_symbol,
        "most_common_count": most_common_count,
        "most_common_value_probability": p_max,
        "min_entropy_per_symbol": -log2(p_max) if p_max > 0.0 else 0.0,
        "notes": [
            "Estimation prudente inspiree de SP 800-90B.",
            "Ne constitue pas une validation formelle complete de la source.",
        ],
    }


def repetition_count_test(symbols: Sequence[int], repetition_limit: int) -> dict[str, Any]:
    """Detecte une repetition anormalement longue d'une meme valeur."""

    sample = _validate_symbols(symbols)
    if repetition_limit <= 1:
        raise ValueError("repetition_limit doit etre > 1.")

    longest_run = 1
    current_run = 1
    previous = sample[0]
    failed_at = None

    for index, value in enumerate(sample[1:], start=1):
        if value == previous:
            current_run += 1
        else:
            longest_run = max(longest_run, current_run)
            current_run = 1
            previous = value

        if current_run >= repetition_limit and failed_at is None:
            failed_at = index

    longest_run = max(longest_run, current_run)
    passed = failed_at is None

    return {
        "test_name": "repetition_count",
        "sample_count": len(sample),
        "threshold": repetition_limit,
        "statistic": longest_run,
        "p_value": None,
        "passed": passed,
        "notes": [
            "Health check inspire de SP 800-90B.",
            "Ne constitue pas une validation formelle complete de la source.",
        ],
        "failure_index": failed_at,
    }


def adaptive_proportion_test(
    symbols: Sequence[int],
    *,
    window_size: int,
    max_proportion: float,
) -> dict[str, Any]:
    """Detecte une domination locale excessive dans des fenetres glissantes."""

    sample = _validate_symbols(symbols)
    if window_size <= 1:
        raise ValueError("window_size doit etre > 1.")
    if not (0.0 < max_proportion <= 1.0):
        raise ValueError("max_proportion doit etre dans ]0, 1].")

    max_observed = 0.0
    failed_window_start = None

    if len(sample) >= window_size:
        for start in range(0, len(sample) - window_size + 1):
            window = sample[start:start + window_size]
            observed = max(Counter(window).values()) / window_size
            if observed > max_observed:
                max_observed = observed
            if observed > max_proportion and failed_window_start is None:
                failed_window_start = start
    else:
        max_observed = max(Counter(sample).values()) / len(sample)

    passed = failed_window_start is None

    return {
        "test_name": "adaptive_proportion",
        "sample_count": len(sample),
        "threshold": max_proportion,
        "window_size": window_size,
        "statistic": max_observed,
        "p_value": None,
        "passed": passed,
        "notes": [
            "Health check inspire de SP 800-90B.",
            "Ne constitue pas une validation formelle complete de la source.",
        ],
        "failure_window_start": failed_window_start,
    }


def analyze_entropy_source(
    symbols: Sequence[int],
    *,
    symbol_bits: int,
    source_name: str,
    repetition_limit: int = 32,
    adaptive_window_size: int = 64,
    adaptive_max_proportion: float = 0.75,
) -> dict[str, Any]:
    """Orchestre une validation experimentale prudente d'une source brute."""

    sample = _validate_symbols(symbols)
    estimator = HealthEstimator(
        repetition_limit=repetition_limit,
        adaptive_window_size=adaptive_window_size,
        adaptive_max_proportion=adaptive_max_proportion,
    )
    health = estimator.evaluate_symbols(sample, symbol_bits=symbol_bits, source_name=source_name)
    return {
        "source_name": source_name,
        "symbol_bits": symbol_bits,
        "sample_count": len(sample),
        "mcv_estimate": estimate_mcv_min_entropy(sample),
        "repetition_count_test": repetition_count_test(sample, repetition_limit=repetition_limit),
        "adaptive_proportion_test": adaptive_proportion_test(
            sample,
            window_size=adaptive_window_size,
            max_proportion=adaptive_max_proportion,
        ),
        "health_report": {
            "source_name": health.source_name,
            "sample_count": health.sample_count,
            "symbol_bits": health.symbol_bits,
            "most_common_value_probability": health.most_common_value_probability,
            "min_entropy_per_symbol": health.min_entropy_per_symbol,
            "repetition_count_ok": health.repetition_count_ok,
            "adaptive_proportion_ok": health.adaptive_proportion_ok,
            "accepted": health.accepted,
            "warnings": list(health.warnings),
        },
        "notes": [
            "Validation experimentale prudente de la source d'entropie.",
            "Approche inspiree de SP 800-90B sans revendication de conformite formelle.",
        ],
    }


def compare_before_after_conditioning(
    raw_data: bytes,
    *,
    conditioner: EntropyMixer | None = None,
    personalization: bytes = b"",
    extra_context: bytes = b"",
    toeplitz_public_seed: bytes | None = None,
) -> dict[str, Any]:
    """Compare des indicateurs simples avant et apres conditionnement."""

    if not raw_data:
        raise ValueError("raw_data ne doit pas etre vide.")

    mixer = conditioner or EntropyMixer()
    conditioned = mixer.condition_raw_data(
        raw_data=raw_data,
        metadata={"source": "experimental_entropy_validation"},
        personalization=personalization,
        extra_context=extra_context,
        toeplitz_public_seed=toeplitz_public_seed,
    )

    raw_bits = _bytes_to_bits(bytes(raw_data))
    toeplitz_bits = _bytes_to_bits(conditioned.toeplitz_output)
    seed_bits = _bytes_to_bits(conditioned.seedinit)

    return {
        "raw_data_bytes": len(raw_data),
        "toeplitz_output_bytes": len(conditioned.toeplitz_output),
        "seedinit_bytes": len(conditioned.seedinit),
        "raw_bit_assessment": analyze_entropy_source(raw_bits, symbol_bits=1, source_name="raw_bits"),
        "toeplitz_bit_assessment": analyze_entropy_source(
            toeplitz_bits,
            symbol_bits=1,
            source_name="toeplitz_output_bits",
        ),
        "seed_bit_assessment": analyze_entropy_source(seed_bits, symbol_bits=1, source_name="seedinit_bits"),
        "notes": [
            "La comparaison avant/apres conditionnement reste empirique.",
            "Le conditionnement Toeplitz + SHAKE-256 n'est pas presente ici comme une preuve normative.",
        ],
    }
