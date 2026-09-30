"""Prediction card with explicit baseline labeling."""

from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class PredictionCard(QFrame):
    def __init__(self, prediction: object | None, parent: object | None = None) -> None:
        super().__init__(parent)  # type: ignore[arg-type]
        self.setObjectName("predictionCard")
        layout = QVBoxLayout(self)
        title = QLabel("Predicted next action")
        title.setObjectName("mutedLabel")
        action = QLabel(
            str(getattr(prediction, "predicted_action", "Not enough observed history yet"))
        )
        action.setObjectName("cardTitle")
        confidence = getattr(prediction, "confidence", None)
        confidence_text = (
            f"Observed transition confidence: {float(confidence):.0%} · baseline"
            if confidence is not None
            else "Rule-based baseline · waiting for repeated observations"
        )
        detail = QLabel(confidence_text)
        detail.setObjectName("mutedLabel")
        layout.addWidget(title)
        layout.addWidget(action)
        layout.addWidget(detail)

