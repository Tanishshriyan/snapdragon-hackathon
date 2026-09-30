"""Latency and resource benchmark utilities with honest power limitations."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from statistics import mean, median
import time
from typing import Any, Callable, Mapping


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    name: str
    iterations: int
    warmups: int
    latency_ms_mean: float
    latency_ms_median: float
    latency_ms_p95: float
    process_cpu_seconds: float | None
    rss_delta_mb: float | None
    power_measurement: str
    notes: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _resource_snapshot() -> tuple[float | None, int | None]:
    try:
        import psutil  # type: ignore[import-not-found]
        process = psutil.Process(os.getpid())
        return process.cpu_times().user + process.cpu_times().system, process.memory_info().rss
    except (ImportError, OSError):
        return None, None


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))]


class BenchmarkRunner:
    def run(self, name: str, operation: Callable[[], Any], iterations: int = 20, warmups: int = 3) -> BenchmarkResult:
        if iterations < 1:
            raise ValueError("iterations must be positive")
        for _ in range(max(0, warmups)):
            operation()
        cpu_before, rss_before = _resource_snapshot()
        latencies: list[float] = []
        for _ in range(iterations):
            started = time.perf_counter()
            operation()
            latencies.append((time.perf_counter() - started) * 1000)
        cpu_after, rss_after = _resource_snapshot()
        cpu_seconds = cpu_after - cpu_before if cpu_before is not None and cpu_after is not None else None
        rss_delta = (rss_after - rss_before) / (1024 * 1024) if rss_before is not None and rss_after is not None else None
        return BenchmarkResult(
            name=name,
            iterations=iterations,
            warmups=warmups,
            latency_ms_mean=mean(latencies),
            latency_ms_median=median(latencies),
            latency_ms_p95=_p95(latencies),
            process_cpu_seconds=cpu_seconds,
            rss_delta_mb=rss_delta,
            power_measurement="not available: no external wattmeter/telemetry source configured",
            notes="Latency and process RSS are measured locally; power efficiency is not inferred.",
        )

    def compare(self, operations: Mapping[str, Callable[[], Any]], iterations: int = 20, warmups: int = 3) -> list[BenchmarkResult]:
        return [self.run(name, operation, iterations, warmups) for name, operation in operations.items()]


def results_to_json(results: list[BenchmarkResult]) -> str:
    return json.dumps([result.as_dict() for result in results], indent=2)
