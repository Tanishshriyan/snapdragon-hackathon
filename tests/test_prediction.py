from datetime import datetime, timedelta

from app.core.events import ActivityObservation


def test_prediction_uses_observed_transition_frequency(service):
    applications = ["VS Code", "Terminal", "Chrome", "VS Code", "Terminal", "Chrome"]
    for index, application in enumerate(applications):
        service.record_observation(
            ActivityObservation(
                timestamp=datetime(2026, 1, 1, 12, 0) + timedelta(minutes=index),
                application_name=application,
                process_name=application,
                window_title=None,
            )
        )
    prediction = service.prediction_engine.predict("VS Code")
    assert prediction is not None
    assert prediction.predicted_action == "Open Terminal"
    assert prediction.confidence == 1.0

