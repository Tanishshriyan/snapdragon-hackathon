from datetime import datetime, timedelta

from app.core.events import ActivityObservation
from app.workflow.pattern_detector import PatternDetector


def test_workflow_detection_and_transition_statistics(service):
    applications = ["VS Code", "Terminal", "Chrome", "VS Code", "Terminal", "Chrome"]
    for index, application in enumerate(applications):
        service.record_observation(
            ActivityObservation(
                timestamp=datetime(2026, 1, 1, 10, 0) + timedelta(minutes=index),
                application_name=application,
                process_name=application,
                window_title=None,
            )
        )
    workflows = service.workflow_tracker.recent_workflows()
    assert any(workflow.name == "VS Code → Terminal → Chrome" for workflow in workflows)
    stats = PatternDetector().transitions(service.activity_repository.recent())
    vs_code_terminal = next(stat for stat in stats if stat.source == "VS Code" and stat.target == "Terminal")
    assert vs_code_terminal.count == 2
    assert vs_code_terminal.confidence == 1.0

