"""CLI for methods orchestration plans."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections.abc import Sequence
from pathlib import Path

from infrastructure.core.cli_scaffold import emit_schema
from infrastructure.core.pipeline.definition import PipelineSourceResolutionError
from infrastructure.methods.models import MethodsIssue
from infrastructure.methods.orchestration import (
    audit_methods_projects,
    build_methods_orchestration_plan,
    render_methods_orchestration_markdown,
    validate_methods_orchestration_plan,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the methods orchestration parser."""
    parser = argparse.ArgumentParser(prog="python -m infrastructure.methods")
    sub = parser.add_subparsers(dest="command", required=True)
    plan = sub.add_parser("plan", help="Render a methods orchestration plan.")
    plan.add_argument("--repo-root", type=Path, default=Path("."), help="Repository root.")
    scope = plan.add_mutually_exclusive_group(required=True)
    scope.add_argument("--project", help="Project name under projects/.")
    scope.add_argument("--all-public", action="store_true", help="Audit every canonical public exemplar.")
    plan.add_argument("--projects-dir", default="projects", help="Projects directory relative to repo root.")
    plan.add_argument(
        "--artifact-mode",
        choices=("source", "rendered"),
        default="rendered",
        help="Validate source contracts only or require rendered evidence artifacts.",
    )
    plan.add_argument("--format", choices=("json", "markdown"), default="markdown")
    plan.add_argument(
        "--check",
        action="store_true",
        help="Compatibility flag; validation errors always exit 1.",
    )
    sub.add_parser("schema", help="Print this CLI's parameter schema as JSON and exit.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the methods orchestration CLI."""
    args = build_parser().parse_args(argv)
    if args.command == "schema":
        return emit_schema(build_parser())
    if args.command == "plan":
        logging.getLogger("infrastructure.core.pipeline.dag").setLevel(logging.WARNING)
        try:
            if args.all_public:
                from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

                report = audit_methods_projects(
                    args.repo_root,
                    list(PUBLIC_PROJECT_NAMES),
                    artifact_mode=args.artifact_mode,
                    projects_dir=args.projects_dir,
                )
                if args.format == "json":
                    print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
                else:
                    for project in report.projects:
                        print(render_methods_orchestration_markdown(project.plan), end="")
                        _print_issues(project.issues)
                    print(
                        f"\nAudited {len(report.projects)} project(s): "
                        f"{report.error_count} error(s), {report.warning_count} warning(s)."
                    )
                if not report.passed:
                    return 1
                return 0

            plan = build_methods_orchestration_plan(
                args.repo_root,
                args.project,
                projects_dir=args.projects_dir,
                artifact_mode=args.artifact_mode,
            )
            issues = validate_methods_orchestration_plan(plan, repo_root=args.repo_root)
        except (OSError, PipelineSourceResolutionError, ValueError) as exc:
            print(f"methods configuration error: {exc}", file=sys.stderr)
            return 2
        if args.format == "json":
            payload = plan.to_dict()
            payload["issues"] = [issue.to_dict() for issue in issues]
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(render_methods_orchestration_markdown(plan), end="")
            _print_issues(issues)
        if any(issue.severity == "error" for issue in issues):
            return 1
    return 0


def _print_issues(issues: Sequence[MethodsIssue]) -> None:
    """Render issue-like objects for the Markdown CLI surface."""
    if not issues:
        return
    print("\n## Issues\n")
    for issue in issues:
        print(f"- `{issue.severity}` `{issue.code}` `{issue.path}`: {issue.message}")
