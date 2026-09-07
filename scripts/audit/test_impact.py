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


def _git_changed_paths(repo_root: Path = REPO_ROOT) -> list[str]:
    """Return staged, unstaged, deleted, and non-ignored untracked paths.

    Keep the three sources explicit instead of relying on one combined
    ``git diff HEAD`` call.  The union is the same for ordinary files, but
    separate commands preserve the intended contract when an index/worktree
    transition (for example, a staged rename followed by an unstaged edit)
    needs to be diagnosed from the planner's input.  ``-z`` also keeps paths
    containing whitespace or newlines unambiguous.
    """
    policy = SubprocessPolicy(
        policy_id="test-impact-git",
        source_path="scripts/audit/test_impact.py",
        timeout_seconds=30,
        capture_output=True,
    )

    def run_paths(args: list[str], error_label: str) -> list[str]:
        """Run a NUL-delimited Git path query and decode it safely."""
        result = run_with_policy(args, cwd=repo_root, env=None, policy=policy)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.command_error or f"{error_label} failed")
        return [item for item in result.stdout.split("\0") if item]

    paths: set[str] = set()
    paths.update(
        run_paths(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACDMRTUXB", "-z", "--"],
            "git staged diff",
        )
    )
    paths.update(
        run_paths(
            ["git", "diff", "--name-only", "--diff-filter=ACDMRTUXB", "-z", "--"],
            "git worktree diff",
        )
    )
    paths.update(
        run_paths(
            ["git", "ls-files", "--others", "--exclude-standard", "-z", "--"],
            "git untracked-file scan",
        )
    )
    return sorted(paths)


def main(argv: list[str] | None = None) -> int:
    """Run the impact planner."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        help="changed paths; defaults to staged, unstaged, and non-ignored untracked paths",
    )
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
