#!/usr/bin/env python3
"""Write manuscript variables from SIA loop outputs."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_ROOT.parents[2]
for path in (PROJECT_ROOT, PROJECT_ROOT / "src", REPO_ROOT):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

from infrastructure.rendering.manuscript_injection import write_resolved_manuscript_tree

from src.reports import compute_variables, write_manuscript_variables


def main() -> int:
    summary = PROJECT_ROOT / "output" / "runs" / "run_1" / "run_summary.json"
    if not summary.is_file():
        raise FileNotFoundError(
            f"Missing {summary.relative_to(PROJECT_ROOT)} — run scripts/run_sia_loop.py first."
        )
    variables_path = write_manuscript_variables(PROJECT_ROOT)
    variables = compute_variables(PROJECT_ROOT)
    write_resolved_manuscript_tree(PROJECT_ROOT, variables)
    print(variables_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
