from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class AuditLogger:
    path: Path

    def log(self, *, actor: str, action: str, vmid: str, cmd: str, result: dict[str, Any], audit_tag: str | None = None) -> None:
        event = {
            "ts": datetime.now(tz=timezone.utc).isoformat(),
            "actor": actor,
            "action": action,
            "vmid": vmid,
            "cmd": cmd,
            "result": result,
            "audit_tag": audit_tag,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(event, sort_keys=True) + "\n")
