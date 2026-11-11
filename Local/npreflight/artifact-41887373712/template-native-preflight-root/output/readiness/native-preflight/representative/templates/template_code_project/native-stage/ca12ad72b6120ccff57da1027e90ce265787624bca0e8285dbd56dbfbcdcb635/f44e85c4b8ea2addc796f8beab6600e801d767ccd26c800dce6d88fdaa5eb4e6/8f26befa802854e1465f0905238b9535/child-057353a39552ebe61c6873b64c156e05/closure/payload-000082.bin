"""Canonical execution mode and deterministic build epoch admission.

Build time is pinned before execution and participates in the effective child
environment identity. This is distinct from actual operation timestamps. A
non-Git export requires its caller to supply the candidate epoch explicitly.
"""

from __future__ import annotations

import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from collections.abc import Mapping

_TRUE = frozenset({"1", "true", "yes", "on"})


def _epoch(value: str) -> int:
    try:
        epoch = int(value)
        if epoch < 0:
            raise ValueError("negative epoch")
        datetime.fromtimestamp(epoch, tz=timezone.utc)
        return epoch
    except (ValueError, OverflowError, OSError) as exc:
        raise ValueError("SOURCE_DATE_EPOCH must be a nonnegative representable integer epoch") from exc


def _candidate_epoch(repo_root: Path, environment: Mapping[str, str]) -> tuple[int, str]:
    """Require the nominated repository itself, rather than an ambient Git tree."""
    env = {key: value for key, value in environment.items() if not key.startswith("GIT_")}
    env.update(LC_ALL="C", GIT_OPTIONAL_LOCKS="0", GIT_NO_REPLACE_OBJECTS="1")
    root = repo_root.resolve()
    try:
        top = subprocess.run(  # nosec B603 B607 -- fixed read-only Git argv, sanitized Git environment
            ["git", "rev-parse", "--show-toplevel"], cwd=root, env=env, capture_output=True, text=True, timeout=5
        )
        if top.returncode or Path(top.stdout.strip()).resolve() != root:
            raise ValueError("No nominated Git candidate; set SOURCE_DATE_EPOCH explicitly for exported execution")
        result = subprocess.run(  # nosec B603 B607 -- fixed read-only Git argv, sanitized Git environment
            ["git", "--no-pager", "show", "-s", "--format=%H%n%ct", "HEAD"],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ValueError("Git candidate epoch unavailable; set SOURCE_DATE_EPOCH explicitly") from exc
    rows = result.stdout.splitlines()
    if result.returncode or len(rows) != 2 or re.fullmatch(r"[0-9a-f]{40,64}", rows[0]) is None:
        raise ValueError("Git candidate epoch is invalid; set SOURCE_DATE_EPOCH explicitly")
    return _epoch(rows[1]), "git:" + rows[0]


def apply_execution_policy(base_env: Mapping[str, str], repo_root: Path, *, mode: str | None = None) -> dict[str, str]:
    """Pin the actual child policy before producing its immutable plan identity."""
    env = dict(base_env)
    selected = mode if mode is not None else env.get("TEMPLATE_EXECUTION_MODE", "core")
    if selected not in {"core", "live"}:
        raise ValueError("TEMPLATE_EXECUTION_MODE must be core or live")
    deterministic = env.get("TEMPLATE_DETERMINISTIC", "").strip().lower()
    if deterministic and deterministic not in _TRUE:
        raise ValueError("Canonical execution is deterministic; retired clock-disable settings are unsupported")
    explicit = env.get("SOURCE_DATE_EPOCH", "").strip()
    if explicit:
        epoch = _epoch(explicit)
        provenance = env.get("TEMPLATE_BUILD_EPOCH_SOURCE", "explicit")
    else:
        epoch, provenance = _candidate_epoch(repo_root, env)
    env.update(
        TEMPLATE_EXECUTION_MODE=selected,
        TEMPLATE_DETERMINISTIC="1",
        SOURCE_DATE_EPOCH=str(epoch),
        TEMPLATE_BUILD_EPOCH_SOURCE=provenance,
    )
    return env


__all__ = ["apply_execution_policy"]
