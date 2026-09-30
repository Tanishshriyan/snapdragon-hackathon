"""Small repository objects that keep SQLAlchemy out of most application code."""

from __future__ import annotations

from datetime import date, datetime
import json
from typing import Any, Iterable

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, sessionmaker, selectinload

from app.core.events import ActivityObservation, CurrentContext, FileActivity
from app.core.time import utc_now
from app.database.models import (
    ActivityEvent,
    ContextSnapshot,
    DailyPlan,
    PlanTask,
    Prediction,
    Task,
    UserPreference,
    WorkSession,
    Workflow,
    WorkflowStep,
)


class RepositoryBase:
    """Base class exposing a fresh short-lived session per operation."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory


class TaskRepository(RepositoryBase):
    def create(
        self,
        title: str,
        description: str = "",
        priority: str = "medium",
        scheduled_date: date | None = None,
        scheduled_time: str | None = None,
        estimated_minutes: int | None = None,
    ) -> Task:
        with self.session_factory() as session:
            task = Task(
                title=title.strip(),
                description=description.strip(),
                priority=priority,
                scheduled_date=scheduled_date,
                scheduled_time=scheduled_time,
                estimated_minutes=estimated_minutes,
            )
            session.add(task)
            session.commit()
            session.refresh(task)
            return task

    def get(self, task_id: int) -> Task | None:
        with self.session_factory() as session:
            return session.get(Task, task_id)

    def list_for_date(self, scheduled_date: date, include_completed: bool = True) -> list[Task]:
        with self.session_factory() as session:
            statement = select(Task).where(Task.scheduled_date == scheduled_date).order_by(Task.created_at)
            if not include_completed:
                statement = statement.where(Task.status != "completed")
            return list(session.scalars(statement).all())

    def list_open(self) -> list[Task]:
        with self.session_factory() as session:
            return list(session.scalars(select(Task).where(Task.status != "completed").order_by(Task.created_at)).all())

    def update(self, task_id: int, **changes: Any) -> Task | None:
        with self.session_factory() as session:
            task = session.get(Task, task_id)
            if task is None:
                return None
            for key, value in changes.items():
                if hasattr(task, key) and key not in {"id", "created_at"}:
                    setattr(task, key, value)
            session.commit()
            session.refresh(task)
            return task

    def complete(self, task_id: int) -> Task | None:
        return self.update(task_id, status="completed", completed_at=utc_now())

    def delete(self, task_id: int) -> bool:
        with self.session_factory() as session:
            task = session.get(Task, task_id)
            if task is None:
                return False
            session.delete(task)
            session.commit()
            return True


class PlanRepository(RepositoryBase):
    def get_or_create(self, plan_date: date, notes: str = "") -> DailyPlan:
        with self.session_factory() as session:
            plan = session.scalar(select(DailyPlan).where(DailyPlan.plan_date == plan_date))
            if plan is None:
                plan = DailyPlan(plan_date=plan_date, notes=notes)
                session.add(plan)
                session.commit()
                session.refresh(plan)
            return plan

    def get(self, plan_date: date) -> DailyPlan | None:
        with self.session_factory() as session:
            statement = (
                select(DailyPlan)
                .options(selectinload(DailyPlan.tasks).selectinload(PlanTask.task))
                .where(DailyPlan.plan_date == plan_date)
            )
            return session.scalar(statement)

    def add_task(self, plan_date: date, task_id: int, sequence_order: int | None = None) -> PlanTask:
        with self.session_factory() as session:
            plan = session.scalar(select(DailyPlan).where(DailyPlan.plan_date == plan_date))
            if plan is None:
                plan = DailyPlan(plan_date=plan_date)
                session.add(plan)
                session.flush()
            if sequence_order is None:
                current_max = session.scalar(
                    select(PlanTask.sequence_order).where(PlanTask.plan_id == plan.id).order_by(desc(PlanTask.sequence_order)).limit(1)
                )
                sequence_order = (current_max or -1) + 1
            link = PlanTask(plan_id=plan.id, task_id=task_id, sequence_order=sequence_order)
            session.add(link)
            session.commit()
            session.refresh(link)
            return link


class ActivityRepository(RepositoryBase):
    def add_observation(self, observation: ActivityObservation) -> ActivityEvent:
        with self.session_factory() as session:
            event = ActivityEvent(
                timestamp=observation.timestamp,
                application_name=observation.application_name,
                process_name=observation.process_name,
                window_title=observation.window_title,
                event_type=observation.event_type,
                metadata_json=json.dumps(observation.metadata, default=str),
            )
            session.add(event)
            session.commit()
            session.refresh(event)
            return event

    def add_file_activity(self, activity: FileActivity, store_file_path: bool = True) -> ActivityEvent:
        metadata = {"is_directory": activity.is_directory}
        if store_file_path:
            metadata["path"] = activity.path
        observation = ActivityObservation(
            timestamp=activity.timestamp,
            application_name="Filesystem",
            process_name="",
            window_title=None,
            event_type=activity.event_type,
            metadata=metadata,
        )
        return self.add_observation(observation)

    def recent(self, limit: int = 100) -> list[ActivityEvent]:
        with self.session_factory() as session:
            statement = select(ActivityEvent).order_by(desc(ActivityEvent.timestamp), desc(ActivityEvent.id)).limit(limit)
            return list(reversed(session.scalars(statement).all()))

    def latest(self) -> ActivityEvent | None:
        with self.session_factory() as session:
            return session.scalar(select(ActivityEvent).order_by(desc(ActivityEvent.timestamp), desc(ActivityEvent.id)).limit(1))


class SessionRepository(RepositoryBase):
    def create(self, started_at: datetime) -> WorkSession:
        with self.session_factory() as session:
            item = WorkSession(started_at=started_at)
            session.add(item)
            session.commit()
            session.refresh(item)
            return item

    def update(self, session_id: int, **changes: Any) -> WorkSession | None:
        with self.session_factory() as session:
            item = session.get(WorkSession, session_id)
            if item is None:
                return None
            for key, value in changes.items():
                if hasattr(item, key):
                    setattr(item, key, value)
            session.commit()
            session.refresh(item)
            return item

    def latest(self) -> WorkSession | None:
        with self.session_factory() as session:
            return session.scalar(select(WorkSession).order_by(desc(WorkSession.started_at)).limit(1))


class ContextRepository(RepositoryBase):
    def add(self, context: CurrentContext) -> ContextSnapshot:
        with self.session_factory() as session:
            snapshot = ContextSnapshot(
                timestamp=context.timestamp,
                active_application=context.active_application,
                active_window=context.active_window,
                project_context=context.project_context,
                current_task_id=context.current_task_id,
                last_activity=context.last_activity,
                summary=context.summary,
            )
            session.add(snapshot)
            session.commit()
            session.refresh(snapshot)
            return snapshot

    def latest(self) -> ContextSnapshot | None:
        with self.session_factory() as session:
            return session.scalar(select(ContextSnapshot).order_by(desc(ContextSnapshot.timestamp)).limit(1))


class WorkflowRepository(RepositoryBase):
    def upsert_pattern(self, name: str, applications: Iterable[str], confidence: float, count: int, event_type: str = "transition") -> Workflow:
        applications = list(applications)
        with self.session_factory() as session:
            workflow = session.scalar(select(Workflow).where(Workflow.name == name))
            if workflow is None:
                workflow = Workflow(name=name)
                session.add(workflow)
                session.flush()
            workflow.confidence = confidence
            workflow.occurrence_count = count
            workflow.last_seen = utc_now()
            workflow.steps.clear()
            workflow.steps.extend(
                WorkflowStep(step_order=index, application_name=app, event_type=event_type)
                for index, app in enumerate(applications)
            )
            session.commit()
            session.refresh(workflow)
            return workflow

    def list_recent(self, limit: int = 10) -> list[Workflow]:
        with self.session_factory() as session:
            statement = select(Workflow).options(selectinload(Workflow.steps)).order_by(desc(Workflow.last_seen)).limit(limit)
            return list(session.scalars(statement).all())


class PredictionRepository(RepositoryBase):
    def add(self, predicted_action: str, confidence: float, source_workflow: str | None) -> Prediction:
        with self.session_factory() as session:
            item = Prediction(
                predicted_action=predicted_action,
                confidence=confidence,
                source_workflow=source_workflow,
            )
            session.add(item)
            session.commit()
            session.refresh(item)
            return item


class PreferenceRepository(RepositoryBase):
    def get(self, key: str, default: str | None = None) -> str | None:
        with self.session_factory() as session:
            item = session.scalar(select(UserPreference).where(UserPreference.key == key))
            return item.value if item else default

    def set(self, key: str, value: str) -> UserPreference:
        with self.session_factory() as session:
            item = session.scalar(select(UserPreference).where(UserPreference.key == key))
            if item is None:
                item = UserPreference(key=key, value=value)
                session.add(item)
            else:
                item.value = value
                item.updated_at = utc_now()
            session.commit()
            session.refresh(item)
            return item
