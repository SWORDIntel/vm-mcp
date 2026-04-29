from __future__ import annotations

from dataclasses import dataclass

from .runner import CommandRunner


@dataclass(slots=True)
class ProxmoxLifecycle:
    runner: CommandRunner

    async def status(self, vmid: str):
        return await self.runner.run(vmid=vmid, cmd=f"qm status {vmid}")

    async def start(self, vmid: str):
        return await self.runner.run(vmid=vmid, cmd=f"qm start {vmid}")

    async def stop(self, vmid: str):
        return await self.runner.run(vmid=vmid, cmd=f"qm stop {vmid}")

    async def reboot(self, vmid: str):
        return await self.runner.run(vmid=vmid, cmd=f"qm reboot {vmid}")


@dataclass(slots=True)
class ProxmoxSnapshot:
    runner: CommandRunner

    async def list(self, vmid: str):
        return await self.runner.run(vmid=vmid, cmd=f"qm listsnapshot {vmid}")

    async def create(self, vmid: str, name: str):
        return await self.runner.run(vmid=vmid, cmd=f"qm snapshot {vmid} {name}")
