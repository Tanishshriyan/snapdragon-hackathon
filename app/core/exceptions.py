"""Domain-specific exceptions used to keep UI and services decoupled."""


class DoppelError(Exception):
    """Base exception for expected Doppel application errors."""


class ConfigurationError(DoppelError):
    """Raised when a setting cannot be used safely."""


class MonitoringError(DoppelError):
    """Raised when a monitor cannot be started or stopped cleanly."""


class RepositoryError(DoppelError):
    """Raised for an expected persistence-layer failure."""

