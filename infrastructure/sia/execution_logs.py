"""Load and normalize SIA agent execution logs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from infrastructure.core.exceptions import ValidationError

from .models import AgentExecutionLog


def load_agent_execution(path: Path) -> AgentExecutionLog:
    """Load agent_execution.json in single- or multi-trajectory format.

    Args:
        path: Path to agent_execution.json or agent_execution/ directory.

    Returns:
        Normalized AgentExecutionLog.

    Raises:
        ValidationError: When the file is missing or malformed.
    """
    resolved = path.resolve()
    if resolved.is_dir():
        return _load_multi_trajectory_dir(resolved)
    if not resolved.is_file():
        raise ValidationError(f"Agent execution log not found: {resolved}")

    payload = json.loads(resolved.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and "trajectories" in payload:
        trajectories = tuple(_coerce_trajectory(item) for item in payload["trajectories"])
        return AgentExecutionLog(trajectories=trajectories, format="multi")
    if isinstance(payload, dict):
        return AgentExecutionLog(trajectories=(payload,), format="single")
    raise ValidationError(f"Unsupported agent execution format: {resolved}")


def _load_multi_trajectory_dir(directory: Path) -> AgentExecutionLog:
    files = sorted(directory.glob("execution_q*.json"))
    if not files:
        raise ValidationError(f"No execution_q*.json files in {directory}")
    trajectories = tuple(_coerce_trajectory(json.loads(file.read_text(encoding="utf-8"))) for file in files)
    return AgentExecutionLog(trajectories=trajectories, format="multi")


def _coerce_trajectory(item: Any) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise ValidationError("Each trajectory must be a JSON object")
    return dict(item)


__all__ = ["load_agent_execution"]
