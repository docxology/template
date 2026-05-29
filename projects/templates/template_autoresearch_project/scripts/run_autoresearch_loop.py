#!/usr/bin/env python3
"""Thin orchestrator for the deterministic AutoResearch loop."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_ROOT.parents[2]
for path in (PROJECT_ROOT, PROJECT_ROOT / "src", REPO_ROOT):
    path_text = str(path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)

from src.loop import run_autoresearch_loop  # noqa: E402


def main() -> int:
    """Run the project AutoResearch loop."""
    result = run_autoresearch_loop(PROJECT_ROOT, REPO_ROOT)
    print(PROJECT_ROOT / "output" / "reports" / "autoresearch_loop.md")
    return 0 if result.readiness_valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
