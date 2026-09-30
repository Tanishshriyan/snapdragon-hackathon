from __future__ import annotations

import pytest

from app.config.settings import Settings
from app.services.application_service import ApplicationService


@pytest.fixture()
def service(tmp_path):
    settings = Settings(
        database_path=tmp_path / "doppel-test.db",
        log_directory=tmp_path / "logs",
        inactivity_timeout_seconds=30,
    )
    app_service = ApplicationService(settings)
    yield app_service
    app_service.shutdown()

