from datetime import date

from app.core.events import ActivityObservation


def test_database_initializes_and_supports_crud(service):
    task = service.task_manager.create_task("Finish database tests", scheduled_date=date.today())
    assert task.id is not None
    assert service.task_repository.get(task.id).title == "Finish database tests"

    plan = service.plan_manager.create_plan(date.today(), "Small focused plan")
    service.plan_manager.add_task_to_plan(date.today(), task)
    loaded = service.plan_manager.plan_for(date.today())
    assert plan.id == loaded.id
    assert loaded.tasks[0].task.title == task.title

    event = service.activity_repository.add_observation(
        ActivityObservation(
            timestamp=task.created_at,
            application_name="VS Code",
            process_name="code.exe",
            window_title="Doppel - Code",
        )
    )
    assert event.id is not None
    assert service.activity_repository.latest().application_name == "VS Code"

