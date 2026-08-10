#!/usr/bin/env python3
"""Print changed-surface test guidance for the current checkout or paths."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from infrastructure.core.test_impact import classify_changed_paths  # noqa: E402
from infrastructure.core.subprocess_policy import SubprocessPolicy, run_with_policy  # noqa: E402


def _git_changed_paths() -> list[str]:
    """Return unstaged and staged paths from git without shell expansion."""
    result = run_with_policy(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=REPO_ROOT,
        env=None,
        policy=SubprocessPolicy(
            policy_id="test-impact-git",
            source_path="scripts/audit/test_impact.py",
            timeout_seconds=30,
            capture_output=True,
        ),
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.command_error or "git diff failed")
    return [line for line in result.stdout.splitlines() if line]


def main(argv: list[str] | None = None) -> int:
    """Run the impact planner."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="changed paths; defaults to git diff --name-only HEAD")
    args = parser.parse_args(argv)
    try:
        paths = args.paths or _git_changed_paths()
        plan = classify_changed_paths(paths)
    except (OSError, RuntimeError) as exc:
        parser.error(str(exc))
    print(json.dumps(plan.__dict__, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
