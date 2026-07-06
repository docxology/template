"""Shared dataclasses and utilities for template_autopoiesis."""

from __future__ import annotations

from dataclasses import dataclass


def trunc(text: str, max_len: int = 80) -> str:
    """Truncate *text* to *max_len* characters, appending '…' if clipped."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


@dataclass(frozen=True)
class CheckResult:
    """Single predicate check outcome."""

    name: str
    passed: bool
    detail: str = ""


@dataclass(frozen=True)
class CheckReport:
    """Aggregate report for a generated child project."""

    child_root: str
    checks: tuple[CheckResult, ...]

    @property
    def all_passed(self) -> bool:
        return all(c.passed for c in self.checks)

    @property
    def failed(self) -> tuple[CheckResult, ...]:
        return tuple(c for c in self.checks if not c.passed)
