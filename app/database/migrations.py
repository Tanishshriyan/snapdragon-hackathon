"""Minimal initial schema migration for the foundation phase."""

from sqlalchemy import Engine

from app.database.models import Base


def initialize_database(engine: Engine) -> None:
    """Create missing tables; future phases can replace this with versioned migrations."""

    Base.metadata.create_all(engine)

