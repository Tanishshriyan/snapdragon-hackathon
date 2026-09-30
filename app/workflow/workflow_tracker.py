"""Persist candidate workflows derived from actual observed events."""

from __future__ import annotations

from app.database.repositories import ActivityRepository, WorkflowRepository
from app.workflow.pattern_detector import PatternDetector


class WorkflowTracker:
    def __init__(self, activity_repository: ActivityRepository, workflow_repository: WorkflowRepository, detector: PatternDetector | None = None) -> None:
        self.activity_repository = activity_repository
        self.workflow_repository = workflow_repository
        self.detector = detector or PatternDetector()

    def refresh(self, event_limit: int = 500) -> list:
        events = self.activity_repository.recent(event_limit)
        candidates = self.detector.candidates(events)
        for candidate in candidates:
            self.workflow_repository.upsert_pattern(
                candidate.name,
                candidate.sequence,
                candidate.confidence,
                candidate.occurrence_count,
            )
        return self.workflow_repository.list_recent()

    def recent_workflows(self, limit: int = 10) -> list:
        return self.workflow_repository.list_recent(limit)

