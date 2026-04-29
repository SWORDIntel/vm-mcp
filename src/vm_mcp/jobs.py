from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from typing import Any

from .models import CommandResult
from .runner import CommandRunner


@dataclass(slots=True)
class JobState:
    job_id: str
    vmid: str
    cmd: str
    status: str
    result: CommandResult | None = None


class JobManager:
    def __init__(self, runner: CommandRunner | None = None) -> None:
        self.runner = runner or CommandRunner()
        self._jobs: dict[str, JobState] = {}
        self._tasks: dict[str, asyncio.Task[CommandResult]] = {}

    def job_start(self, vmid: str, cmd: str) -> str:
        job_id = str(uuid.uuid4())
        self._jobs[job_id] = JobState(job_id=job_id, vmid=vmid, cmd=cmd, status="running")
        task = asyncio.create_task(self.runner.run(vmid=vmid, cmd=cmd))
        self._tasks[job_id] = task
        task.add_done_callback(lambda t, j=job_id: self._finalize(j, t))
        return job_id

    def _finalize(self, job_id: str, task: asyncio.Task[CommandResult]) -> None:
        state = self._jobs[job_id]
        if task.cancelled():
            state.status = "cancelled"
            return
        state.result = task.result()
        state.status = "completed"

    def job_status(self, job_id: str) -> dict[str, Any]:
        state = self._jobs[job_id]
        return {
            "job_id": state.job_id,
            "vmid": state.vmid,
            "cmd": state.cmd,
            "status": state.status,
            "result": state.result.to_dict() if state.result else None,
        }

    def job_cancel(self, job_id: str) -> bool:
        task = self._tasks[job_id]
        if task.done():
            return False
        task.cancel()
        self._jobs[job_id].status = "cancelled"
        return True
