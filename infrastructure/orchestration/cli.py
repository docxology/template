"""Compatible facade and dispatch for ``python -m infrastructure.orchestration``."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from typing import Any

from infrastructure.core.cli_scaffold import emit_schema
from infrastructure.orchestration.commands import (
    cmd_link_projects,
    cmd_list_projects,
    cmd_menu,
    cmd_multi,
    cmd_pipeline,
    cmd_promotion_check,
    cmd_secure,
    default_project_name,
    default_repo_root,
    maybe_sync_links,
    resolve_repo_root,
)
from infrastructure.orchestration.interactive import dispatch_menu_key, interactive
from infrastructure.orchestration.parser import build_parser
from infrastructure.orchestration.pipeline_runner import PipelineRunner
from infrastructure.orchestration.secure_run import run_secure_pipeline

# Historical private helper imports are kept as aliases for downstream callers
# and the repository's compatibility tests.
_cmd_link_projects = cmd_link_projects
_cmd_list_projects = cmd_list_projects
_cmd_menu = cmd_menu
_cmd_multi = cmd_multi
_cmd_pipeline = cmd_pipeline
_cmd_promotion_check = cmd_promotion_check
_cmd_secure = cmd_secure
_default_project_name = default_project_name
_default_repo_root = default_repo_root
_dispatch_menu_key = dispatch_menu_key
_interactive = interactive
_maybe_sync_links = maybe_sync_links
_resolve_repo_root = resolve_repo_root


def main(
    argv: Sequence[str] | None = None,
    *,
    runner_factory: Any = PipelineRunner,
    secure_runner: Any = run_secure_pipeline,
    interactive_runner: Any = interactive,
) -> int:
    """Parse, dispatch, and return a stable process exit code."""
    parser = build_parser()
    ns = parser.parse_args(argv)
    if ns.command == "schema":
        return emit_schema(build_parser())
    if ns.command not in {"link-projects", "promotion-check"}:
        maybe_sync_links(resolve_repo_root(ns))
    if ns.command is None:
        return int(interactive_runner(resolve_repo_root(ns)))

    dispatch = {
        "pipeline": lambda args: cmd_pipeline(args, runner_factory=runner_factory),
        "multi": lambda args: cmd_multi(args, runner_factory=runner_factory),
        "secure": lambda args: cmd_secure(args, secure_runner=secure_runner),
        "menu": cmd_menu,
        "list-projects": cmd_list_projects,
        "link-projects": cmd_link_projects,
        "promotion-check": cmd_promotion_check,
    }
    try:
        return dispatch[ns.command](ns)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


__all__ = [
    "build_parser",
    "main",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
