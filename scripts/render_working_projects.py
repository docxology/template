#!/usr/bin/env python3
"""Batch core-pipeline render for projects under ``projects/working/``.

Thin orchestrator: delegates to :mod:`infrastructure.project.working_render`.
Not discovered by ``./run.sh --all-projects``; use this script for WIP audits.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from infrastructure.core.logging.utils import get_logger, log_header  # noqa: E402
from infrastructure.project.working_render import (  # noqa: E402
    ProjectAudit,
    audit_project,
    audit_project_filesystem_only,
    consolidate_audits,
    list_working_projects,
    run_project_pipeline,
    write_audit_report,
)

logger = get_logger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch core pipeline for projects/working/")
    parser.add_argument(
        "--project",
        action="append",
        dest="projects",
        help="Run only these project name(s); default: all under projects/working/",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List projects that would run and exit",
    )
    parser.add_argument(
        "--audit-only",
        action="store_true",
        help="Scan output trees and write audit report without running the pipeline",
    )
    parser.add_argument(
        "--skip-infra",
        action="store_true",
        help="Skip infrastructure smoke on every project (faster resume batches)",
    )
    parser.add_argument(
        "--consolidate",
        type=Path,
        default=None,
        metavar="BATCH_LOG",
        help="Write full audit for all working projects by merging BATCH_LOG Result lines with filesystem scan",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=repo_root,
        help="Repository root (default: parent of scripts/)",
    )
    args = parser.parse_args()
    repo = args.repo_root.resolve()

    names = args.projects if args.projects else list_working_projects(repo)
    if not names:
        logger.error("No projects found under %s", repo / "projects" / "working")
        return 1

    if args.dry_run:
        for name in names:
            print(name)
        return 0

    if args.consolidate is not None:
        log_path = args.consolidate if args.consolidate.is_file() else None
        consolidated = consolidate_audits(repo, log_path)
        json_path, md_path = write_audit_report(repo, consolidated)
        logger.info("Consolidated audit: %s", json_path)
        return 0

    if args.audit_only:
        # Filesystem + PDF-validator only (no pipeline run); rubric lives in infrastructure.
        records = [audit_project_filesystem_only(repo, name) for name in names]
        json_path, md_path = write_audit_report(repo, records)
        logger.info("Audit-only report: %s", json_path)
        logger.info("Summary: %s", md_path)
        return 0

    log_header(f"Working projects batch render ({len(names)} projects)", logger)
    audits: list[ProjectAudit] = []
    any_failed = False

    for index, name in enumerate(names):
        skip_infra = args.skip_infra or index > 0
        logger.info("=== [%d/%d] %s (skip_infra=%s) ===", index + 1, len(names), name, skip_infra)
        try:
            results, duration = run_project_pipeline(repo, name, skip_infra=skip_infra)
        except Exception as exc:
            logger.error("Pipeline crashed for %s: %s", name, exc, exc_info=True)
            audits.append(
                ProjectAudit(
                    name=name,
                    status="FAIL — pipeline",
                    pipeline_success=False,
                    duration_sec=0.0,
                    error_message=str(exc),
                    structure_notes=[],
                )
            )
            any_failed = True
            continue

        audit = audit_project(repo, name, results, duration)
        audits.append(audit)
        if not audit.pipeline_success or not audit.status.startswith("PASS"):
            any_failed = True
        logger.info(
            "Result: %s (%.1fs) top_pdf=%s",
            audit.status,
            audit.duration_sec,
            audit.top_pdf or "none",
        )

    json_path, md_path = write_audit_report(repo, audits)
    logger.info("Audit written: %s", json_path)
    logger.info("Summary: %s", md_path)

    pass_n = sum(1 for audit in audits if audit.status.startswith("PASS"))
    logger.info(
        "Complete: %d PASS, %d PARTIAL, %d FAIL (of %d)",
        pass_n,
        sum(1 for audit in audits if audit.status.startswith("PARTIAL")),
        sum(1 for audit in audits if audit.status.startswith("FAIL")),
        len(audits),
    )
    return 1 if any_failed else 0


if __name__ == "__main__":
    sys.exit(main())
