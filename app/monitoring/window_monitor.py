"""Foreground-window polling with a safe non-Windows fallback.

The Windows path uses pywin32 APIs. The fallback exists so database and service
tests can run on CI hosts without pretending to observe a real desktop.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import logging

from app.core.events import ActivityObservation
from app.core.time import utc_now
from app.monitoring.process_monitor import ProcessMonitor

logger = logging.getLogger(__name__)

try:  # pragma: no cover - exercised only on Windows with pywin32 installed
    import win32gui
    import win32process
except ImportError:  # pragma: no cover - platform dependent
    win32gui = None
    win32process = None


@dataclass(slots=True, frozen=True)
class ForegroundWindow:
    application_name: str
    process_name: str
    window_title: str | None
    handle: int | None = None


class WindowMonitor:
    """Read the current foreground app; never reads input, clipboard, or pixels."""

    def __init__(self, process_monitor: ProcessMonitor | None = None, store_window_titles: bool = True) -> None:
        self.process_monitor = process_monitor or ProcessMonitor()
        self.store_window_titles = store_window_titles
        self._last_fingerprint: tuple[str, str, str | None] | None = None

    def read_foreground(self) -> ForegroundWindow | None:
        if win32gui is None or win32process is None:
            return None
        try:
            handle = int(win32gui.GetForegroundWindow())
            if not handle:
                return None
            _, pid = win32process.GetWindowThreadProcessId(handle)
            process_name = self.process_monitor.name_for_pid(pid)
            title = str(win32gui.GetWindowText(handle) or "")
            return ForegroundWindow(
                application_name=self._display_name(process_name),
                process_name=process_name,
                window_title=title if self.store_window_titles and title else None,
                handle=handle,
            )
        except (OSError, RuntimeError, ValueError) as error:
            logger.debug("Unable to read foreground window: %s", error)
            return None

    def poll(self, timestamp: datetime | None = None) -> ActivityObservation | None:
        current = self.read_foreground()
        if current is None:
            return None
        fingerprint = (current.application_name, current.process_name, current.window_title)
        if fingerprint == self._last_fingerprint:
            return None
        self._last_fingerprint = fingerprint
        return ActivityObservation(
            timestamp=timestamp or utc_now(),
            application_name=current.application_name,
            process_name=current.process_name,
            window_title=current.window_title,
        )

    @staticmethod
    def _display_name(process_name: str) -> str:
        clean_name = process_name.removesuffix(".exe")
        known_names = {
            "code": "VS Code",
            "devenv": "Visual Studio",
            "chrome": "Chrome",
            "msedge": "Edge",
            "windowsterminal": "Windows Terminal",
            "powershell": "PowerShell",
            "explorer": "File Explorer",
        }
        return known_names.get(clean_name.casefold(), clean_name or "Unknown")
