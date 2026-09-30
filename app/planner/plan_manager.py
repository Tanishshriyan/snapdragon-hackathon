"""Daily plan use cases, including Tomorrow's Plan."""

from __future__ import annotations

from datetime import date, timedelta

from app.database.models import DailyPlan, PlanTask, Task
from app.database.repositories import PlanRepository, TaskRepository


class PlanManager:
    def __init__(self, plan_repository: PlanRepository, task_repository: TaskRepository) -> None:
        self.plan_repository = plan_repository
        self.task_repository = task_repository

    def create_plan(self, plan_date: date, notes: str = "") -> DailyPlan:
        return self.plan_repository.get_or_create(plan_date, notes)

    def add_task_to_plan(self, plan_date: date, task: Task, sequence_order: int | None = None) -> PlanTask:
        if task.id is None:
            raise ValueError("Task must be persisted before adding it to a plan")
        return self.plan_repository.add_task(plan_date, task.id, sequence_order)

    def plan_for(self, plan_date: date) -> DailyPlan | None:
        return self.plan_repository.get(plan_date)

    def tomorrow(self, today: date | None = None) -> DailyPlan | None:
        return self.plan_for((today or date.today()) + timedelta(days=1))

    def tomorrow_tasks(self, today: date | None = None) -> list[Task]:
        plan = self.tomorrow(today)
        if plan is None:
            return []
        return [link.task for link in plan.tasks if link.task is not None]

