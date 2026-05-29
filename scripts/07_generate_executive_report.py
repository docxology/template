#!/usr/bin/env python3
"""Executive report generation orchestrator (Stage 07, multi-project only)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts import ensure_repo_root_on_path  # noqa: E402

ensure_repo_root_on_path()

from infrastructure.core.logging.utils import get_logger, log_header, log_substep, log_success
from infrastructure.project.discovery import discover_projects
from infrastructure.reporting._executive_health import verify_project_completion
from infrastructure.reporting.multi_project_reporter import generate_multi_project_report
from infrastructure.reporting.output_organizer import OutputOrganizer

logger = get_logger(__name__)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Generate executive report")
    parser.add_argument("--project", help="Ignored — executive reporting runs for all projects")
    parser.parse_args()

    log_header("STAGE 07: Executive Reporting", logger)
    repo_root = Path(__file__).parent.parent
    projects = discover_projects(repo_root)
    if len(projects) <= 1:
        logger.info("Single-project checkout — executive reporting skipped")
        return 0

    completed = [
        project.qualified_name
        for project in projects
        if verify_project_completion(repo_root, project.qualified_name)
    ]
    if not completed:
        logger.error("No projects completed the pipeline successfully")
        return 1

    output_dir = repo_root / "output" / "executive_summary"
    log_substep(f"Generating executive summary for {len(completed)} project(s)...", logger)
    generate_multi_project_report(repo_root, completed, output_dir)

    log_substep("Copying combined PDFs...", logger)
    copied = OutputOrganizer().copy_combined_pdfs(repo_root, output_dir)
    logger.info("Copied %d combined PDF file(s)", copied)

    log_success("Executive reporting complete", logger)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
