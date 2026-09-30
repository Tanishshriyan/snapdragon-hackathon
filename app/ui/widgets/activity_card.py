"""Activity metadata card."""

from __future__ import annotations

from PySide6.QtWidgets import QVBoxLayout, QLabel, QFrame


class ActivityCard(QFrame):
    def __init__(self, event: object, parent: object | None = None) -> None:
        super().__init__(parent)  # type: ignore[arg-type]
        self.setObjectName("activityCard")
        layout = QVBoxLayout(self)
        application = QLabel(str(getattr(event, "application_name", "Unknown")))
        application.setObjectName("cardTitle")
        detail = QLabel(
            f"{getattr(event, 'event_type', 'activity')} · "
            f"{getattr(event, 'window_title', None) or 'No window title stored'}"
        )
        detail.setObjectName("mutedLabel")
        layout.addWidget(application)
        layout.addWidget(detail)

