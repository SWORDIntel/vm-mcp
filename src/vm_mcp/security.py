from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(slots=True)
class RedactionRule:
    pattern: re.Pattern[str]
    replacement: str = "[REDACTED]"


class SecretRedactor:
    def __init__(self) -> None:
        self._rules = [
            RedactionRule(re.compile(r"(?i)(password|token|secret)\s*[=:]\s*[^\s\n]+")),
            RedactionRule(re.compile(r"(?i)bearer\s+[a-z0-9._-]+")),
        ]

    def redact(self, text: str) -> str:
        value = text
        for rule in self._rules:
            value = rule.pattern.sub(rule.replacement, value)
        return value
