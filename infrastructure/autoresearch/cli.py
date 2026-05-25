"""Command-line interface for AutoResearch readiness checks."""

from __future__ import annotations

import argparse
from pathlib import Path

from infrastructure.autoresearch.planner import build_autoresearch_plan
from infrastructure.autoresearch.reports import (
    write_autoresearch_plan,
    write_autoresearch_report,
    write_autoresearch_review_packet,
    write_autoresearch_summary,
    write_benchmark_scores,
)
from infrastructure.autoresearch.validation import validate_autoresearch_plan


def main(argv: list[str] | None = None) -> int:
    """Run the AutoResearch CLI."""
    parser = argparse.ArgumentParser(description="Validate deterministic AutoResearch readiness")
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan_parser = subparsers.add_parser("plan", help="Write the composed AutoResearch plan JSON")
    _add_project_args(plan_parser)

    validate_parser = subparsers.add_parser("validate", help="Validate a project readiness plan")
    _add_project_args(validate_parser)
    validate_parser.add_argument("--fail-on-issues", action="store_true", help="Exit nonzero when any issue exists")

    review_parser = subparsers.add_parser("review-packet", help="Write a generic human review packet")
    _add_project_args(review_parser)

    summary_parser = subparsers.add_parser("summarize", help="Write a generic AutoResearch summary")
    _add_project_args(summary_parser)

    benchmark_parser = subparsers.add_parser("benchmark", help="Write benchmark task status from grading outputs")
    _add_project_args(benchmark_parser)

    args = parser.parse_args(argv)
    if args.command == "plan":
        return _plan(args.repo_root, args.project, args.projects_dir)
    if args.command == "validate":
        return _validate(args.repo_root, args.project, args.projects_dir, args.fail_on_issues)
    if args.command == "review-packet":
        return _review_packet(args.repo_root, args.project, args.projects_dir)
    if args.command == "summarize":
        return _summarize(args.repo_root, args.project, args.projects_dir)
    if args.command == "benchmark":
        return _benchmark(args.repo_root, args.project, args.projects_dir)
    return 2


def _add_project_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument("--projects-dir", default="projects", help="Projects directory relative to repo root")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="Repository root")


def _plan(repo_root: Path, project: str, projects_dir: str) -> int:
    plan = build_autoresearch_plan(repo_root, project, projects_dir=projects_dir)
    path = write_autoresearch_plan(plan.project_root, plan)
    print(f"AutoResearch plan JSON: {path}")
    return 0


def _validate(repo_root: Path, project: str, projects_dir: str, fail_on_issues: bool) -> int:
    plan = build_autoresearch_plan(repo_root, project, projects_dir=projects_dir)
    report = validate_autoresearch_plan(plan, plan.project_root)
    json_path, md_path = write_autoresearch_report(plan.project_root, report)
    print(f"AutoResearch readiness JSON: {json_path}")
    print(f"AutoResearch readiness Markdown: {md_path}")
    if fail_on_issues and report.issues:
        return 1
    return 0 if report.valid else 1


def _review_packet(repo_root: Path, project: str, projects_dir: str) -> int:
    plan = build_autoresearch_plan(repo_root, project, projects_dir=projects_dir)
    report = validate_autoresearch_plan(plan, plan.project_root)
    json_path, md_path = write_autoresearch_review_packet(plan.project_root, report)
    print(f"AutoResearch review packet JSON: {json_path}")
    print(f"AutoResearch review packet Markdown: {md_path}")
    return 0


def _summarize(repo_root: Path, project: str, projects_dir: str) -> int:
    plan = build_autoresearch_plan(repo_root, project, projects_dir=projects_dir)
    report = validate_autoresearch_plan(plan, plan.project_root)
    path = write_autoresearch_summary(plan.project_root, report)
    print(f"AutoResearch summary Markdown: {path}")
    return 0


def _benchmark(repo_root: Path, project: str, projects_dir: str) -> int:
    plan = build_autoresearch_plan(repo_root, project, projects_dir=projects_dir)
    path = write_benchmark_scores(plan.project_root, plan)
    print(f"AutoResearch benchmark scores JSON: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
