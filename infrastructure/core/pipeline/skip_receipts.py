"""Fresh, parent-bound reasons for an explicitly skippable child stage."""

from __future__ import annotations

import json
import os
from pathlib import Path
from collections.abc import Mapping

from infrastructure.core.files.secure_write import atomic_write_text_confined, read_bytes_confined

SKIP_SCHEMA_VERSION = 1
SKIP_REASONS = frozenset({"tool_unavailable", "disabled_by_config", "not_applicable"})
_BINDINGS = {
    "run_id": "PIPELINE_RUN_ID",
    "stage_key": "PIPELINE_STAGE_KEY",
    "command_digest": "PIPELINE_COMMAND_DIGEST",
    "plan_digest": "PIPELINE_PLAN_DIGEST",
}


def write_skip_receipt(reason: str, diagnostic: str, *, env: Mapping[str, str] | None = None) -> bool:
    """Record a reason under a parent's fresh receipt path; standalone calls have no receipt."""
    environment = os.environ if env is None else env
    if reason not in SKIP_REASONS or not diagnostic.strip():
        raise ValueError("A skip requires a supported reason and nonempty diagnostic")
    target = environment.get("PIPELINE_SKIP_RECEIPT_PATH")
    if not target:
        return False
    bindings = {key: environment.get(variable, "") for key, variable in _BINDINGS.items()}
    if not all(bindings.values()):
        raise ValueError("Incomplete skip receipt identity")
    path = Path(target)
    root = path.parent
    payload = {"schema_version": SKIP_SCHEMA_VERSION, **bindings, "reason": reason, "diagnostic": diagnostic}
    atomic_write_text_confined(root, path, json.dumps(payload, sort_keys=True) + "\n", mode=0o600)
    return True


def validate_skip_receipt(path: Path, *, env: Mapping[str, str]) -> tuple[str, str] | None:
    """Accept only a current command/run/plan/stage receipt created after parent removal."""
    try:
        payload = json.loads(read_bytes_confined(path.parent, path, max_bytes=64 * 1024))
    except (OSError, ValueError):
        return None
    if (
        not isinstance(payload, dict)
        or type(payload.get("schema_version")) is not int
        or payload["schema_version"] != SKIP_SCHEMA_VERSION
    ):
        return None
    if any(payload.get(key) != env.get(variable) for key, variable in _BINDINGS.items()):
        return None
    reason, diagnostic = payload.get("reason"), payload.get("diagnostic")
    if (
        not isinstance(reason, str)
        or reason not in SKIP_REASONS
        or not isinstance(diagnostic, str)
        or not diagnostic.strip()
    ):
        return None
    return str(reason), diagnostic


__all__ = ["validate_skip_receipt", "write_skip_receipt"]
