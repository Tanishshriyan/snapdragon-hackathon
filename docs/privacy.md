# Doppel prototype privacy boundary

Doppel is designed to keep the prototype's observations local and small. The
default storage is a SQLite file and a local log directory under `data/`.

## Collected metadata

When monitoring is running, Doppel may record:

- the foreground application/process name;
- a window title when that setting is enabled;
- timestamps and high-level activity kind;
- high-level metadata for filesystem events in folders explicitly selected by
  the user;
- inactivity-based session start/end times and summaries;
- task, workflow, prediction, and preference records created in the app.

## Explicitly excluded

The prototype does not collect or store:

- keystrokes or mouse input;
- passwords or credentials;
- clipboard contents;
- continuous screenshots;
- file contents;
- cloud copies or cloud synchronization.

File monitoring is opt-in and limited to selected directories. The `store_file_paths`
setting controls whether paths are retained; file contents are never read.
The `automatic_workspace_preparation` default is false, and the resume action
only presents an explicit preparation message.

## Practical limitations

This is a hackathon prototype, not a security product. Users should review the
selected-folder scope and local database/log permissions on a shared Windows
machine. The app currently assumes a trusted local account and does not offer
encryption, multi-user access control, or a formal data-retention manager.
