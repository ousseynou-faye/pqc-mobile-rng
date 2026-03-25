"""Configuration commune des benchmarks de l'etape 7."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class BenchmarkConfig:
    mode: str
    repetitions: int
    warmup_rounds: int
    output_sizes: tuple[int, ...] = (32, 256, 1024, 4096)
    output_dir: str = "benchmarks/results"
    include_csv: bool = True
    include_markdown: bool = True

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


BENCHMARK_PRESETS: dict[str, BenchmarkConfig] = {
    "smoke": BenchmarkConfig(mode="smoke", repetitions=3, warmup_rounds=1, output_sizes=(32, 256)),
    "local": BenchmarkConfig(mode="local", repetitions=8, warmup_rounds=2),
    "memoire": BenchmarkConfig(mode="memoire", repetitions=20, warmup_rounds=4),
}
