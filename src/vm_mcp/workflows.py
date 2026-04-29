from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .service import VMService
from .proxmox import ProxmoxFileOps, ProxmoxGuestExec
from .models import CommandResult

@dataclass(slots=True)
class WorkflowManager:
    service: VMService
    file_ops: ProxmoxFileOps
    gexec: ProxmoxGuestExec
    
    async def run_generate_outputs(self, vmid: str, script_path: str, output_path: str) -> CommandResult:
        """Example workflow: upload script, run it, collect output."""
        # 1. Put script
        put_res = await self.file_ops.put(vmid, script_path, "/tmp/workflow_script.sh")
        if not put_res.ok:
            return put_res
        
        # 2. Run script
        exec_res = await self.gexec.exec(vmid, "bash /tmp/workflow_script.sh > /tmp/workflow_output.txt")
        if not exec_res.ok:
            return exec_res
        
        # 3. Get output
        return await self.file_ops.get(vmid, "/tmp/workflow_output.txt")

    async def run_eval_scorecard(self, vmid: str, data_path: str) -> dict[str, Any]:
        """Example workflow: evaluate a scorecard based on data in VM."""
        # This is a mock implementation of a high-level workflow
        res = await self.gexec.exec(vmid, f"cat {data_path}")
        score = len(res.stdout) % 100 # Mock score logic
        return {
            "ok": res.ok,
            "score": score,
            "vmid": vmid,
            "ts": datetime.now(tz=timezone.utc).isoformat()
        }

@dataclass(slots=True)
class ArtifactIndex:
    artifacts: dict[str, dict[str, Any]] = field(default_factory=dict)
    
    def add(self, name: str, vmid: str, path: str, size: int):
        self.artifacts[name] = {
            "vmid": vmid,
            "path": path,
            "size": size,
            "mtime": datetime.now(tz=timezone.utc).isoformat()
        }
    
    def list(self) -> dict[str, dict[str, Any]]:
        return self.artifacts
