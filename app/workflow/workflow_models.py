"""Value objects for deterministic sequence learning."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class TransitionStat:
    source: str
    target: str
    count: int
    source_total: int

    @property
    def confidence(self) -> float:
        return self.count / self.source_total if self.source_total else 0.0


@dataclass(slots=True, frozen=True)
class WorkflowCandidate:
    sequence: tuple[str, ...]
    occurrence_count: int
    confidence: float

    @property
    def name(self) -> str:
        return " → ".join(self.sequence)

