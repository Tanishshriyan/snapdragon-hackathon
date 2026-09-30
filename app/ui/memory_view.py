"""Saved-session memory view."""

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class MemoryView(QWidget):
    def __init__(self, service: object, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.service = service
        self.layout = QVBoxLayout(self)
        title = QLabel("Memory")
        title.setObjectName("pageTitle")
        self.layout.addWidget(title)
        self.memory_label = QLabel()
        self.memory_label.setObjectName("resumeCard")
        self.memory_label.setWordWrap(True)
        self.layout.addWidget(self.memory_label)
        self.layout.addStretch()
        self.refresh()

    def refresh(self) -> None:
        memory = self.service.memory_manager.latest_session()
        if not memory:
            self.memory_label.setText("No completed work session has been saved yet.")
            return
        recent = ", ".join(memory.recent_activity) or "No recent activity summary"
        self.memory_label.setText(
            f"{memory.summary}\n\nProject: {memory.project_context or 'Not identified'}\n"
            f"Recent: {recent}"
        )

