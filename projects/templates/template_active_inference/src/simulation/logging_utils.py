"""Structured JSONL logging for pymdp runs."""

from __future__ import annotations

import json
import os
import time
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STEP_EVENT = "si_tmaze_step"
HEADER_EVENT = "si_tmaze_run_header"

_REQUIRED_KEYS: dict[str, tuple[str, ...]] = {
    HEADER_EVENT: ("event", "config_hash", "mode", "seed", "policy_len"),
    STEP_EVENT: ("event", "step", "obs", "action", "belief_entropy"),
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _json_default(obj: Any) -> Any:
    if hasattr(obj, "tolist"):
        return obj.tolist()
    raise TypeError(f"not JSON serializable: {type(obj)!r}")


def validate_record(record: Mapping[str, Any]) -> None:
    """Validate record."""
    event = str(record.get("event", ""))
    required = _REQUIRED_KEYS.get(event)
    if required is None:
        return
    missing = [key for key in required if key not in record]
    if missing:
        raise ValueError(f"JSONL record for {event!r} missing keys: {missing}")


@dataclass
class RunLogger:
    """Data container for RunLogger."""

    path: Path
    enabled: bool = True

    def __post_init__(self) -> None:
        self.path = Path(self.path)
        if self.enabled:
            self.path.parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_project_root(
        cls,
        project_root: Path,
        *,
        relative_path: str = "output/logs/pymdp_runs.jsonl",
        enabled: bool | None = None,
    ) -> RunLogger:
        """Process from project root."""
        if enabled is None:
            enabled = os.environ.get("PYMDP_RUN_LOG_DISABLED", "") != "1"
        return cls(path=project_root / relative_path, enabled=enabled)

    def fresh(self) -> None:
        """Process fresh."""
        if self.enabled:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text("", encoding="utf-8")

    def emit(self, record: Mapping[str, Any]) -> None:
        """Process emit."""
        if not self.enabled:
            return
        full = {"timestamp": _now_iso(), **dict(record)}
        validate_record(full)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(full, separators=(",", ":"), default=_json_default) + "\n")

    def emit_run_header(
        self,
        *,
        config_hash: str,
        mode: str,
        seed: int,
        policy_len: int,
    ) -> None:
        """Process emit run header."""
        self.emit(
            {
                "event": HEADER_EVENT,
                "config_hash": config_hash,
                "mode": mode,
                "seed": seed,
                "policy_len": policy_len,
            }
        )

    @contextmanager
    def timed(self, **fields: Any) -> Iterator[dict[str, Any]]:
        """Process timed."""
        ctx: dict[str, Any] = dict(fields)
        start = time.perf_counter()
        try:
            yield ctx
        finally:
            ctx["runtime_ms"] = round((time.perf_counter() - start) * 1000.0, 3)
            self.emit(ctx)

    def records(self) -> list[dict[str, Any]]:
        """Process records."""
        if not self.path.exists():
            return []
        out: list[dict[str, Any]] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                out.append(json.loads(line))
        return out

    def step_records(self) -> list[dict[str, Any]]:
        """Process step records."""
        return [rec for rec in self.records() if rec.get("event") == STEP_EVENT]
