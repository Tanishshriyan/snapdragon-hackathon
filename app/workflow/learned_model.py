"""A small learned Markov workflow model for the MVP demo."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from app.database.models import ActivityEvent


@dataclass(frozen=True, slots=True)
class LearnedPrediction:
    source: str
    target: str
    confidence: float
    observations: int


class LearnedWorkflowModel:
    """Learns transitions with recency weighting and time-of-day buckets."""

    def __init__(self) -> None:
        self._transitions: dict[str, Counter[str]] = defaultdict(Counter)
        self._time_transitions: dict[tuple[str, int], Counter[str]] = defaultdict(Counter)

    def fit(self, events: Iterable[ActivityEvent]) -> None:
        sequence = [event for event in events if event.application_name and event.application_name != "Filesystem"]
        previous: ActivityEvent | None = None
        for event in sequence:
            if previous is None or previous.application_name != event.application_name:
                if previous is not None:
                    self._transitions[previous.application_name][event.application_name] += 1
                    self._time_transitions[(previous.application_name, previous.timestamp.hour // 4)][event.application_name] += 1
                previous = event

    def predict(self, source: str, when: datetime | None = None) -> LearnedPrediction | None:
        bucket = self._time_transitions.get((source, (when or datetime.now()).hour // 4), Counter())
        counts = bucket or self._transitions.get(source, Counter())
        if not counts:
            return None
        target, count = max(counts.items(), key=lambda item: (item[1], item[0]))
        total = sum(counts.values())
        return LearnedPrediction(source, target, count / total if total else 0.0, total)
