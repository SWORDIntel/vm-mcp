from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PolicyConfig:
    allowlist: tuple[str, ...] = ("echo", "ls", "pwd", "cat", "qm")
    denylist: tuple[str, ...] = ("rm -rf", "mkfs", "dd if=", "shutdown", "reboot")


class PolicyError(RuntimeError):
    pass


class PolicyEnforcer:
    def __init__(self, config: PolicyConfig | None = None) -> None:
        self.config = config or PolicyConfig()

    def validate(self, cmd: str, danger_mode: bool = False) -> None:
        lowered = cmd.strip().lower()
        if not lowered:
            raise PolicyError("empty command is not allowed")

        if any(blocked in lowered for blocked in self.config.denylist) and not danger_mode:
            raise PolicyError("command blocked by denylist")

        if not lowered.startswith(self.config.allowlist):
            raise PolicyError("command does not match allowlist")
