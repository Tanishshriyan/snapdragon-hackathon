# Doppel development guide

## First run on Windows

From the project root in PowerShell:

```powershell
.\scripts\setup.ps1
.\scripts\run.ps1
```

The setup script validates Python 3.11+, creates `.venv`, installs the runtime
and development requirements, creates the local data directories, and
initializes the SQLite schema. To only prepare the environment without
installing packages again:

```powershell
.\scripts\setup.ps1 -SkipInstall
```

For a pre-existing environment, `python -m app.main` runs the desktop app and
`python -m pytest -q` runs the test suite.

## Verification checklist

1. Run `python -m pytest -q`.
2. Run `python -c "import PySide6; from app.ui.main_window import MainWindow; print('ui imports ok')"`.
3. Start the app and confirm the dashboard opens.
4. Add and complete a task in Planner.
5. Choose a test folder in Settings and confirm Activity shows metadata only.
6. Close the window and confirm the process exits cleanly.

The UI can be smoke-tested without a visible desktop session by setting
`QT_QPA_PLATFORM=offscreen`, although real foreground-window monitoring still
requires Windows desktop APIs.

## Working conventions

- Keep prototype behavior deterministic and easy to demonstrate.
- Preserve the privacy boundary when adding monitors or repository fields.
- Keep UI code thin; put domain behavior in services and managers.
- Add or update a focused test when changing persistence or prediction logic.
- Do not describe future AI/NPU work as implemented until it is integrated and
  measured.

## Known prototype limits

PySide6 is required to launch the desktop UI. Windows-specific monitoring is
best-effort and may be unavailable in non-Windows environments. There is no
semantic memory, local model, automatic application restoration, benchmark
suite, or production-grade migration/security layer yet.
