#!/usr/bin/env python3
"""Thin orchestrator for manuscript-variable hydration."""

from __future__ import annotations

from pathlib import Path

from _bootstrap import ensure_project_paths

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = next(
    (
        candidate
        for candidate in (PROJECT_ROOT, *PROJECT_ROOT.parents)
        if (candidate / "infrastructure").is_dir() and (candidate / "pyproject.toml").is_file()
    ),
    PROJECT_ROOT,
)
ensure_project_paths(PROJECT_ROOT, repo_root=REPO_ROOT)

from template_autoresearch_project.loop.settlement import settle_standalone_hydration  # noqa: E402

_LOOP_JSON = PROJECT_ROOT / "output" / "data" / "autoresearch_loop.json"


def main() -> int:
    """Write manuscript variables and resolved manuscript sources."""
    if not _LOOP_JSON.exists():
        raise FileNotFoundError(
            f"Missing {_LOOP_JSON.relative_to(PROJECT_ROOT)} — run "
            f"projects/templates/template_autoresearch_project/scripts/run_autoresearch_loop.py first."
        )
    paths = settle_standalone_hydration(PROJECT_ROOT, REPO_ROOT)
    print(paths[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
