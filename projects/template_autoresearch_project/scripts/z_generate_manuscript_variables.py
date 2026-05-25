#!/usr/bin/env python3
"""Thin orchestrator for manuscript-variable hydration."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_ROOT.parents[1]
for path in (PROJECT_ROOT, PROJECT_ROOT / "src", REPO_ROOT):
    path_text = str(path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)

from infrastructure.rendering.manuscript_injection import write_resolved_manuscript_tree  # noqa: E402
from src.loop import run_autoresearch_loop  # noqa: E402
from src.manuscript_variables import compute_variables, save_variables  # noqa: E402


def main() -> int:
    """Write manuscript variables and resolved manuscript sources."""
    if not (PROJECT_ROOT / "output" / "data" / "autoresearch_loop.json").exists():
        run_autoresearch_loop(PROJECT_ROOT, REPO_ROOT)
    variables = compute_variables(PROJECT_ROOT)
    out_path = save_variables(variables, PROJECT_ROOT / "output" / "data" / "manuscript_variables.json")
    write_resolved_manuscript_tree(PROJECT_ROOT, variables)
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
