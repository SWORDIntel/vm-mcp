# vm-mcp

Production-grade command orchestration framework for virtualized infrastructure, evolving from a basic guest execution wrapper into an async-capable, policy-enforced, observable control plane.

## Mission

Deliver a secure, backwards-compatible execution engine that preserves existing guest execution transport behavior while introducing:

- strict response schemas,
- asynchronous job control,
- hardened policy guardrails,
- deep observability,
- multi-VM orchestration and federation.

## Runtime Baseline (Current Target)

- **Hypervisor**: Proxmox VE cluster with QEMU guest agent enabled on target VMs.
- **Execution tooling**: `qm guest exec` transport with adapter-ready abstraction for async orchestration layers.
- **Storage**: Proxmox-managed VM volumes and snapshots.
- **Containers/services**: Docker/Compose + service orchestration inside guest VMs.

> Compatibility is mandatory: preserve existing `qm guest exec` behavior while layering async control, policy guardrails, and observability.

## Priority Model

- **P0** — must-have for safe daily operation
- **P1** — high-impact operational capability
- **P2** — workflow acceleration and developer UX
- **P3** — scale-out and federation

## Recommended Implementation Order

1. P0.1 Core reliability
2. P0.2 Security and guardrails
3. P1.4 File operations (automation unlock)
4. P1.5 Service/container orchestration
5. P1.6 Observability and SLO
6. P1.3 Proxmox-native operations
7. P2 workflow wrappers + SDK
8. P3 federation

---

## P0 — Foundations (Safety + Reliability)

### 1) Core reliability

- Unified command runner with:
  - hard timeout controls
  - bounded retry policy
  - consistent error envelope
- Async job model for long operations:
  - `job_start`
  - `job_status`
  - `job_cancel`
- Strict response schema for all tools:
  - `ok`, `code`, `stdout`, `stderr`, `duration_ms`, `vmid`, `cmd`
- VM profile resolution:
  - profile name -> vmid/auth/runtime defaults

### 2) Security and guardrails

- Policy engine:
  - allowlist (safe defaults)
  - denylist (destructive commands blocked by default)
  - per-request `danger_mode` override with audit tag
- Secret safety:
  - password/token from env or file only
  - output redaction for sensitive patterns
- Audit logging:
  - who/what/when/result for every tool call

---

## P1 — Platform Operations

### 3) Proxmox-native operations

- Extend `vm_exec` with:
  - `cwd`, `env`, `stdin`, `timeout`, optional PTY
- Reliable stdin path using transport adapters that preserve compatibility for legacy backends.
- VM lifecycle namespace:
  - `vm_state` (`status/start/stop/reboot`)
  - `vm_snapshot` (`list/create/rollback/delete`)
  - `vm_config_get` / `vm_config_set` (safe subset)
- Guest-agent probe tool
- Proxmox coverage targets:
  - `qm status`, `qm start`, `qm stop`, `qm reboot`
  - VM profile resolution and safe config materialization
  - snapshot lifecycle and disk operation workflows

### 4) In-VM file operations

- `vm_file_put` / `vm_file_get`:
  - chunked transfer
  - checksum validation
- `vm_file_tail` with bounded follow mode
- `vm_file_stat` / `vm_file_find`
- Remote script runner pattern:
  - upload temp file -> execute -> collect output -> cleanup

### 5) Service and container orchestration

- `vm_service` expansion:
  - `is-active`, `is-enabled`, `enable`, `disable`, `journal_tail`
- `vm_docker` namespace:
  - `ps`, `logs`, `inspect`, `restart`, `compose up/down/pull`
- Stack health summary endpoint for critical services

### 6) Observability and SLO

- Internal metrics:
  - request count
  - error rate
  - timeout rate
  - latency percentiles
- SLO checker tool:
  - required service/container checks
  - throughput floor checks
- Event-stream updates for long tasks

---

## P2 — Workflow and UX

### 7) Data and analysis workflow wrappers

- One-shot workflow tools:
  - `run_generate_outputs`
  - `run_eval_scorecard`
  - `run_panel_snapshot`
- Scheduler primitives:
  - create/list/remove periodic jobs
- Artifact index:
  - latest outputs, sizes, mtimes, score deltas

### 8) SDK and operator UX

- Typed Python client SDK for vm-mcp
- Thin CLI (`vmctl`) over MCP methods
- Ops docs:
  - profile examples
  - safe defaults
  - troubleshooting (`qm`, guest-agent, sudo, docker)

---

## P3 — Federation

### 9) Multi-VM orchestration and federation

- Multi-target fan-out execution
- Role-based profile groups (`collector`, `analysis`, `authority`)
- Cross-VM dependency workflow execution graph

---

## Tactical Implementation Specification (TIS)

### SITREP

- **Current State**: Synchronous guest execution wrapper with limited namespace support and no telemetry.
- **Objective**: Build a production-grade execution engine with async control, strict schema guarantees, and federated orchestration for Proxmox-managed fleets.
- **Threat Assessment**: Scaling before P0 completion introduces systemic integrity risk (`THREATCON: ALPHA`).

### BATTLE PLAN

- **OBJECTIVE**: Execute phased refactor and feature expansion across P0→P3 while preserving transport compatibility.
- **CURRENT_STATE**: Blocking execution path, limited safety controls, no orchestration graph.
- **ACTIONS**:
  1. **Phase I / P0**: Introduce unified async runner, strict schema envelope, policy engine, secret redaction, and audit trail.
  2. **Phase II / P1**: Expand execution options, lifecycle namespaces, file APIs, and container/service orchestration on Proxmox.
  3. **Phase III / P2**: Add telemetry streams, SLO checks, workflow wrappers, scheduler primitives, SDK/CLI.
  4. **Phase IV / P3**: Enable fan-out execution, role-based routing, and cross-VM dependency graphs.
- **VERIFICATION**:
  - destructive commands blocked by default policy
  - async jobs respect timeout/cancel semantics
  - dependency graph enforces role and order constraints
  - Proxmox lifecycle adapters pass compatibility integration tests
- **CONTINGENCY**:
  - if guest-agent stalls under load, fail over to direct hypervisor API/CLI state intervention and mark affected nodes degraded.

### QUALITY METRICS & SUCCESS VALIDATION

- **Metric 1 — Schema Compliance**: 100% tool responses conform to strict envelope.
- **Metric 2 — Orchestration Reliability**: >99% success for dependency-graph execution.
- **Metric 3 — Observability Coverage**: 100% timeout/policy/latency anomalies represented in metrics.
- **Success Validation**: `vmctl` orchestrates multi-VM stack deployment with async tracking, secure credential handling, and validated service/container health.

### SECURITY & COMPLIANCE GATES

- No secret injection via CLI args (env/file only).
- PolicyEnforcer runs fail-closed by default.
- Static analysis and test gates required before phase advancement.
- Target test coverage: >90% unit coverage for newly introduced modules.

## Compatibility Contract

- Primary target: Proxmox-native execution and lifecycle operations.
- Compatibility requirement: legacy transport behavior remains available behind adapter boundaries during migration.
