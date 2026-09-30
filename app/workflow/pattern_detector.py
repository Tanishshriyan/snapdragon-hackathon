"""Count application transitions and repeated short sequences."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Sequence

from app.database.models import ActivityEvent
from app.workflow.workflow_models import TransitionStat, WorkflowCandidate


class PatternDetector:
    """A transparent baseline detector; no machine-learning claim is made."""

    @staticmethod
    def collapsed_applications(events: Iterable[ActivityEvent]) -> list[str]:
        sequence: list[str] = []
        for event in events:
            name = event.application_name.strip()
            if not name or name == "Filesystem":
                continue
            if not sequence or sequence[-1] != name:
                sequence.append(name)
        return sequence

    def transitions(self, events: Iterable[ActivityEvent]) -> list[TransitionStat]:
        sequence = self.collapsed_applications(events)
        pair_counts = Counter(zip(sequence, sequence[1:]))
        source_counts = Counter(source for source, _ in zip(sequence, sequence[1:]))
        return [
            TransitionStat(source, target, count, source_counts[source])
            for (source, target), count in pair_counts.items()
        ]

    def candidates(self, events: Iterable[ActivityEvent], window_size: int = 3) -> list[WorkflowCandidate]:
        sequence = self.collapsed_applications(events)
        if len(sequence) < window_size:
            return []
        windows = [tuple(sequence[index : index + window_size]) for index in range(len(sequence) - window_size + 1)]
        counts = Counter(windows)
        starts = Counter(window[0] for window in windows)
        return [
            WorkflowCandidate(window, count, count / starts[window[0]])
            for window, count in counts.most_common()
            if count >= 2
        ]

