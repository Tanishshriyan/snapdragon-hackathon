"""Usable task and daily-plan editor."""

from __future__ import annotations

from datetime import date

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.ui.widgets.task_card import TaskCard


class TaskDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add task")
        form = QFormLayout(self)
        self.title = QLineEdit()
        self.title.setPlaceholderText("What would move the work forward?")
        self.priority = QComboBox()
        self.priority.addItems(["low", "medium", "high"])
        self.date = QLineEdit(QDate.currentDate().toString("yyyy-MM-dd"))
        self.time = QLineEdit()
        self.time.setPlaceholderText("Optional, e.g. 10:00")
        self.minutes = QSpinBox()
        self.minutes.setRange(0, 1440)
        self.minutes.setSuffix(" min")
        form.addRow("Title", self.title)
        form.addRow("Priority", self.priority)
        form.addRow("Date", self.date)
        form.addRow("Time", self.time)
        form.addRow("Estimated", self.minutes)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def values(self) -> dict[str, object]:
        scheduled_date = date.fromisoformat(self.date.text().strip())
        return {
            "title": self.title.text(),
            "priority": self.priority.currentText(),
            "scheduled_date": scheduled_date,
            "scheduled_time": self.time.text().strip() or None,
            "estimated_minutes": self.minutes.value() or None,
        }


class PlannerView(QWidget):
    def __init__(self, service: object, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.service = service
        self.layout = QVBoxLayout(self)
        header = QHBoxLayout()
        title = QLabel("Plan your next chapter")
        title.setObjectName("pageTitle")
        header.addWidget(title)
        header.addStretch()
        add_button = QPushButton("Add task")
        add_button.clicked.connect(self._add_task)
        header.addWidget(add_button)
        self.layout.addLayout(header)
        self.subtitle = QLabel("Plan tomorrow, or shape today around the work that matters.")
        self.subtitle.setObjectName("subtitle")
        self.layout.addWidget(self.subtitle)
        self.task_container = QVBoxLayout()
        self.layout.addLayout(self.task_container)
        self.layout.addStretch()
        self.refresh()

    def refresh(self) -> None:
        while self.task_container.count():
            item = self.task_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        tasks = self.service.task_repository.list_open()
        if not tasks:
            label = QLabel("No open tasks. Add one to begin shaping tomorrow's plan.")
            label.setObjectName("mutedLabel")
            self.task_container.addWidget(label)
            return
        for task in tasks:
            card = TaskCard(task)
            card.completed.connect(self._complete)
            card.deleted.connect(self._delete)
            self.task_container.addWidget(card)

    def _add_task(self) -> None:
        dialog = TaskDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            values = dialog.values()
            title = str(values.pop("title"))
            task = self.service.task_manager.create_task(title, **values)
            self.service.plan_manager.create_plan(task.scheduled_date or date.today())
            self.service.plan_manager.add_task_to_plan(task.scheduled_date or date.today(), task)
            self.refresh()
        except (ValueError, TypeError) as error:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.warning(self, "Could not add task", str(error))

    def _complete(self, task_id: int) -> None:
        self.service.task_manager.complete_task(task_id)
        self.refresh()

    def _delete(self, task_id: int) -> None:
        self.service.task_manager.delete_task(task_id)
        self.refresh()
