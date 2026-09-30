# Doppel prototype architecture

Doppel is a local-first Windows desktop prototype. Its design keeps the
privacy boundary and the future local-AI boundary explicit, while using
deterministic logic for the current demo.

## Runtime flow

```text
Windows foreground window + optional selected folders
                    |
                    v
              monitoring layer
                    |
                    v
       activity/session repositories (SQLite)
                    |
        +-----------+-----------+
        v                       v
 context engine             workflow tracker
        |                       |
        v                       v
 context snapshots       transition statistics
        |                       |
        +-----------+-----------+
                    v
             rule-based prediction
                    |
                    v
        Dashboard / Activity / Memory / Planner
```

`ApplicationService` owns startup and shutdown ordering. It initializes the
database, creates repositories and domain services, starts the optional
filesystem observer, and receives foreground samples from the UI timer.

## Main modules

- `app/config`: conservative runtime defaults and local paths.
- `app/monitoring`: foreground process/window sampling, selected-folder file
  metadata, and inactivity-based sessions.
- `app/database`: SQLAlchemy models, SQLite engine setup, initialization, and
  repository operations.
- `app/context` and `app/memory`: current-work context and saved-session
  summaries.
- `app/workflow` and `app/prediction`: deterministic repeated-sequence and
  next-action baselines.
- `app/planner` and `app/resume`: task planning and explicit resume guidance.
- `app/ui`: the PySide6 desktop shell and prototype screens.
- `app/ai`: an intentionally small provider boundary reserved for future
  local inference.

## Persistence

The default database is `data/doppel.db`. The schema stores tasks, plans,
activity metadata, sessions, context snapshots, workflows, predictions, and
preferences. The prototype does not use a migration framework; startup creates
missing tables through `initialize_database`.

## Prototype boundaries

The current prediction and context behavior is rule-based and explainable. It
does not contain embeddings, an LLM, ONNX Runtime, QNN, Qualcomm AI Runtime,
or NPU execution. Resume preparation reports what could be resumed; it does
not launch arbitrary applications.
