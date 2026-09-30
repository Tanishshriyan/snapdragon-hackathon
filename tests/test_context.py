from datetime import datetime

from app.core.events import ActivityObservation


def test_context_generation_is_deterministic(service):
    task = service.task_manager.create_task("Java assignment", scheduled_date=None)
    service.record_observation(
        ActivityObservation(
            timestamp=datetime(2026, 1, 1, 10, 0),
            application_name="VS Code",
            process_name="code.exe",
            window_title="assignment.java - VS Code",
        )
    )
    context = service.context_engine.current
    assert context.project_context == "Java assignment development"
    assert context.current_task_id == task.id
    assert service.context_repository.latest().summary == context.summary

