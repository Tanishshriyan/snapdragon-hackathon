# Doppel

## Your Personal AI Work Twin

Doppel is a privacy-first, local-first Windows desktop application that helps a
user plan work, remember unfinished context, observe safe high-level activity,
learn recurring application workflows, predict a likely next action, and resume
work without starting from zero.

## Current progress

Phase 1 is substantially implemented. The codebase currently contains the
foundation for:

`PLAN → OBSERVE → REMEMBER → LEARN BASIC PATTERNS → PREDICT → RESUME`

The project is intentionally a runnable hackathon prototype. The current
handoff includes local setup/run scripts and architecture, privacy, and
development notes; it does not claim production readiness or Snapdragon/NPU
integration.

### Completed so far

- Clean modular Python package structure under `app/`.
- Python 3.11+ project configuration in `pyproject.toml`.
- Dependency manifests in `requirements.txt` and `requirements-dev.txt`.
- SQLite database setup through SQLAlchemy.
- Database models for tasks, daily plans, preferences, activity events,
  sessions, workflows, predictions, and context snapshots.
- Repository layer with CRUD operations for the main entities.
- Windows foreground-window monitoring using `pywin32`.
- Process discovery using `psutil`.
- Optional selected-folder monitoring using `watchdog`.
- Privacy boundary that avoids keystrokes, passwords, clipboard contents,
  screenshots, and file contents.
- Inactivity-based session tracking.
- Deterministic context engine and context snapshots.
- Task creation, editing, completion, deletion, scheduling, priority, and
  estimated duration support.
- Daily plan and Tomorrow's Plan support.
- Deterministic workflow sequence detection.
- Transition statistics based on actual observed application history.
- Rule-based next-action prediction with frequency-derived confidence.
- Session memory and Continue Where You Left Off support.
- Explicit workspace preparation response without automatically launching apps.
- Future `AIProvider` / `LocalInferenceProvider` abstraction.
- PySide6 UI modules for Dashboard, Planner, Activity, Memory, and Settings.
- Application lifecycle service with monitoring start, polling, and clean
  shutdown behavior.
- Seven automated tests covering database, planner, context, monitoring
  lifecycle, sessions, workflows, and prediction.

### Verification completed

The core service, desktop shell, and setup handoff were verified in the current
environment:

```text
7 passed
PySide6 and app.main import successfully
offscreen smoke exit 0
Setup complete. Run .\scripts\run.ps1 to start Doppel.
PowerShell scripts parse successfully
```

The offscreen desktop smoke test instantiated the real `MainWindow`, started
the monitoring lifecycle, and closed the application through Qt without
hanging. The functional service tests cover database CRUD, planning,
context, monitoring lifecycle, sessions, workflows, and prediction.

## Runnable handoff

On Windows, from the project root:

```powershell
.\scripts\setup.ps1
.\scripts\run.ps1
```

Use `.\scripts\setup.ps1 -SkipInstall` when the virtual environment already
has the dependencies. The setup script validates Python 3.11+, initializes
the local SQLite schema, and creates the application-owned data directories.

For development verification:

```powershell
python -m pytest -q
python -c "import PySide6; import app.main; print('UI imports ok')"
```

## What is not implemented yet

- Local embeddings or semantic memory.
- Local SLM/LLM reasoning.
- ONNX Runtime integration.
- QNN or Qualcomm AI Runtime integration.
- Snapdragon NPU execution.
- CPU versus NPU benchmarks, latency measurements, resource measurements, or
  power-efficiency claims.
- Automatic launching or restoration of arbitrary applications.
- Advanced machine-learning workflow models.
- Cloud APIs or cloud synchronization.

The current context, workflow, and prediction logic is explicitly a
deterministic/rule-based baseline. It does not make AI or Snapdragon
acceleration claims.

## Privacy

Doppel is local-first. The baseline does not require a cloud service and does
not log keystrokes, store passwords, read clipboard contents, capture
continuous screenshots, or store file contents. Filesystem monitoring is
limited to directories selected by the user and records high-level metadata
only.

## Installation and running

The intended Windows workflow is:

```powershell
.\scripts\setup.ps1
.\scripts\run.ps1
```

For direct development runs after dependencies are installed:

```powershell
python -m app.main
python -m pytest -q
```

The local SQLite database will be stored at `data/doppel.db`, and application
logs will be stored under `data/logs/`.

For development details, verification steps, and the prototype limitations,
see [docs/development.md](docs/development.md), [docs/architecture.md](docs/architecture.md),
and [docs/privacy.md](docs/privacy.md).

## Project structure

```text
app/
├── ai/             Future local inference boundary
├── config/         Runtime settings and privacy defaults
├── context/        Deterministic current-work context
├── core/           Events, exceptions, logging, and time helpers
├── database/       SQLAlchemy models, engine, migrations, repositories
├── memory/         Session and context memory
├── monitoring/     Process, foreground-window, filesystem, and session monitors
├── planner/        Task and daily-plan services
├── prediction/     Rule-based next-action prediction
├── resume/         Resume context and workspace preparation
├── services/       Application lifecycle orchestration
├── ui/             PySide6 screens and reusable widgets
└── workflow/       Transition and repeated-sequence analysis
tests/              Unit and integration tests
docs/               Architecture, privacy, and development documentation
scripts/            Windows setup and run scripts
```

## Roadmap

### Phase 1 — Doppel Base

Planner, activity monitoring, context, memory, workflow learning, baseline
prediction, and resume behavior.

### Phase 2 — Intelligence

Local embeddings, semantic memory, better workflow modeling, and a local
small/large language model.

### Phase 3 — Snapdragon

ONNX Runtime, QNN, Qualcomm AI Runtime, and Snapdragon NPU execution after a
real, testable runtime is available.

### Phase 4 — Optimization

Measured CPU versus NPU latency, resource usage, and power-efficiency analysis.

### Phase 5 — Competition polish

UI refinement, demo flow, benchmark methodology, presentation, and final
documentation.

## Handoff scope

Implemented in this prototype: local planning and task completion, daily and
tomorrow plans, high-level Windows activity monitoring, selected-folder
metadata monitoring, inactivity-based sessions, deterministic context and
workflow detection, frequency-based next-action prediction, saved session
memory, explicit resume guidance, privacy settings, SQLite persistence, and a
PySide6 desktop shell.

Not implemented: semantic embeddings, local SLM/LLM reasoning, ONNX/QNN or
Qualcomm AI Runtime integration, Snapdragon NPU execution, measured CPU/NPU
benchmarks, automatic application launching/restoration, advanced learned
workflow models, cloud APIs, and cloud synchronization.
