#!/usr/bin/env python3
"""Analysis-stage orchestrator (thin dispatcher).

Stage 02. Discovers ``projects/<name>/scripts/*.py`` and runs each in
lexicographic order via :func:`infrastructure.core.analysis_pipeline.run_analysis_pipeline`.
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
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Bootstrap: add repo root so the centralized helper itself is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts import ensure_repo_root_on_path  # noqa: E402

ensure_repo_root_on_path()

from infrastructure.core.analysis_pipeline import run_analysis_pipeline  # noqa: E402
from infrastructure.core.exceptions import PipelineError, ScriptExecutionError  # noqa: E402
from infrastructure.core.logging.utils import (  # noqa: E402
    get_logger,
    log_header,
    log_live_resource_usage,
    log_success,
)
from infrastructure.core.script_discovery import (  # noqa: E402
    discover_analysis_scripts,
    verify_analysis_outputs,
)

logger = get_logger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run analysis pipeline (Stage 02)")
    parser.add_argument(
        "--project",
        default="project",
        help="Project name in projects/ directory (default: project)",
    )
    args = parser.parse_args()

    log_header(f"STAGE 02: Run Analysis (Project: {args.project})", logger)
    log_live_resource_usage("Analysis stage start", logger)

    repo_root = Path(__file__).resolve().parents[2]
    try:
        scripts = discover_analysis_scripts(repo_root, args.project)
        if not scripts:
            logger.info("  No analysis scripts found - skipping stage")
            return 0

        logger.info(
            "  Running %d analysis script(s) in lexicographic order: %s",
            len(scripts),
            ", ".join(s.name for s in scripts),
        )

        exit_code = run_analysis_pipeline(scripts, repo_root, args.project)

        if exit_code == 0:
            if verify_analysis_outputs(repo_root, args.project):
                log_success("Analysis complete - ready for PDF rendering", logger)
            else:
                logger.warning("\nAnalysis complete but output verification failed")
        else:
            logger.error("\nAnalysis failed - fix issues and try again")

        return exit_code
    except (ScriptExecutionError, PipelineError) as e:
        logger.error("Pipeline error: %s", e)
        return 1
    except Exception as e:  # noqa: BLE001 — last-line crash containment
        logger.error("Unexpected error: %s", e, exc_info=True)
        return 1
    finally:
        log_live_resource_usage("Analysis stage end", logger)


if __name__ == "__main__":
    sys.exit(main())
