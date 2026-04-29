from __future__ import annotations

import asyncio
import json
import os
from typing import Any

from fastmcp import FastMCP

from .service import VMService
from .proxmox import ProxmoxLifecycle, ProxmoxSnapshot, ProxmoxFileOps, ProxmoxGuestExec, ProxmoxConfig
from .orchestration import VMServiceManager, VMContainerManager
from .workflows import WorkflowManager, ArtifactIndex
from .federation import FederationManager
from .models import CommandResult

# Initialize FastMCP
mcp = FastMCP("vm-mcp")

# Build the internal service
service = VMService.build(audit_path=os.getenv("VM_MCP_AUDIT_LOG", "logs/audit.log"))
proxmox = ProxmoxLifecycle(runner=service.runner)
snapshot = ProxmoxSnapshot(runner=service.runner)
file_ops = ProxmoxFileOps(runner=service.runner)
svc_mgr = VMServiceManager(runner=service.runner)
container_mgr = VMContainerManager(runner=service.runner)
proxmox_config = ProxmoxConfig(runner=service.runner)
gexec = ProxmoxGuestExec(runner=service.runner)
workflow_mgr = WorkflowManager(service=service, file_ops=file_ops, gexec=gexec)
artifact_idx = ArtifactIndex()
federation = FederationManager(service=service)

@mcp.tool()
async def vm_fan_out(vmids: list[str], cmd: str) -> dict[str, Any]:
    """Execute a command on multiple VMs in parallel."""
    results = await federation.fan_out_exec(vmids, cmd)
    return {vmid: res.to_dict() for vmid, res in results.items()}

@mcp.tool()
async def vm_orchestrate(plan: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Execute a sequence of commands across different VMs (dependency graph)."""
    return await federation.cross_vm_dependency_exec(plan)

@mcp.tool()
async def run_workflow_generate(vmid: str, script_path: str) -> dict[str, Any]:
    """Run a generation workflow: upload script, execute, and return results."""
    result = await workflow_mgr.run_generate_outputs(vmid, script_path, "")
    return result.to_dict()

@mcp.tool()
async def run_eval_scorecard(vmid: str, data_path: str) -> dict[str, Any]:
    """Run an evaluation scorecard workflow on data within the VM."""
    return await workflow_mgr.run_eval_scorecard(vmid, data_path)

@mcp.tool()
def list_artifacts() -> dict[str, Any]:
    """List all tracked artifacts in the index."""
    return artifact_idx.list()

@mcp.tool()
async def vm_exec(vmid: str, cmd: str, danger_mode: bool = False, actor: str = "mcp-agent") -> dict[str, Any]:
    """Execute a command on a VM with policy enforcement."""
    result = await service.exec(vmid=vmid, cmd=cmd, actor=actor, danger_mode=danger_mode)
    return result.to_dict()

@mcp.tool()
async def vm_guest_exec(vmid: str, cmd: str, cwd: str | None = None, env: dict[str, str] | None = None, timeout: int | None = None) -> dict[str, Any]:
    """Execute a command inside a Proxmox guest using the guest agent."""
    result = await gexec.exec(vmid=vmid, cmd=cmd, cwd=cwd, env=env, timeout=timeout)
    return result.to_dict()

@mcp.tool()
async def vm_file_put(vmid: str, local_path: str, remote_path: str) -> dict[str, Any]:
    """Upload a file to a VM."""
    result = await file_ops.put(vmid=vmid, local_path=local_path, remote_path=remote_path)
    return result.to_dict()

@mcp.tool()
async def vm_file_get(vmid: str, remote_path: str) -> dict[str, Any]:
    """Read a file from a VM."""
    result = await file_ops.get(vmid=vmid, remote_path=remote_path)
    return result.to_dict()

@mcp.tool()
async def vm_state(vmid: str, action: str) -> dict[str, Any]:
    """Manage VM power state: status, start, stop, reboot."""
    if action not in ["status", "start", "stop", "reboot"]:
        return {"ok": False, "error": f"Invalid action: {action}"}
    method = getattr(proxmox, action)
    result = await method(vmid)
    return result.to_dict()

@mcp.tool()
async def vm_snapshot(vmid: str, action: str, name: str | None = None) -> dict[str, Any]:
    """Manage VM snapshots: list, create, rollback, delete."""
    if action == "list":
        result = await snapshot.list(vmid)
    elif action == "create" and name:
        result = await snapshot.create(vmid, name)
    elif action == "rollback" and name:
        result = await snapshot.rollback(vmid, name)
    elif action == "delete" and name:
        result = await snapshot.delete(vmid, name)
    else:
        return {"ok": False, "error": f"Invalid action or missing name: {action}"}
    return result.to_dict()

@mcp.tool()
async def vm_config(vmid: str, action: str, params: dict[str, str] | None = None) -> dict[str, Any]:
    """Get or set VM configuration."""
    if action == "get":
        result = await proxmox_config.get(vmid)
    elif action == "set" and params:
        result = await proxmox_config.set(vmid, params)
    else:
        return {"ok": False, "error": f"Invalid action or missing params: {action}"}
    return result.to_dict()

@mcp.tool()
async def vm_service(vmid: str, action: str, service_name: str) -> dict[str, Any]:
    """Manage services in the guest: status, enable, disable, journal_tail."""
    if action == "status":
        result = await svc_mgr.status(vmid, service_name)
    elif action == "enable":
        result = await svc_mgr.enable(vmid, service_name)
    elif action == "disable":
        result = await svc_mgr.disable(vmid, service_name)
    elif action == "journal_tail":
        result = await svc_mgr.journal_tail(vmid, service_name)
    else:
        return {"ok": False, "error": f"Invalid action: {action}"}
    return result.to_dict()

@mcp.tool()
async def vm_docker(vmid: str, action: str, container: str | None = None, path: str | None = None) -> dict[str, Any]:
    """Manage Docker containers in the guest: ps, logs, restart, compose_up."""
    if action == "ps":
        result = await container_mgr.ps(vmid)
    elif action == "logs" and container:
        result = await container_mgr.logs(vmid, container)
    elif action == "restart" and container:
        result = await container_mgr.restart(vmid, container)
    elif action == "compose_up" and path:
        result = await container_mgr.compose_up(vmid, path)
    else:
        return {"ok": False, "error": f"Invalid action or missing args: {action}"}
    return result.to_dict()

@mcp.tool()
async def vm_slo_check(vmid: str | None = None, services: list[str] | None = None, containers: list[str] | None = None) -> dict[str, Any]:
    """Check SLO compliance for the system and optionally for a specific VM."""
    metrics_res = service.slo.check_metrics()
    guest_res = None
    if vmid:
        guest_res = await service.slo.check_guest_health(
            vmid=vmid,
            services=services or [],
            containers=containers or [],
            svc_mgr=svc_mgr,
            container_mgr=container_mgr
        )
    
    final_ok = metrics_res.ok and (guest_res.ok if guest_res else True)
    output = {
        "ok": final_ok,
        "metrics": {"ok": metrics_res.ok, "details": metrics_res.details}
    }
    if guest_res:
        output["guest"] = {"ok": guest_res.ok, "details": guest_res.details}
    return output

@mcp.tool()
def vm_metrics() -> dict[str, Any]:
    """Get system performance metrics."""
    return service.metrics_snapshot()

def main():
    mcp.run()

if __name__ == "__main__":
    main()
