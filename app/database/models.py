"""Normalized SQLite models for planning, memory, and safe activity metadata."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.core.time import utc_now


class Base(DeclarativeBase):
    """Declarative base for all Doppel tables."""


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    value: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(240))
    description: Mapped[str] = mapped_column(Text, default="")
    priority: Mapped[str] = mapped_column(String(20), default="medium", index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    scheduled_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    scheduled_time: Mapped[str | None] = mapped_column(String(10), nullable=True)
    estimated_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    plan_links: Mapped[list["PlanTask"]] = relationship(back_populates="task", cascade="all, delete-orphan")


class DailyPlan(Base):
    __tablename__ = "daily_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_date: Mapped[date] = mapped_column(Date, unique=True, index=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    tasks: Mapped[list["PlanTask"]] = relationship(
        back_populates="plan", cascade="all, delete-orphan", order_by="PlanTask.sequence_order"
    )


class PlanTask(Base):
    __tablename__ = "plan_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("daily_plans.id", ondelete="CASCADE"), index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), index=True)
    sequence_order: Mapped[int] = mapped_column(Integer, default=0)
    plan: Mapped[DailyPlan] = relationship(back_populates="tasks")
    task: Mapped[Task] = relationship(back_populates="plan_links")


class ActivityEvent(Base):
    __tablename__ = "activity_events"
    __table_args__ = (
        Index("ix_activity_timestamp_application", "timestamp", "application_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)
    application_name: Mapped[str] = mapped_column(String(160), index=True)
    process_name: Mapped[str] = mapped_column(String(160), default="")
    window_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    event_type: Mapped[str] = mapped_column(String(60), index=True)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")


class WorkSession(Base):
    __tablename__ = "work_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    primary_application: Mapped[str | None] = mapped_column(String(160), nullable=True)
    project_context: Mapped[str | None] = mapped_column(String(240), nullable=True)
    summary: Mapped[str] = mapped_column(Text, default="")
    last_state: Mapped[str] = mapped_column(Text, default="{}")


class Workflow(Base):
    __tablename__ = "workflows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(300), unique=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    occurrence_count: Mapped[int] = mapped_column(Integer, default=0)
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)
    steps: Mapped[list["WorkflowStep"]] = relationship(
        back_populates="workflow", cascade="all, delete-orphan", order_by="WorkflowStep.step_order"
    )


class WorkflowStep(Base):
    __tablename__ = "workflow_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workflow_id: Mapped[int] = mapped_column(ForeignKey("workflows.id", ondelete="CASCADE"), index=True)
    step_order: Mapped[int] = mapped_column(Integer)
    application_name: Mapped[str] = mapped_column(String(160))
    event_type: Mapped[str] = mapped_column(String(60))
    expected_duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    workflow: Mapped[Workflow] = relationship(back_populates="steps")


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)
    predicted_action: Mapped[str] = mapped_column(String(240))
    confidence: Mapped[float] = mapped_column(Float)
    source_workflow: Mapped[str | None] = mapped_column(String(300), nullable=True)
    accepted: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    rejected: Mapped[bool | None] = mapped_column(Boolean, nullable=True)


class ContextSnapshot(Base):
    __tablename__ = "context_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)
    active_application: Mapped[str | None] = mapped_column(String(160), nullable=True)
    active_window: Mapped[str | None] = mapped_column(String(500), nullable=True)
    project_context: Mapped[str | None] = mapped_column(String(240), nullable=True)
    current_task_id: Mapped[int | None] = mapped_column(ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)
    last_activity: Mapped[str | None] = mapped_column(String(300), nullable=True)
    summary: Mapped[str] = mapped_column(Text, default="")
    current_task: Mapped[Task | None] = relationship()
