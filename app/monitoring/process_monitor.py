"""Process discovery using psutil, without retaining command lines or arguments."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Iterable

import psutil

logger = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class ProcessInfo:
    """Minimal process information needed to label an active window."""

    pid: int
    name: str


class ProcessMonitor:
    """Enumerate running processes and resolve a PID to a display-safe name."""

    def list_processes(self) -> list[ProcessInfo]:
        processes: list[ProcessInfo] = []
        for process in psutil.process_iter(attrs=("pid", "name")):
            try:
                info = process.info
                name = str(info.get("name") or "unknown")
                processes.append(ProcessInfo(pid=int(info["pid"]), name=name))
            except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError, ValueError):
                continue
        return processes

    def name_for_pid(self, pid: int) -> str:
        try:
            return psutil.Process(pid).name()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return "unknown"

    def relevant_processes(self, names: Iterable[str]) -> list[ProcessInfo]:
        wanted = {name.casefold() for name in names}
        return [process for process in self.list_processes() if process.name.casefold() in wanted]

