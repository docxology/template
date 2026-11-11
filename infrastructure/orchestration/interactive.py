"""TTY-dependent interactive orchestration loop."""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from infrastructure.core.pipeline.single_stage import execute_single_stage
from infrastructure.orchestration.discovery import select_project_interactive
from infrastructure.orchestration.menu import menu_action, parse_choice_sequence, render_menu
from infrastructure.orchestration.pipeline_runner import (
    MultiProjectInvocation,
    PipelineInvocation,
    PipelineRunner,
)
from infrastructure.project.discovery import discover_projects


def interactive(
    repo_root: Path,
    *,
    reader: Callable[[], str] = input,
    runner: PipelineRunner | None = None,
    stage_runner: Any = None,
) -> int:
    """Run the compatible interactive menu loop."""
    if runner is None:
        runner = PipelineRunner(repo_root=repo_root)
    projects = discover_projects(repo_root)
    if not projects:
        print("No projects discovered under projects/", file=sys.stderr)
        return 1
    current = projects[0].qualified_name

    while True:
        print(render_menu(current))
        print(
            "  Keys: 0-9, a-d, f, p, i, q  |  chain digits (e.g. 234)  |  comma or space  |  p project  i info  q quit",
        )
        print()
        print("Choice: ", end="", flush=True)
        try:
            raw = reader().strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        action = menu_action(raw.lower())
        control = action.control if action is not None else None
        if control == "quit":
            return 0
        if control == "select":
            picked = select_project_interactive(projects, current=current, reader=reader, writer=sys.stdout)
            if picked is None:
                return 0
            if picked != "all":
                current = picked
            continue
        if control == "info":
            print(f"Current project: {current}")
            continue

        try:
            keys = parse_choice_sequence(raw)
        except ValueError as exc:
            print(f"Invalid input: {exc}", file=sys.stderr)
            continue
        if not keys:
            continue

        for key in keys:
            rc = dispatch_menu_key(key, current, repo_root, runner, stage_runner=stage_runner)
            if rc != 0:
                print(f"Last operation exited with code {rc}", file=sys.stderr)
            action = menu_action(key)
            if len(keys) == 1 and action is not None and action.exit_when_alone:
                return rc
            if rc != 0:
                break


def dispatch_menu_key(
    key: str,
    project: str,
    repo_root: Path,
    runner: PipelineRunner,
    *,
    stage_runner: Any = None,
) -> int:
    """Dispatch one interactive menu key."""
    action = menu_action(key)
    if action is None:
        return 1
    if action.section == "pipeline":
        return runner.run(PipelineInvocation(project=project, skip_infra=action.skip_infra, mode=action.mode))
    if action.section == "multi":
        return runner.run_multi(MultiProjectInvocation(skip_infra=action.skip_infra, mode=action.mode))
    if action.stage is not None:
        if stage_runner is not None:
            return int(stage_runner(action.stage, project, repo_root))
        return int(execute_single_stage(action.stage, project, repo_root, mode=action.mode))
    return 1


__all__ = ["dispatch_menu_key", "interactive"]
