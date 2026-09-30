"""Baseline deterministic context classification."""

from __future__ import annotations

import re

from app.context.context_models import ContextInput
from app.core.events import CurrentContext


class ContextBuilder:
    """Build human-readable context without an LLM or semantic model."""

    _PROJECT_HINTS = (".java", "java", "python", "javascript", "typescript", "project", "assignment", "src")

    def build(self, inputs: ContextInput) -> CurrentContext:
        project_context = self._infer_project(inputs.application_name, inputs.window_title)
        task_id = self._infer_task(project_context, inputs.open_tasks)
        app = inputs.application_name or "No active application"
        project = project_context or "General work"
        summary = f"Working in {app} · {project}"
        if task_id:
            task_title = next(title for item_id, title in inputs.open_tasks if item_id == task_id)
            summary = f"Working in {app} · {project} · {task_title}"
        return CurrentContext(
            timestamp=inputs.timestamp,
            active_application=inputs.application_name,
            active_window=inputs.window_title,
            project_context=project_context,
            current_task_id=task_id,
            last_activity=inputs.recent_activity,
            summary=summary,
        )

    def _infer_project(self, application_name: str | None, window_title: str | None) -> str | None:
        text = f"{application_name or ''} {window_title or ''}".strip()
        lowered = text.casefold()
        if "java" in lowered:
            return "Java assignment development"
        if any(term in lowered for term in ("python", "pycharm", "jupyter")):
            return "Python development"
        if any(term in lowered for term in ("visual studio", "vs code", "code")):
            project_name = self._title_project_name(window_title)
            return f"{project_name} development" if project_name else "Code development"
        if "terminal" in lowered or "powershell" in lowered:
            return "Development workflow"
        return None

    def _infer_task(self, project_context: str | None, open_tasks: tuple[tuple[int, str], ...]) -> int | None:
        if not open_tasks:
            return None
        if project_context:
            project_terms = set(re.findall(r"[a-z0-9]+", project_context.casefold()))
            for task_id, title in open_tasks:
                task_terms = set(re.findall(r"[a-z0-9]+", title.casefold()))
                if project_terms.intersection(task_terms):
                    return task_id
        return open_tasks[0][0]

    @staticmethod
    def _title_project_name(window_title: str | None) -> str | None:
        if not window_title:
            return None
        parts = [part.strip() for part in window_title.split(" - ") if part.strip()]
        return parts[-1] if parts else None

