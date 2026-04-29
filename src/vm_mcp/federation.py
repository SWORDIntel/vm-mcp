from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from .service import VMService
from .models import CommandResult

@dataclass(slots=True)
class FederationManager:
    service: VMService
    
    async def fan_out_exec(self, vmids: list[str], cmd: str) -> dict[str, CommandResult]:
        """Execute a command on multiple VMs in parallel."""
        tasks = [self.service.exec(vmid=vmid, cmd=cmd) for vmid in vmids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        output = {}
        for vmid, res in zip(vmids, results):
            if isinstance(res, Exception):
                output[vmid] = CommandResult(
                    ok=False, code=500, stdout="", stderr=str(res), 
                    duration_ms=0, vmid=vmid, cmd=cmd
                )
            else:
                output[vmid] = res
        return output

    async def cross_vm_dependency_exec(self, plan: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Execute a sequence of commands across different VMs.
        Example plan: [{"vmid": "100", "cmd": "ls"}, {"vmid": "101", "cmd": "ps"}]
        """
        results = []
        for step in plan:
            vmid = step["vmid"]
            cmd = step["cmd"]
            res = await self.service.exec(vmid=vmid, cmd=cmd)
            results.append({"step": step, "result": res.to_dict()})
            if not res.ok:
                break # Stop on failure
        return results
