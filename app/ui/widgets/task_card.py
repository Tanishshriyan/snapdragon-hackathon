"""Compact task row used by planning views."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget


class TaskCard(QWidget):
    completed = Signal(int)
    deleted = Signal(int)

    def __init__(self, task: object, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.task_id = int(getattr(task, "id"))
        layout = QHBoxLayout(self)
        title = QLabel(str(getattr(task, "title", "Untitled task")))
        title.setObjectName("cardTitle")
        priority = QLabel(str(getattr(task, "priority", "medium")).upper())
        priority.setObjectName("mutedLabel")
        layout.addWidget(title, 1)
        layout.addWidget(priority)
        if getattr(task, "status", "pending") != "completed":
            done = QPushButton("Complete")
            done.clicked.connect(lambda: self.completed.emit(self.task_id))
            layout.addWidget(done)
        remove = QPushButton("Delete")
        remove.clicked.connect(lambda: self.deleted.emit(self.task_id))
        layout.addWidget(remove)

