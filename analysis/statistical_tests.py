"""Tests statistiques experimentaux inspires de SP 800-22."""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from .bit_metrics import compute_bit_balance
from .linear_complexity import berlekamp_massey_linear_complexity
from .period_metrics import estimate_observed_period
from .run_metrics import compute_run_metrics


def _validate_bits(bits: Sequence[int]) -> list[int]:
    sample = [int(bit) for bit in bits]
    if any(bit not in (0, 1) for bit in sample):
        raise ValueError("Je demande une sequence binaire composee uniquement de 0 et de 1.")
    return sample


def bytes_to_bits(data: bytes) -> list[int]:
    """Convertit des octets en bits ordonnes du MSB vers le LSB."""

    return [((byte >> shift) & 1) for byte in data for shift in range(7, -1, -1)]


def _regularized_gamma_q(a: float, x: float) -> float:
    """Approximation numerique simple de Q(a, x) sans dependance externe."""

    if a <= 0.0:
        raise ValueError("a doit etre > 0.")
    if x < 0.0:
        raise ValueError("x doit etre >= 0.")
    if x == 0.0:
        return 1.0

    gln = math.lgamma(a)
    if x < a + 1.0:
        ap = a
        delta = 1.0 / a
        series = delta
        for _ in range(200):
            ap += 1.0
            delta *= x / ap
            series += delta
            if abs(delta) < abs(series) * 1e-12:
                break
        p = series * math.exp(-x + a * math.log(x) - gln)
        return max(0.0, min(1.0, 1.0 - p))

    b = x + 1.0 - a
    c = 1.0 / 1e-30
    d = 1.0 / b
    h = d
    for i in range(1, 200):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        if abs(d) < 1e-30:
            d = 1e-30
        c = b + an / c
        if abs(c) < 1e-30:
            c = 1e-30
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-12:
            break
    q = math.exp(-x + a * math.log(x) - gln) * h
    return max(0.0, min(1.0, q))


def _insufficient_length_result(
    test_name: str,
    *,
    length: int,
    threshold: float | int | None,
    notes: list[str],
) -> dict[str, Any]:
    return {
        "test_name": test_name,
        "length": length,
        "statistic": None,
        "p_value": None,
        "passed": False,
        "threshold": threshold,
        "notes": notes + ["Sequence trop courte pour une interpretation fiable."],
    }


def monobit_frequency_test(bits: Sequence[int], *, alpha: float = 0.01) -> dict[str, Any]:
    """Test monobit inspire de SP 800-22."""

    sample = _validate_bits(bits)
    n = len(sample)
    if n < 2:
        return _insufficient_length_result(
            "monobit_frequency",
            length=n,
            threshold=alpha,
            notes=["Test statistique inspire de SP 800-22, non preuve cryptographique."],
        )

    s_obs = abs(sum(1 if bit else -1 for bit in sample)) / math.sqrt(n)
    p_value = math.erfc(s_obs / math.sqrt(2.0))
    balance = compute_bit_balance(sample)

    return {
        "test_name": "monobit_frequency",
        "length": n,
        "statistic": s_obs,
        "p_value": p_value,
        "passed": p_value >= alpha,
        "threshold": alpha,
        "notes": [
            "Test statistique inspire de SP 800-22, utilise comme indicateur experimental.",
            f"Biais empirique observe: {balance['bias']:.6f}",
        ],
    }


def block_frequency_test(bits: Sequence[int], *, block_size: int = 128, alpha: float = 0.01) -> dict[str, Any]:
    """Test de frequence par blocs inspire de SP 800-22."""

    sample = _validate_bits(bits)
    n = len(sample)
    if block_size <= 1:
        raise ValueError("block_size doit etre > 1.")
    n_blocks = n // block_size
    if n_blocks == 0:
        return _insufficient_length_result(
            "block_frequency",
            length=n,
            threshold=alpha,
            notes=["Test statistique inspire de SP 800-22, non preuve cryptographique."],
        )

    chisq = 0.0
    proportions: list[float] = []
    for block_index in range(n_blocks):
        block = sample[block_index * block_size:(block_index + 1) * block_size]
        pi = sum(block) / block_size
        proportions.append(pi)
        chisq += 4.0 * block_size * ((pi - 0.5) ** 2)

    p_value = _regularized_gamma_q(n_blocks / 2.0, chisq / 2.0)

    return {
        "test_name": "block_frequency",
        "length": n,
        "statistic": chisq,
        "p_value": p_value,
        "passed": p_value >= alpha,
        "threshold": alpha,
        "notes": [
            "Test statistique inspire de SP 800-22, utilise comme indicateur experimental.",
            f"Nombre de blocs analyses: {n_blocks}",
            f"Taille de bloc: {block_size}",
            f"Proportion moyenne de 1: {sum(proportions) / len(proportions):.6f}",
        ],
        "block_size": block_size,
        "n_blocks": n_blocks,
    }


def runs_test(bits: Sequence[int], *, alpha: float = 0.01) -> dict[str, Any]:
    """Test de runs inspire de SP 800-22."""

    sample = _validate_bits(bits)
    n = len(sample)
    if n < 2:
        return _insufficient_length_result(
            "runs",
            length=n,
            threshold=alpha,
            notes=["Test statistique inspire de SP 800-22, non preuve cryptographique."],
        )

    pi = sum(sample) / n
    tau = 2.0 / math.sqrt(n)
    if abs(pi - 0.5) >= tau:
        return {
            "test_name": "runs",
            "length": n,
            "statistic": None,
            "p_value": 0.0,
            "passed": False,
            "threshold": alpha,
            "notes": [
                "Test statistique inspire de SP 800-22, utilise comme indicateur experimental.",
                "Precondition de frequence non satisfaite, le test des runs rejette la sequence.",
            ],
        }

    v_obs = 1 + sum(1 for index in range(1, n) if sample[index] != sample[index - 1])
    numerator = abs(v_obs - (2.0 * n * pi * (1.0 - pi)))
    denominator = 2.0 * math.sqrt(2.0 * n) * pi * (1.0 - pi)
    p_value = math.erfc(numerator / denominator)
    run_metrics = compute_run_metrics(sample)

    return {
        "test_name": "runs",
        "length": n,
        "statistic": v_obs,
        "p_value": p_value,
        "passed": p_value >= alpha,
        "threshold": alpha,
        "notes": [
            "Test statistique inspire de SP 800-22, utilise comme indicateur experimental.",
            f"Longest run observe: {run_metrics['longest_run']}",
            f"Nombre total de runs observes: {run_metrics['total_runs']}",
        ],
    }


def linear_complexity_metric(bits: Sequence[int]) -> dict[str, Any]:
    """Metrique descriptive reutilisant Berlekamp-Massey existant."""

    sample = _validate_bits(bits)
    complexity = berlekamp_massey_linear_complexity(sample)
    return {
        "test_name": "linear_complexity_metric",
        "length": len(sample),
        "statistic": complexity["linear_complexity"],
        "p_value": None,
        "passed": True,
        "threshold": None,
        "notes": [
            "Metrique descriptive experimentale.",
            "Il ne s'agit pas ici d'une implementation complete du test NIST de complexite lineaire.",
        ],
        "normalized_linear_complexity": complexity["normalized_linear_complexity"],
    }


def observed_periodicity_metric(bits: Sequence[int], *, max_period: int | None = None) -> dict[str, Any]:
    """Metrique descriptive reutilisant l'estimation de periode observee existante."""

    sample = _validate_bits(bits)
    period = estimate_observed_period(sample, max_period=max_period)
    observed_period = period["observed_period"]
    return {
        "test_name": "observed_periodicity_metric",
        "length": len(sample),
        "statistic": observed_period,
        "p_value": None,
        "passed": observed_period is None,
        "threshold": None,
        "notes": [
            "Metrique descriptive experimentale.",
            "Une periode observee courte sur une fenetre finie est un signal de vigilance, pas une preuve generale.",
        ],
        "checked_prefix_length": period["checked_prefix_length"],
    }


def run_sp800_22_inspired_suite(
    bits: Sequence[int],
    *,
    alpha: float = 0.01,
    block_size: int = 128,
    max_period: int | None = None,
) -> dict[str, Any]:
    """Orchestre la batterie experimentale inspiree de SP 800-22."""

    sample = _validate_bits(bits)
    tests = {
        "monobit_frequency": monobit_frequency_test(sample, alpha=alpha),
        "block_frequency": block_frequency_test(sample, block_size=block_size, alpha=alpha),
        "runs": runs_test(sample, alpha=alpha),
        "linear_complexity_metric": linear_complexity_metric(sample),
        "observed_periodicity_metric": observed_periodicity_metric(sample, max_period=max_period),
    }
    passed = sum(1 for result in tests.values() if result["passed"])
    return {
        "sample_length": len(sample),
        "alpha": alpha,
        "block_size": block_size,
        "tests": tests,
        "summary": {
            "passed_tests": passed,
            "total_tests": len(tests),
            "success_ratio": passed / len(tests),
        },
        "notes": [
            "Batterie statistique experimentale inspiree de SP 800-22.",
            "Les resultats ne doivent pas etre interpretes comme une preuve cryptographique ni comme une conformite NIST.",
        ],
    }
