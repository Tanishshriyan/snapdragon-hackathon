"""Doppel desktop entry point."""

from __future__ import annotations

import sys

from app.services.application_service import build_application_service


def main() -> int:
    """Start the local desktop application."""

    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    app.setApplicationName("Doppel")
    service = build_application_service()
    from app.ui.main_window import MainWindow

    window = MainWindow(service)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

