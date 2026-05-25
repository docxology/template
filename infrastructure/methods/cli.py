"""CLI for methods orchestration plans."""

from __future__ import annotations

import argparse
import json
import logging
from collections.abc import Sequence
from pathlib import Path

from infrastructure.methods.orchestration import (
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
    plan.add_argument("--project", required=True, help="Project name under projects/.")
    plan.add_argument("--projects-dir", default="projects", help="Projects directory relative to repo root.")
    plan.add_argument("--format", choices=("json", "markdown"), default="markdown")
    plan.add_argument("--check", action="store_true", help="Exit non-zero when validation errors exist.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the methods orchestration CLI."""
    args = build_parser().parse_args(argv)
    if args.command == "plan":
        logging.getLogger("infrastructure.core.pipeline.dag").setLevel(logging.WARNING)
        plan = build_methods_orchestration_plan(
            args.repo_root,
            args.project,
            projects_dir=args.projects_dir,
        )
        issues = validate_methods_orchestration_plan(plan, repo_root=args.repo_root)
        if args.format == "json":
            payload = plan.to_dict()
            payload["issues"] = [issue.to_dict() for issue in issues]
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(render_methods_orchestration_markdown(plan), end="")
            if issues:
                print("\n## Issues\n")
                for issue in issues:
                    print(f"- `{issue.severity}` `{issue.code}` `{issue.path}`: {issue.message}")
        if args.check and any(issue.severity == "error" for issue in issues):
            return 1
    return 0
