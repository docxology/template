#!/usr/bin/env python3
"""Thin orchestrator for manuscript-variable hydration."""

from __future__ import annotations

from pathlib import Path

from _bootstrap import ensure_project_paths

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ensure_project_paths(PROJECT_ROOT)

REPO_ROOT = next(
    candidate for candidate in (PROJECT_ROOT, *PROJECT_ROOT.parents) if (candidate / "infrastructure").is_dir()
)

from infrastructure.rendering.manuscript_injection import write_resolved_manuscript_tree  # noqa: E402
from src.manuscript_variables import compute_variables, write_manuscript_hydration_artifacts  # noqa: E402
from src.writers import write_artifact_manifest  # noqa: E402

_LOOP_JSON = PROJECT_ROOT / "output" / "data" / "autoresearch_loop.json"


def main() -> int:
    """Write manuscript variables and resolved manuscript sources."""
    if not _LOOP_JSON.exists():
        raise FileNotFoundError(
            f"Missing {_LOOP_JSON.relative_to(PROJECT_ROOT)} — run "
            f"projects/templates/template_autoresearch_project/scripts/run_autoresearch_loop.py first."
        )
    paths = write_manuscript_hydration_artifacts(
        PROJECT_ROOT,
        require_valid=True,
        validate_sources=True,
    )
    variables = compute_variables(PROJECT_ROOT)
    write_resolved_manuscript_tree(PROJECT_ROOT, variables)
    write_artifact_manifest(PROJECT_ROOT, repo_root=REPO_ROOT)
    print(paths[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
