from datetime import datetime, timedelta

from app.core.events import ActivityObservation


def test_session_closes_after_inactivity(service):
    started = datetime(2026, 1, 1, 9, 0)
    service.session_monitor.record_observation(
        ActivityObservation(started, "VS Code", "code.exe", "project")
    )
    assert service.session_monitor.active_session is not None
    service.session_monitor.tick(started + timedelta(seconds=31))
    assert service.session_monitor.active_session is None
    latest = service.session_repository.latest()
    assert latest.ended_at is not None
    assert latest.primary_application == "VS Code"

