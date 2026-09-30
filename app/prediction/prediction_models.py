"""Prediction value objects exposed independently of Qt and SQLAlchemy."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, frozen=True)
class PredictionResult:
    predicted_action: str
    confidence: float
    source_workflow: str | None
    timestamp: datetime

