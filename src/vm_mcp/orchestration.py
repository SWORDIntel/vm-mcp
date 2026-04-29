from __future__ import annotations

from dataclasses import dataclass
from .runner import CommandRunner
from .models import CommandResult

@dataclass(slots=True)
class VMServiceManager:
    runner: CommandRunner

    async def status(self, vmid: str, service: str) -> CommandResult:
        return await self.runner.run(vmid=vmid, cmd=f"systemctl is-active {service}")

    async def enable(self, vmid: str, service: str) -> CommandResult:
        return await self.runner.run(vmid=vmid, cmd=f"systemctl enable {service}")

    async def disable(self, vmid: str, service: str) -> CommandResult:
        return await self.runner.run(vmid=vmid, cmd=f"systemctl disable {service}")

    async def journal_tail(self, vmid: str, service: str, lines: int = 50) -> CommandResult:
        return await self.runner.run(vmid=vmid, cmd=f"journalctl -u {service} -n {lines} --no-pager")


@dataclass(slots=True)
class VMContainerManager:
    runner: CommandRunner

    async def ps(self, vmid: str) -> CommandResult:
        return await self.runner.run(vmid=vmid, cmd="docker ps --format '{{.ID}}\t{{.Names}}\t{{.Status}}'")

    async def logs(self, vmid: str, container: str, lines: int = 50) -> CommandResult:
        return await self.runner.run(vmid=vmid, cmd=f"docker logs --tail {lines} {container}")

    async def restart(self, vmid: str, container: str) -> CommandResult:
        return await self.runner.run(vmid=vmid, cmd=f"docker restart {container}")

    async def compose_up(self, vmid: str, path: str) -> CommandResult:
        return await self.runner.run(vmid=vmid, cmd=f"docker-compose -f {path} up -d")
