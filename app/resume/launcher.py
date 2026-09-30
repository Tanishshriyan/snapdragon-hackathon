"""Explicit, allowlisted application launching for resume demos."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import subprocess
from typing import Sequence


@dataclass(frozen=True, slots=True)
class LaunchTarget:
    name: str
    executable: str
    arguments: tuple[str, ...] = ()
    working_directory: str | None = None


@dataclass(frozen=True, slots=True)
class LaunchResult:
    name: str
    started: bool
    message: str


class WorkspaceLauncher:
    """Only launches applications explicitly registered by the user/demo."""

    def __init__(self, targets: Sequence[LaunchTarget] = ()) -> None:
        self._targets = {target.name.casefold(): target for target in targets}

    def register(self, target: LaunchTarget) -> None:
        self._targets[target.name.casefold()] = target

    def targets(self) -> tuple[LaunchTarget, ...]:
        return tuple(self._targets.values())

    def prepare(self, application_names: Sequence[str]) -> list[LaunchTarget]:
        return [self._targets[name.casefold()] for name in application_names if name.casefold() in self._targets]

    def launch(self, target: LaunchTarget, dry_run: bool = False) -> LaunchResult:
        executable = target.executable
        if not os.path.isabs(executable):
            executable = shutil.which(executable) or executable
        if not dry_run and os.path.isabs(executable) and not Path(executable).exists():
            return LaunchResult(target.name, False, f"Executable not found: {executable}")
        command = [executable, *target.arguments]
        if dry_run:
            return LaunchResult(target.name, True, "Dry run: " + " ".join(command))
        try:
            subprocess.Popen(command, cwd=target.working_directory or None, shell=False)
        except OSError as error:
            return LaunchResult(target.name, False, f"Could not start {target.name}: {error}")
        return LaunchResult(target.name, True, f"Started {target.name}")

    def launch_names(self, application_names: Sequence[str], dry_run: bool = False) -> list[LaunchResult]:
        targets = self.prepare(application_names)
        results = [self.launch(target, dry_run=dry_run) for target in targets]
        missing = [name for name in application_names if name.casefold() not in self._targets]
        results.extend(LaunchResult(name, False, "Not registered in the workspace allowlist") for name in missing)
        return results
