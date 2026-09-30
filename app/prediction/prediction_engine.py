"""Rule-based next-action prediction from observed transition frequencies."""

from __future__ import annotations

from datetime import datetime

from app.database.repositories import ActivityRepository, PredictionRepository
from app.core.time import utc_now
from app.prediction.prediction_models import PredictionResult
from app.workflow.pattern_detector import PatternDetector
from app.workflow.learned_model import LearnedWorkflowModel


class PredictionEngine:
    """Predict the most frequent observed next application for the current app."""

    def __init__(self, activity_repository: ActivityRepository, prediction_repository: PredictionRepository, detector: PatternDetector | None = None) -> None:
        self.activity_repository = activity_repository
        self.prediction_repository = prediction_repository
        self.learned_model = LearnedWorkflowModel()
        self.detector = detector or PatternDetector()

    def predict(self, current_application: str | None = None, event_limit: int = 500) -> PredictionResult | None:
        events = self.activity_repository.recent(event_limit)
        transitions = self.detector.transitions(events)
        if not transitions:
            return None
        source = current_application
        if not source:
            sequence = self.detector.collapsed_applications(events)
            source = sequence[-1] if sequence else None
        if source:
            self.learned_model.fit(events)
            learned = self.learned_model.predict(source, events[-1].timestamp if events else None)
            if learned:
                result = PredictionResult(f"Open {learned.target}", learned.confidence, f"{learned.source} -> {learned.target}", utc_now())
                self.prediction_repository.add(result.predicted_action, result.confidence, result.source_workflow)
                return result
            return None
        if current_application:
            matching = [stat for stat in transitions if stat.source.casefold() == current_application.casefold()]
        else:
            sequence = self.detector.collapsed_applications(events)
            matching = [stat for stat in transitions if stat.source == (sequence[-1] if sequence else "")]
        if not matching:
            return None
        best = max(matching, key=lambda stat: (stat.count, stat.target))
        result = PredictionResult(
            predicted_action=f"Open {best.target}",
            confidence=best.confidence,
            source_workflow=f"{best.source} → {best.target}",
            timestamp=utc_now(),
        )
        self.prediction_repository.add(result.predicted_action, result.confidence, result.source_workflow)
        return result
