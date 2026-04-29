from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass

from .models import CommandResult


@dataclass(slots=True)
class RunnerConfig:
    timeout_s: float = 30.0
    retries: int = 1


class CommandRunner:
    def __init__(self, config: RunnerConfig | None = None) -> None:
        self.config = config or RunnerConfig()

    async def run(self, vmid: str, cmd: str, timeout_s: float | None = None, retries: int | None = None) -> CommandResult:
        timeout = timeout_s if timeout_s is not None else self.config.timeout_s
        max_retries = retries if retries is not None else self.config.retries

        last_err = ""
        start = time.monotonic()
        for attempt in range(max_retries + 1):
            try:
                proc = await asyncio.create_subprocess_shell(
                    cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=timeout)
                duration_ms = int((time.monotonic() - start) * 1000)
                code = proc.returncode or 0
                return CommandResult(
                    ok=(code == 0),
                    code=code,
                    stdout=stdout_b.decode(),
                    stderr=stderr_b.decode(),
                    duration_ms=duration_ms,
                    vmid=vmid,
                    cmd=cmd,
                )
            except TimeoutError:
                last_err = f"timeout after {timeout}s"
            except Exception as exc:  # noqa: BLE001
                last_err = str(exc)

            if attempt < max_retries:
                await asyncio.sleep(0.2 * (attempt + 1))

        duration_ms = int((time.monotonic() - start) * 1000)
        return CommandResult(
            ok=False,
            code=124,
            stdout="",
            stderr=last_err,
            duration_ms=duration_ms,
            vmid=vmid,
            cmd=cmd,
        )
