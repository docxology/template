"""Command-line interface for AutoResearch readiness checks."""

from __future__ import annotations

import argparse
from pathlib import Path

from infrastructure.autoresearch.planner import build_autoresearch_plan
from infrastructure.autoresearch.reports import write_autoresearch_report
from infrastructure.autoresearch.validation import validate_autoresearch_plan


def main(argv: list[str] | None = None) -> int:
    """Run the AutoResearch CLI."""
    parser = argparse.ArgumentParser(description="Validate deterministic AutoResearch readiness")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate a project readiness plan")
    validate_parser.add_argument("--project", required=True, help="Project name")
    validate_parser.add_argument("--projects-dir", default="projects", help="Projects directory relative to repo root")
    validate_parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="Repository root")
    validate_parser.add_argument("--fail-on-issues", action="store_true", help="Exit nonzero when any issue exists")

    args = parser.parse_args(argv)
    if args.command == "validate":
        return _validate(args.repo_root, args.project, args.projects_dir, args.fail_on_issues)
    return 2


def _validate(repo_root: Path, project: str, projects_dir: str, fail_on_issues: bool) -> int:
    plan = build_autoresearch_plan(repo_root, project, projects_dir=projects_dir)
    report = validate_autoresearch_plan(plan, plan.project_root)
    json_path, md_path = write_autoresearch_report(plan.project_root, report)
    print(f"AutoResearch readiness JSON: {json_path}")
    print(f"AutoResearch readiness Markdown: {md_path}")
    if fail_on_issues and report.issues:
        return 1
    return 0 if report.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
