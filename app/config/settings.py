"""Centralized, local-first application settings.

Settings are deliberately small and serializable. User-editable preferences are
stored in SQLite by the planner/service layer; this module contains safe runtime
defaults and filesystem locations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import os
from typing import Iterable


def project_root() -> Path:
    """Return the repository/application root for the source checkout."""

    return Path(__file__).resolve().parents[2]


@dataclass(slots=True)
class Settings:
    """Runtime configuration with conservative privacy defaults."""

    database_path: Path = field(default_factory=lambda: project_root() / "data" / "doppel.db")
    log_directory: Path = field(default_factory=lambda: project_root() / "data" / "logs")
    monitoring_interval_seconds: float = 1.5
    inactivity_timeout_seconds: int = 15 * 60
    monitored_directories: tuple[Path, ...] = ()
    store_window_titles: bool = True
    store_file_paths: bool = True
    prediction_enabled: bool = True
    automatic_workspace_preparation: bool = False

    def ensure_directories(self) -> None:
        """Create only the application-owned data directories."""

        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.log_directory.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_environment(cls) -> "Settings":
        """Load optional path/runtime overrides without requiring dotenv."""

        settings = cls()
        database_path = os.getenv("DOPPEL_DATABASE_PATH")
        if database_path:
            settings.database_path = Path(database_path).expanduser()
        interval = os.getenv("DOPPEL_MONITORING_INTERVAL")
        if interval:
            try:
                settings.monitoring_interval_seconds = max(0.5, float(interval))
            except ValueError:
                pass
        timeout = os.getenv("DOPPEL_INACTIVITY_TIMEOUT")
        if timeout:
            try:
                settings.inactivity_timeout_seconds = max(30, int(timeout))
            except ValueError:
                pass
        return settings

    def with_monitored_directories(self, directories: Iterable[str | Path]) -> "Settings":
        """Return a copy with normalized, user-selected monitoring directories."""

        self.monitored_directories = tuple(Path(directory).expanduser().resolve() for directory in directories)
        return self


DEFAULT_SETTINGS = Settings.from_environment()

