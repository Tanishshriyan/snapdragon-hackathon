"""Application orchestration without UI-framework dependencies."""

from __future__ import annotations

from datetime import date, datetime
import logging
from pathlib import Path

from app.config.settings import Settings
from app.context.context_engine import ContextEngine
from app.core.events import ActivityObservation, FileActivity
from app.core.logging_config import configure_logging
from app.database.engine import create_database_engine, create_session_factory
from app.database.migrations import initialize_database
from app.database.repositories import (
    ActivityRepository,
    ContextRepository,
    PlanRepository,
    PredictionRepository,
    PreferenceRepository,
    SessionRepository,
    TaskRepository,
    WorkflowRepository,
)
from app.ai.local_reasoning import build_reasoner
from app.memory.embeddings import EmbeddingConfig, LocalTextEmbedder
from app.memory.semantic_memory import SemanticMemory
from app.memory.semantic_repository import SemanticMemoryRepository
from app.resume.launcher import LaunchTarget, WorkspaceLauncher
from app.workflow.learned_model import LearnedWorkflowModel
from app.memory.memory_manager import MemoryManager
from app.memory.session_memory import SessionMemoryStore
from app.monitoring.filesystem_monitor import FilesystemMonitor
from app.monitoring.process_monitor import ProcessMonitor
from app.monitoring.session_monitor import SessionMonitor
from app.monitoring.window_monitor import WindowMonitor
from app.planner.plan_manager import PlanManager
from app.planner.task_manager import TaskManager
from app.prediction.prediction_engine import PredictionEngine
from app.resume.resume_engine import ResumeEngine
from app.workflow.workflow_tracker import WorkflowTracker

logger = logging.getLogger(__name__)


class ApplicationService:
    """Own application components and define their startup/shutdown order."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.settings.ensure_directories()
        configure_logging(self.settings.log_directory)
        self.engine = create_database_engine(self.settings.database_path)
        initialize_database(self.engine)
        self.session_factory = create_session_factory(self.engine)

        self.task_repository = TaskRepository(self.session_factory)
        self.plan_repository = PlanRepository(self.session_factory)
        self.semantic_memory = SemanticMemory(
            SemanticMemoryRepository(self.session_factory),
            LocalTextEmbedder(EmbeddingConfig(self.settings.embedding_dimensions)),
        )
        self.reasoner = build_reasoner(self.settings.local_model_path)
        self.learned_workflow_model = LearnedWorkflowModel()
        targets = [
            LaunchTarget(name, values[0], tuple(values[1:]))
            for name, values in self.settings.launchable_applications.items()
            if values
        ]
        self.workspace_launcher = WorkspaceLauncher(targets)
        self.activity_repository = ActivityRepository(self.session_factory)
        self.session_repository = SessionRepository(self.session_factory)
        self.context_repository = ContextRepository(self.session_factory)
        self.workflow_repository = WorkflowRepository(self.session_factory)
        self.prediction_repository = PredictionRepository(self.session_factory)
        self.preference_repository = PreferenceRepository(self.session_factory)

        self.task_manager = TaskManager(self.task_repository)
        self.plan_manager = PlanManager(self.plan_repository, self.task_repository)
        self.context_engine = ContextEngine(
            self.activity_repository,
            self.context_repository,
            self.task_repository,
        )
        self.session_monitor = SessionMonitor(
            self.session_repository,
            self.settings.inactivity_timeout_seconds,
        )
        self.session_monitor.set_on_closed(self._on_session_closed)
        self.workflow_tracker = WorkflowTracker(self.activity_repository, self.workflow_repository)
        self.prediction_engine = PredictionEngine(self.activity_repository, self.prediction_repository)
        self.memory_manager = MemoryManager(self.context_engine, SessionMemoryStore(self.session_repository))
        self.resume_engine = ResumeEngine(self.memory_manager.session_memory)

        self.process_monitor = ProcessMonitor()
        self.window_monitor = WindowMonitor(
            self.process_monitor,
            store_window_titles=self.settings.store_window_titles,
        )
        self.filesystem_monitor = FilesystemMonitor(
            self.settings.monitored_directories,
            self.record_file_activity,
            store_file_paths=self.settings.store_file_paths,
        )
        self._monitoring = False

    @property
    def is_monitoring(self) -> bool:
        return self._monitoring

    def start_monitoring(self) -> None:
        if self._monitoring:
            return
        try:
            self.filesystem_monitor.start()
        except Exception:
            logger.exception("Filesystem monitor could not start; continuing with foreground monitoring")
        self._monitoring = True
        logger.info("Doppel monitoring started")

    def poll(self, now: datetime | None = None) -> None:
        """Poll one foreground sample; the UI invokes this from a QTimer."""

        if not self._monitoring:
            return
        observation = self.window_monitor.poll(now)
        if observation:
            self.record_observation(observation)
        self.session_monitor.tick(now)
        self.learned_workflow_model.fit(self.activity_repository.recent(500))

    def record_observation(self, observation: ActivityObservation) -> None:
        self.activity_repository.add_observation(observation)
        self.session_monitor.record_observation(observation)
        self.context_engine.refresh(observation.timestamp)
        self.workflow_tracker.refresh()

    def record_file_activity(self, activity: FileActivity) -> None:
        self.activity_repository.add_file_activity(activity, self.settings.store_file_paths)
        self.session_monitor.record_observation(activity)
        self.context_engine.refresh(activity.timestamp)

    def current_prediction(self) -> object | None:
        context = self.context_engine.current or self.context_engine.refresh(persist=False)
        if not self.settings.prediction_enabled:
            return None
        return self.prediction_engine.predict(context.active_application)

    def latest_plan(self, plan_date: date | None = None) -> object | None:
        return self.plan_manager.plan_for(plan_date or date.today())

    def set_monitored_directories(self, directories: list[str | Path]) -> None:
        """Apply a new folder scope, restarting the observer if needed."""

        was_running = self._monitoring
        if was_running:
            self.filesystem_monitor.stop()
        self.settings.with_monitored_directories(directories)
        self.filesystem_monitor = FilesystemMonitor(
            self.settings.monitored_directories,
            self.record_file_activity,
            store_file_paths=self.settings.store_file_paths,
        )
        if was_running:
            try:
                self.filesystem_monitor.start()
            except Exception:
                logger.exception("Updated filesystem monitor could not start")

    def resume_context(self) -> object:
        current = self.context_engine.current
        task_title = None
        if current and current.current_task_id:
            task = self.task_repository.get(current.current_task_id)
            task_title = task.title if task else None
        return self.resume_engine.load_resume_context(task_title)

    def remember_memory(
        self,
        text: str,
        memory_type: str = "note",
        metadata: dict[str, object] | None = None,
    ) -> object:
        return self.semantic_memory.remember(text, memory_type, metadata or {})

    def search_memory(self, query: str, limit: int = 5) -> list:
        return self.semantic_memory.search(query, limit=limit)

    def explain_current_context(self) -> object:
        context = self.context_engine.current or self.context_engine.refresh(persist=False)
        memories = [hit.memory.text for hit in self.semantic_memory.search(context.summary, limit=3)]
        return self.reasoner.explain(context, memories)

    def register_launch_target(self, target: LaunchTarget) -> None:
        self.workspace_launcher.register(target)

    def prepare_workspace(self, launch: bool = False, dry_run: bool = False) -> object:
        context = self.resume_context()
        preparation = self.resume_engine.prepare_workspace(context)
        if not launch or context.session is None:
            return preparation
        application = context.session.primary_application
        if not application:
            return preparation
    def shutdown(self) -> None:
        """Stop observers, close active session, and release SQLite resources."""

        if not self._monitoring:
            self.engine.dispose()
            return
        self._monitoring = False
        self.filesystem_monitor.stop()
        self.session_monitor.close()
        self.engine.dispose()
        logger.info("Doppel monitoring stopped")

    def _on_session_closed(self, session: object) -> None:
        current = self.context_engine.current
        if current:
            session_id = getattr(session, "id", None)
            if session_id:
                self.session_repository.update(session_id, project_context=current.project_context)


def build_application_service(settings: Settings | None = None) -> ApplicationService:
    """Construct a fully initialized service graph."""

    return ApplicationService(settings or Settings.from_environment())
