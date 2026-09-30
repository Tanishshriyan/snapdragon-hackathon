"""Main PySide6 window and lifecycle bridge."""

from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QListWidget, QMainWindow, QStackedWidget, QWidget

from app.ui.activity_view import ActivityView
from app.ui.dashboard import Dashboard
from app.ui.memory_view import MemoryView
from app.ui.planner_view import PlannerView
from app.ui.settings_view import SettingsView


STYLE = """
QMainWindow, QWidget { background: #f6f7fb; color: #172033; font-family: 'Segoe UI'; }
QListWidget { background: #111827; color: #cbd5e1; border: none; padding: 18px 8px; }
QListWidget::item { padding: 12px 14px; border-radius: 8px; }
QListWidget::item:selected { background: #2e6bff; color: white; }
QLabel#eyebrow { color: #2e6bff; font-size: 12px; font-weight: 700; letter-spacing: 1px; }
QLabel#pageTitle { color: #111827; font-size: 28px; font-weight: 700; margin-bottom: 2px; }
QLabel#subtitle, QLabel#mutedLabel { color: #667085; font-size: 13px; }
QLabel#sectionTitle { color: #111827; font-size: 17px; font-weight: 700; margin-top: 8px; }
QLabel#resumeCard, QLabel#contextCard, QFrame#activityCard, QFrame#predictionCard {
    background: white; border: 1px solid #e5e7eb; border-radius: 12px; padding: 12px;
}
QLabel#cardTitle { color: #111827; font-size: 15px; font-weight: 600; }
QPushButton { background: #2e6bff; color: white; border: none; border-radius: 8px; padding: 9px 14px; }
QPushButton:hover { background: #1e54d9; }
QLineEdit, QSpinBox, QComboBox { background: white; border: 1px solid #d0d5dd; border-radius: 6px; padding: 7px; }
QScrollArea { border: none; }
"""


class MainWindow(QMainWindow):
    """Responsive shell; polling work is kept in a short QTimer callback."""

    def __init__(self, service: object) -> None:
        super().__init__()
        self.service = service
        self.setWindowTitle("Doppel — Your Personal AI Work Twin")
        self.resize(1180, 760)
        self.setStyleSheet(STYLE)
        self._build_ui()
        self.timer = QTimer(self)
        self.timer.setInterval(int(self.service.settings.monitoring_interval_seconds * 1000))
        self.timer.timeout.connect(self._poll)
        self.service.start_monitoring()
        self.timer.start()

    def _build_ui(self) -> None:
        root = QWidget()
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        self.navigation = QListWidget()
        self.navigation.setFixedWidth(190)
        self.navigation.addItems(["Doppel", "Planner", "Activity", "Memory", "Settings"])
        self.navigation.currentRowChanged.connect(self._select_view)
        layout.addWidget(self.navigation)
        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(30, 26, 30, 24)
        self.stack = QStackedWidget()
        self.dashboard = Dashboard(self.service)
        self.planner = PlannerView(self.service)
        self.activity = ActivityView(self.service)
        self.memory = MemoryView(self.service)
        self.settings = SettingsView(self.service)
        self.dashboard.open_planner.connect(lambda: self.navigation.setCurrentRow(1))
        for view in (self.dashboard, self.planner, self.activity, self.memory, self.settings):
            self.stack.addWidget(view)
        content_layout.addWidget(self.stack)
        layout.addWidget(content, 1)
        self.setCentralWidget(root)
        self.navigation.setCurrentRow(0)

    def _select_view(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        view = self.stack.widget(index)
        if hasattr(view, "refresh"):
            view.refresh()

    def _poll(self) -> None:
        self.service.poll()
        configured_interval = int(self.service.settings.monitoring_interval_seconds * 1000)
        if self.timer.interval() != configured_interval:
            self.timer.setInterval(configured_interval)
        self.dashboard.refresh()
        if self.stack.currentWidget() is self.activity:
            self.activity.refresh()

    def closeEvent(self, event: object) -> None:
        self.timer.stop()
        self.service.shutdown()
        event.accept()  # type: ignore[attr-defined]
