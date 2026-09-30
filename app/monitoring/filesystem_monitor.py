"""Watch only explicitly selected folders and emit metadata-only events."""

from __future__ import annotations

from datetime import datetime
import logging
from pathlib import Path
from typing import Callable, Iterable

from app.core.events import FileActivity
from app.core.exceptions import MonitoringError
from app.core.time import utc_now

logger = logging.getLogger(__name__)

try:  # pragma: no cover - watchdog callback threading is integration behavior
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer
except ImportError:  # pragma: no cover
    FileSystemEventHandler = object  # type: ignore[assignment,misc]
    Observer = None


class _Handler(FileSystemEventHandler):
    def __init__(self, callback: Callable[[FileActivity], None], store_file_paths: bool) -> None:
        super().__init__()
        self.callback = callback
        self.store_file_paths = store_file_paths

    def _emit(self, event_type: str, path: str, is_directory: bool) -> None:
        self.callback(
            FileActivity(
                timestamp=utc_now(),
                event_type=event_type,
                path=path if self.store_file_paths else "",
                is_directory=is_directory,
            )
        )

    def on_created(self, event: object) -> None:
        self._emit("file_created", str(event.src_path), bool(event.is_directory))

    def on_modified(self, event: object) -> None:
        self._emit("file_modified", str(event.src_path), bool(event.is_directory))

    def on_deleted(self, event: object) -> None:
        self._emit("file_deleted", str(event.src_path), bool(event.is_directory))

    def on_moved(self, event: object) -> None:
        self._emit("file_moved", str(event.dest_path), bool(event.is_directory))


class FilesystemMonitor:
    """Lifecycle wrapper around watchdog's background observer."""

    def __init__(self, directories: Iterable[Path], callback: Callable[[FileActivity], None], store_file_paths: bool = True) -> None:
        self.directories = tuple(directory.resolve() for directory in directories)
        self.callback = callback
        self.store_file_paths = store_file_paths
        self._observer: Observer | None = None

    @property
    def is_running(self) -> bool:
        return bool(self._observer and self._observer.is_alive())

    def start(self) -> None:
        if self.is_running or not self.directories:
            return
        if Observer is None:
            raise MonitoringError("watchdog is not installed; filesystem monitoring is unavailable")
        observer = Observer()
        handler = _Handler(self.callback, self.store_file_paths)
        for directory in self.directories:
            if directory.is_dir():
                observer.schedule(handler, str(directory), recursive=True)
            else:
                logger.warning("Skipping unconfigured or missing monitored directory: %s", directory)
        observer.start()
        self._observer = observer

    def stop(self) -> None:
        if self._observer is None:
            return
        self._observer.stop()
        self._observer.join(timeout=5)
        self._observer = None
