"""Recent activity view showing metadata only."""

from PySide6.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget

from app.ui.widgets.activity_card import ActivityCard


class ActivityView(QWidget):
    def __init__(self, service: object, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.service = service
        layout = QVBoxLayout(self)
        title = QLabel("Activity trail")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        subtitle = QLabel("High-level application and configured-folder events. No keystrokes or file contents.")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)
        self.content = QVBoxLayout()
        layout.addLayout(self.content)
        layout.addStretch()
        self.refresh()

    def refresh(self) -> None:
        while self.content.count():
            item = self.content.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        events = list(reversed(self.service.activity_repository.recent(30)))
        for event in events:
            self.content.addWidget(ActivityCard(event))
        if not events:
            empty = QLabel("Doppel has not observed a high-level event yet.")
            empty.setObjectName("mutedLabel")
            self.content.addWidget(empty)

