# vm-mcp

Production-grade command orchestration framework for virtualized infrastructure, featuring a native Model Context Protocol (MCP) interface for AI-driven infrastructure management.

## Mission

Deliver a secure, async-capable, and observable control plane for Proxmox and Xen environments.

- **Strict Schema Enforcement**: 100% tool responses conform to reliable envelopes.
- **Asynchronous Orchestration**: Native job control and long-running task management.
- **Policy-Enforced Execution**: Allowlist/Denylist guardrails with audit logging.
- **MCP Native**: First-class support for AI agents (Gemini, Windsurf, Claude).

## Installation

```bash
# Clone the repository
git clone https://github.com/SWORDIntel/vm-mcp.git
cd vm-mcp

# Install dependencies
pip install . mcp fastmcp
```

## Features

### 1. MCP Server Interface
Expose your infrastructure to AI agents. The server provides tools for:
- **Execution**: `vm_exec`, `vm_guest_exec` (Proxmox-native)
- **Lifecycle**: `vm_state`, `vm_snapshot`, `vm_config`
- **Orchestration**: `vm_fan_out`, `vm_orchestrate` (Dependency graphs)
- **Observability**: `vm_slo_check`, `vm_metrics`

**Run the server:**
```bash
vm-mcp-server
```

### 2. CLI Tooling (`vmctl`)
A powerful CLI for manual operations.
- `vmctl exec --vmid 100 --cmd "ls -la"`
- `vmctl file put --vmid 100 --local ./app.py --remote /app/app.py`
- `vmctl service status --vmid 100 --name docker`
- `vmctl slo check --vmid 100`

### 3. Advanced Orchestration
- **Federation**: Execute commands across VM clusters with parallel fan-out.
- **Workflows**: Built-in managers for script generation, evaluation, and artifact tracking.
- **Security**: Automated secret redaction and audit trails for every operation.

## Roadmap Status

- [x] **P0: Foundations** (Runner, Async Jobs, Policy, Audit)
- [x] **P1: Platform Operations** (Proxmox-native, File Ops, Service/Docker)
- [x] **P1.6: Observability** (SLO Checker, Metrics, Events)
- [x] **P2: Workflow & UX** (Workflow Manager, Artifact Index)
- [x] **P3: Federation** (Fan-out, Dependency Graph)

## Development

**Run Tests:**
```bash
pytest
```

## Security & Compliance
- **PolicyEnforcer**: Default fail-closed policy.
- **Audit Logs**: Stored in `logs/audit.log` (configurable).
- **Redaction**: Secrets (passwords, tokens) are automatically redacted from stdout/stderr.

---
© 2026 SWORDIntel. Production-grade orchestration for the modern cloud.
