from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path

from .models import CommandResult
from .runner import CommandRunner


@dataclass(slots=True)
class ProxmoxLifecycle:
    runner: CommandRunner

    async def status(self, vmid: str) -> CommandResult:
        return await self.runner.run(vmid=vmid, cmd=f"qm status {vmid}")

    async def start(self, vmid: str) -> CommandResult:
        return await self.runner.run(vmid=vmid, cmd=f"qm start {vmid}")

    async def stop(self, vmid: str) -> CommandResult:
        return await self.runner.run(vmid=vmid, cmd=f"qm stop {vmid}")

    async def reboot(self, vmid: str) -> CommandResult:
        return await self.runner.run(vmid=vmid, cmd=f"qm reboot {vmid}")


@dataclass(slots=True)
class ProxmoxSnapshot:
    runner: CommandRunner

    async def list(self, vmid: str) -> CommandResult:
        return await self.runner.run(vmid=vmid, cmd=f"qm listsnapshot {vmid}")

    async def create(self, vmid: str, name: str) -> CommandResult:
        return await self.runner.run(vmid=vmid, cmd=f"qm snapshot {vmid} {name}")

    async def rollback(self, vmid: str, name: str) -> CommandResult:
        return await self.runner.run(vmid=vmid, cmd=f"qm rollback {vmid} {name}")

    async def delete(self, vmid: str, name: str) -> CommandResult:
        return await self.runner.run(vmid=vmid, cmd=f"qm delsnapshot {vmid} {name}")


@dataclass(slots=True)
class ProxmoxFileOps:
    runner: CommandRunner

    async def put(self, vmid: str, local_path: str, remote_path: str) -> CommandResult:
        """Upload a file to the guest using qm guest file write."""
        path = Path(local_path)
        if not path.exists():
            return CommandResult(
                ok=False, code=1, stdout="", stderr=f"Local file not found: {local_path}", 
                duration_ms=0, vmid=vmid, cmd=f"put {local_path}"
            )
        
        cmd = f"qm guest file write {vmid} {remote_path} {local_path}"
        return await self.runner.run(vmid=vmid, cmd=cmd)

    async def get(self, vmid: str, remote_path: str) -> CommandResult:
        """Read a file from the guest using qm guest file read."""
        cmd = f"qm guest file read {vmid} {remote_path}"
        return await self.runner.run(vmid=vmid, cmd=cmd)


@dataclass(slots=True)
class ProxmoxGuestExec:
    runner: CommandRunner

    async def exec(self, vmid: str, cmd: str, cwd: str | None = None, env: dict[str, str] | None = None, timeout: int | None = None) -> CommandResult:
        args = []
        if cwd:
            args.append(f"--cwd {cwd}")
        if env:
            for k, v in env.items():
                args.append(f"--env {k}={v}")
        if timeout:
            args.append(f"--timeout {timeout}")
        
        flags = " ".join(args)
        full_cmd = f"qm guest exec {vmid} {flags} -- {cmd}"
        return await self.runner.run(vmid=vmid, cmd=full_cmd)

    async def probe(self, vmid: str) -> CommandResult:
        return await self.runner.run(vmid=vmid, cmd=f"qm guest agent {vmid} ping")


@dataclass(slots=True)
class ProxmoxConfig:
    runner: CommandRunner

    async def get(self, vmid: str) -> CommandResult:
        return await self.runner.run(vmid=vmid, cmd=f"qm config {vmid}")

    async def set(self, vmid: str, params: dict[str, str]) -> CommandResult:
        items = [f"-{k} {v}" for k, v in params.items()]
        cmd = f"qm set {vmid} {' '.join(items)}"
        return await self.runner.run(vmid=vmid, cmd=cmd)
