from datetime import date, timedelta


def test_tomorrows_plan_and_task_completion(service):
    tomorrow = date.today() + timedelta(days=1)
    task = service.task_manager.create_task(
        "Study DSA",
        priority="high",
        scheduled_date=tomorrow,
        estimated_minutes=60,
    )
    service.plan_manager.create_plan(tomorrow)
    service.plan_manager.add_task_to_plan(tomorrow, task)
    assert [link.task.title for link in service.plan_manager.tomorrow().tasks] == ["Study DSA"]
    service.task_manager.complete_task(task.id)
    assert service.task_repository.get(task.id).status == "completed"

