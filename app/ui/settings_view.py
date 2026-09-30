"""Privacy and monitoring controls."""

from __future__ import annotations

from PySide6.QtWidgets import QCheckBox, QFileDialog, QLabel, QPushButton, QSpinBox, QVBoxLayout, QWidget


from app.ai.onnx_runtime import detect_runtime

class SettingsView(QWidget):
    def __init__(self, service: object, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.service = service
        layout = QVBoxLayout(self)
        title = QLabel("Settings")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        privacy = QLabel("Privacy boundary")
        privacy.setObjectName("sectionTitle")
        layout.addWidget(privacy)
        for text in (
            "No keystrokes, passwords, clipboard contents, or screenshots are collected.",
            "Only explicitly selected folders are watched, and file contents are never stored.",
            "All data stays in the local SQLite database and local log directory.",
        ):
            label = QLabel("• " + text)
            label.setObjectName("mutedLabel")
            label.setWordWrap(True)
            layout.addWidget(label)
        interval_label = QLabel("Foreground monitoring interval (seconds)")
        self.interval = QSpinBox()
        self.interval.setRange(1, 60)
        self.interval.setValue(int(self.service.settings.monitoring_interval_seconds))
        layout.addWidget(interval_label)
        layout.addWidget(self.interval)
        self.prediction = QCheckBox("Enable baseline next-action predictions")
        self.prediction.setChecked(self.service.settings.prediction_enabled)
        self.prediction.stateChanged.connect(self._toggle_prediction)
        layout.addWidget(self.prediction)
        self.auto_resume = QCheckBox("Allow automatic launch of registered resume apps")
        self.auto_resume.setChecked(self.service.settings.automatic_workspace_preparation)
        self.auto_resume.stateChanged.connect(self._toggle_auto_resume)
        layout.addWidget(self.auto_resume)
        runtime = detect_runtime()
        self.runtime_label = QLabel(f"Inference runtime: {runtime.message}")
        self.runtime_label.setObjectName("mutedLabel")
        layout.addWidget(self.runtime_label)
        folder_button = QPushButton("Choose monitored folder")
        folder_button.clicked.connect(self._choose_folder)
        layout.addWidget(folder_button)
        self.folders = QLabel(self._folder_text())
        self.folders.setObjectName("mutedLabel")
        self.folders.setWordWrap(True)
        layout.addWidget(self.folders)
        self.status = QLabel()
        self.status.setObjectName("mutedLabel")
        layout.addWidget(self.status)
        self.interval.valueChanged.connect(self._save_interval)
        layout.addStretch()

    def _toggle_prediction(self, state: int) -> None:
        self.service.settings.prediction_enabled = bool(state)
        self.service.preference_repository.set("prediction_enabled", str(bool(state)))

    def _toggle_auto_resume(self, state: int) -> None:
        self.service.settings.automatic_workspace_preparation = bool(state)
        self.service.preference_repository.set("automatic_workspace_preparation", str(bool(state)))

    def _save_interval(self, value: int) -> None:
        self.service.settings.monitoring_interval_seconds = float(value)
        self.service.preference_repository.set("monitoring_interval_seconds", str(value))

    def _choose_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Choose a project folder")
        if not folder:
            return
        self.service.set_monitored_directories([folder])
        self.folders.setText(self._folder_text())
        self.status.setText("Folder monitoring updated. It is active while Doppel is running.")

    def _folder_text(self) -> str:
        folders = self.service.settings.monitored_directories
        return "Monitored: " + (", ".join(str(folder) for folder in folders) if folders else "none")

