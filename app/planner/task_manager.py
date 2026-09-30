"""Task CRUD and completion use cases."""

from __future__ import annotations

from datetime import date

from app.database.models import Task
from app.database.repositories import TaskRepository


class TaskManager:
    """Validate basic task inputs before passing them to persistence."""

    def __init__(self, repository: TaskRepository) -> None:
        self.repository = repository

    def create_task(self, title: str, **kwargs: object) -> Task:
        if not title.strip():
            raise ValueError("Task title cannot be empty")
        estimated = kwargs.get("estimated_minutes")
        if estimated is not None and int(estimated) <= 0:
            raise ValueError("Estimated duration must be positive")
        return self.repository.create(title=title, **kwargs)  # type: ignore[arg-type]

    def edit_task(self, task_id: int, **changes: object) -> Task | None:
        if "title" in changes and not str(changes["title"]).strip():
            raise ValueError("Task title cannot be empty")
        return self.repository.update(task_id, **changes)

    def complete_task(self, task_id: int) -> Task | None:
        return self.repository.complete(task_id)

    def delete_task(self, task_id: int) -> bool:
        return self.repository.delete(task_id)

    def tasks_for(self, plan_date: date) -> list[Task]:
        return self.repository.list_for_date(plan_date)

