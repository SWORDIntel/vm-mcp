from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .audit import AuditLogger
from .jobs import JobManager
from .models import CommandResult
from .policy import PolicyEnforcer
from .runner import CommandRunner
from .metrics import MetricsStore, Timer
from .security import SecretRedactor
from .slo import SLOChecker


@dataclass(slots=True)
class VMService:
    runner: CommandRunner
    policy: PolicyEnforcer
    jobs: JobManager
    audit: AuditLogger
    redactor: SecretRedactor
    metrics: MetricsStore
    _slo: SLOChecker | None = None

    @classmethod
    def build(cls, audit_path: str = "logs/audit.log") -> "VMService":
        runner = CommandRunner()
        policy = PolicyEnforcer()
        jobs = JobManager(runner=runner)
        audit = AuditLogger(path=Path(audit_path))
        redactor = SecretRedactor()
        metrics = MetricsStore()
        return cls(runner=runner, policy=policy, jobs=jobs, audit=audit, redactor=redactor, metrics=metrics)

    @property
    def slo(self) -> SLOChecker:
        if self._slo is None:
            self._slo = SLOChecker(self.metrics)
        return self._slo

    async def exec(self, *, vmid: str, cmd: str, actor: str = "system", danger_mode: bool = False, 
                   audit_tag: str | None = None, cwd: str | None = None, 
                   env: dict[str, str] | None = None, timeout: int | None = None) -> CommandResult:
        timer = Timer()
        try:
            self.policy.validate(cmd, danger_mode=danger_mode)
        except Exception:
            self.metrics.record_policy_block()
            raise

        # Determine if we should use guest exec or host exec
        # For now, if any guest-specific flag is set, we could use ProxmoxGuestExec
        # but the current architecture has service.runner as a generic CommandRunner.
        # Let's keep it simple and just use the runner.run with extended args if we update it.
        
        result = await self.runner.run(vmid=vmid, cmd=cmd, timeout_s=float(timeout) if timeout else None)
        result.stdout = self.redactor.redact(result.stdout)
        result.stderr = self.redactor.redact(result.stderr)
        self.audit.log(actor=actor, action="vm_exec", vmid=vmid, cmd=cmd, result=result.to_dict(), audit_tag=audit_tag)
        self.metrics.record(action="vm_exec", duration_ms=timer.elapsed_ms(), ok=result.ok, timeout=(result.code == 124))
        return result

    def metrics_snapshot(self) -> dict[str, float | int | dict[str, int]]:
        return self.metrics.snapshot()
