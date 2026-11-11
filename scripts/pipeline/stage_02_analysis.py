#!/usr/bin/env python3
"""Analysis-stage orchestrator (thin dispatcher).

Stage 02. Discovers ``projects/<name>/scripts/*.py`` and runs each in the
configuration-declared order when ``analysis.scripts`` exists, otherwise in
lexicographic discovery order, via
:func:`infrastructure.core.analysis_pipeline.execute_analysis_stage`.
This file is intentionally thin — all execution logic lives in
:mod:`infrastructure.core.analysis_pipeline` and
:mod:`infrastructure.core.script_discovery`.

Architecture:
    Generic Layer-1 entry point. Discovers and dispatches to project-specific
    scripts without knowing their implementation details. Follows the thin
    orchestrator pattern.

Exit codes:
    0: All discovered analysis scripts completed successfully (or no scripts found).
    1: At least one analysis script failed, or an unrecoverable pipeline error.
    2: Invalid configuration, before producer execution.
    75: Execution blocked by source or runtime admission.
    124: Analysis deadline expired.
    130: Analysis interrupted.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Bootstrap: add repo root so the centralized helper itself is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts import ensure_repo_root_on_path  # noqa: E402

ensure_repo_root_on_path()

from infrastructure.core.analysis_pipeline import execute_analysis_stage  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run analysis pipeline (Stage 02)")
    parser.add_argument(
        "--project",
        default="project",
        help="Project name in projects/ directory (default: project)",
    )
    args = parser.parse_args()

    return execute_analysis_stage(Path(__file__).resolve().parents[2], args.project)


if __name__ == "__main__":
    sys.exit(main())
