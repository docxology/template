"""Digest the effective child environment without recording its values.

Scientific overrides and credentials that reach a child affect its execution
identity. Only exact executor-owned control names are omitted; a similarly named
user variable remains an input. The selected project's lock marker is transient
because the executor acquires that lock after resolving its plan.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path

from infrastructure.core.files.project_lock import _env_var, _lock_key

VOLATILE_CONTROL_KEYS = frozenset(
    {
        "PIPELINE_RUN_ID",
        "PIPELINE_STAGE_KEY",
        "PIPELINE_COMMAND_DIGEST",
        "PIPELINE_PLAN_DIGEST",
        "PIPELINE_SKIP_RECEIPT_PATH",
        "TEMPLATE_BOUNDED_RUN_IDS",
        "PYTEST_CURRENT_TEST",
    }
)


def environment_digest(environment: Mapping[str, str], *, project_dir: Path) -> str:
    """Hash effective values; do not return or persist the environment itself."""
    excluded = VOLATILE_CONTROL_KEYS | {_env_var(_lock_key(project_dir))}
    payload = {key: value for key, value in environment.items() if key not in excluded}
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def effective_environment_identity(repo_root: Path, project_dir: Path, *, mode: str | None = None) -> str:
    """Bind the same environment builder used by script stage execution."""
    from infrastructure.core.pipeline.stages import build_stage_subprocess_env

    return environment_digest(build_stage_subprocess_env(repo_root, project_dir, mode=mode), project_dir=project_dir)


__all__ = ["effective_environment_identity", "environment_digest"]
