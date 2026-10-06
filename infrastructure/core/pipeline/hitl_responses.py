"""Typed validation of responses bound to a specific paused execution."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AgentResponseValidation:
    """Validation result for a detached HITL agent response."""

    valid: bool
    issues: tuple[str, ...] = ()
    payload: dict[str, Any] = field(default_factory=dict)


AGENT_RESPONSE_ACTIONS = ("approve", "reject", "guide", "resume", "abort")
DECISION_BINDINGS = ("run_id", "plan_digest", "stage_key", "artifact_digest")


def agent_response_schema() -> dict[str, Any]:
    """Return the JSON schema for detached HITL responses."""
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "required": ["action"],
        "properties": {
            "action": {"type": "string", "enum": list(AGENT_RESPONSE_ACTIONS)},
            "message": {"type": "string"},
            "reason": {"type": "string"},
            "stage_num": {"type": "integer", "minimum": 0},
            "run_id": {"type": "string", "minLength": 1},
            "plan_digest": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            "stage_key": {"type": "string", "minLength": 1},
            "artifact_digest": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        },
        "allOf": [
            {
                "if": {"properties": {"action": {"enum": ["approve", "reject", "resume", "abort"]}}},
                "then": {"required": list(DECISION_BINDINGS)},
            }
        ],
    }


def validate_agent_response_file(path: Path) -> AgentResponseValidation:
    """Validate a detached HITL response JSON file without recording it."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return AgentResponseValidation(valid=False, issues=(f"invalid response JSON: {exc}",))
    if not isinstance(payload, dict):
        return AgentResponseValidation(valid=False, issues=("response must be a JSON object",))
    issues: list[str] = []
    allowed = set(agent_response_schema()["properties"])
    unknown = set(payload) - allowed
    if unknown:
        issues.append(f"unsupported response key(s): {', '.join(sorted(unknown))}")
    action = payload.get("action")
    if not isinstance(action, str) or action not in AGENT_RESPONSE_ACTIONS:
        issues.append(f"unsupported action: {action}")
    if action == "guide" and not str(payload.get("message", "") or "").strip():
        issues.append("guide responses require message")
    for key in ("message", "reason"):
        if key in payload and not isinstance(payload[key], str):
            issues.append(f"{key} must be a string")
    if isinstance(action, str) and action in {"approve", "reject", "resume", "abort"}:
        for key in DECISION_BINDINGS:
            value = payload.get(key)
            if not isinstance(value, str) or not value.strip():
                issues.append(f"Detached decision requires {key}")
            elif key.endswith("digest") and re.fullmatch(r"[0-9a-f]{64}", value) is None:
                issues.append(f"Detached decision {key} must be a SHA-256 digest")
    if "stage_num" in payload and (type(payload["stage_num"]) is not int or payload["stage_num"] < 0):
        issues.append("stage_num must be a nonnegative integer")
    return AgentResponseValidation(valid=not issues, issues=tuple(issues), payload=payload if not issues else {})
