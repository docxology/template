#!/usr/bin/env python3
"""Thin orchestrator for manuscript-variable hydration."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_ROOT.parents[2]
for path in (PROJECT_ROOT, PROJECT_ROOT / "src", REPO_ROOT):
    path_text = str(path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)

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
    loop_payload = json.loads((PROJECT_ROOT / "output" / "data" / "autoresearch_loop.json").read_text())
    declared_paths = [
        PROJECT_ROOT / str(path) for path in loop_payload.get("output_paths", []) if isinstance(path, str)
    ]
    write_artifact_manifest(PROJECT_ROOT, [*declared_paths, *paths])
    print(paths[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
