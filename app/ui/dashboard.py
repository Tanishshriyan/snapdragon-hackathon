"""Doppel's primary dashboard."""

from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.ui.widgets.prediction_card import PredictionCard
from app.ui.widgets.task_card import TaskCard


class Dashboard(QWidget):
    open_planner = Signal()

    def __init__(self, service: object, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.service = service
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(14)
        self._build_static()
        self.refresh()

    def _build_static(self) -> None:
        greeting = QLabel("GOOD TO SEE YOU")
        greeting.setObjectName("eyebrow")
        heading = QLabel("Your work, remembered.")
        heading.setObjectName("pageTitle")
        subtitle = QLabel("Doppel keeps the thread between sessions — privately, on this device.")
        subtitle.setObjectName("subtitle")
        self.layout.addWidget(greeting)
        self.layout.addWidget(heading)
        self.layout.addWidget(subtitle)

        plan_header = QHBoxLayout()
        plan_header.addWidget(self._section_label("Today's Plan"))
        plan_header.addStretch()
        plan_button = QPushButton("Plan Tomorrow")
        plan_button.clicked.connect(self.open_planner.emit)
        plan_header.addWidget(plan_button)
        self.layout.addLayout(plan_header)
        self.plan_container = QVBoxLayout()
        self.layout.addLayout(self.plan_container)

        resume_header = self._section_label("Continue Where You Left Off")
        self.layout.addWidget(resume_header)
        self.resume_label = QLabel()
        self.resume_label.setObjectName("resumeCard")
        self.resume_label.setWordWrap(True)
        self.layout.addWidget(self.resume_label)
        resume_button = QPushButton("Pick Up Where I Left Off")
        resume_button.clicked.connect(self._prepare_workspace)
        self.layout.addWidget(resume_button, alignment=Qt.AlignmentFlag.AlignLeft)

        self.context_label = QLabel()
        self.context_label.setObjectName("contextCard")
        self.context_label.setWordWrap(True)
        self.layout.addWidget(self._section_label("Current Context"))
        self.layout.addWidget(self.context_label)
        self.layout.addWidget(self._section_label("Local reasoning"))
        self.reasoning_label = QLabel()
        self.reasoning_label.setObjectName("contextCard")
        self.reasoning_label.setWordWrap(True)

        self.layout.addWidget(self._section_label("Predicted Next Action"))
        self.prediction_host = QVBoxLayout()
        self.layout.addLayout(self.prediction_host)
        self.layout.addWidget(self._section_label("Recent Workflows"))
        self.workflow_label = QLabel()
        self.workflow_label.setObjectName("mutedLabel")
        self.workflow_label.setWordWrap(True)
        self.layout.addWidget(self.workflow_label)
        self.layout.addStretch()

    @staticmethod
    def _section_label(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("sectionTitle")
        return label

    def refresh(self) -> None:
        plan = self.service.latest_plan(date.today())
        while self.plan_container.count():
            item = self.plan_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if plan and plan.tasks:
            for link in plan.tasks:
                card = TaskCard(link.task)
                card.completed.connect(self._complete_task)
                card.deleted.connect(self._delete_task)
                self.plan_container.addWidget(card)
        else:
            empty = QLabel("No tasks planned for today yet. Start with a small next step.")
            empty.setObjectName("mutedLabel")
            self.plan_container.addWidget(empty)

        resume = self.service.resume_context()
        if resume.session:
            session = resume.session
            self.resume_label.setText(
                f"{session.summary or 'A saved session is ready.'}\n"
                f"Last app: {session.primary_application or 'Unknown'} · "
                f"Last session: {session.started_at.strftime('%b %d, %H:%M')}"
            )
        else:
            self.resume_label.setText("Your first saved work session will appear here.")
        context = self.service.context_engine.current
        reasoning = self.service.explain_current_context()
        self.reasoning_label.setText(f"{reasoning.text}\n\nProvider: {reasoning.provider}")
        self.context_label.setText(context.summary if context else "No active context observed yet.")

        while self.prediction_host.count():
            item = self.prediction_host.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.prediction_host.addWidget(PredictionCard(self.service.current_prediction()))
        workflows = self.service.workflow_tracker.recent_workflows(5)
        self.workflow_label.setText(
            "\n".join(f"{workflow.name} · {workflow.occurrence_count} observations" for workflow in workflows)
            or "Repeated application patterns will appear after Doppel observes them."
        )

    def _complete_task(self, task_id: int) -> None:
        self.service.task_manager.complete_task(task_id)
        self.refresh()

    def _delete_task(self, task_id: int) -> None:
        self.service.task_manager.delete_task(task_id)
        self.refresh()

    def _prepare_workspace(self) -> None:
        from PySide6.QtWidgets import QMessageBox

        result = self.service.prepare_workspace(launch=self.service.settings.automatic_workspace_preparation)
        QMessageBox.information(self, "Workspace preparation", result.message)
