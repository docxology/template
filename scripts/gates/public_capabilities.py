#!/usr/bin/env python3
"""Emit and validate the versioned public-exemplar capability manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from infrastructure.project.public_capabilities import audit_public_capabilities  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    """Run the public capability contract gate."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true", help="Emit the complete pretty-printed manifest.")
    output.add_argument(
        "--ci-matrix-json",
        action="store_true",
        help="Emit the compact GitHub Actions include matrix from the same validated manifest.",
    )
    args = parser.parse_args(argv)
    report = audit_public_capabilities(args.repo_root)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    elif args.ci_matrix_json:
        matrix = {"include": [entry.to_dict() for entry in report.ci_matrix]}
        print(json.dumps(matrix, sort_keys=True, separators=(",", ":")))
    else:
        print(
            f"schema={report.schema_version} roster={report.roster_digest} "
            f"ci-python={','.join(report.ci_python_versions)}"
        )
        for project in report.projects:
            status = "OK" if project.passed else "FAIL"
            enabled_formats = [
                name for name in ("pdf", "html", "slides", "docx", "epub") if getattr(project.render_formats, name)
            ]
            print(
                f"{status} {project.project}: package={project.package.name or '<missing>'} "
                f"python={project.package.requires_python or '<missing>'} "
                f"imports={len(project.package.import_targets)} formats={','.join(enabled_formats) or '<none>'} "
                f"hydration={project.hydration.mode} analysis={len(project.analysis.entrypoints)} "
                f"src={project.source_file_count} "
                f"tests={project.test_file_count} scripts={project.script_file_count} "
                f"skips={len(project.skip_contracts)}"
            )
            for issue in project.missing_paths:
                print(f"  missing: {issue}")
            for issue in project.issues:
                print(f"  issue: {issue}")
        for issue in report.issues:
            print(f"REPORT issue: {issue}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
