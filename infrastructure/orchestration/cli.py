"""Argparse + dispatch for ``python -m infrastructure.orchestration``.

This module is the single entry point that the thin shell wrappers
``run.sh`` and ``secure_run.sh`` exec into.

Subcommands
-----------

- ``(no subcommand)`` — interactive menu (parity with bare ``./run.sh``).
- ``pipeline`` — run a single-project pipeline (``./run.sh --pipeline``).
- ``multi`` — run all-projects orchestration (``./run.sh --all-projects``).
- ``secure`` — secure_run.sh entry point.
- ``menu`` — render the menu to stdout (used for diagnostics).

All subcommands return an integer exit code.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from infrastructure.orchestration.discovery import (
    discover_qualified_names,
    select_project_interactive,
    validate_project_slug,
)
from infrastructure.orchestration.menu import (
    parse_choice_sequence,
    render_menu,
)
from infrastructure.orchestration.pipeline_runner import (
    MultiProjectInvocation,
    PipelineInvocation,
    PipelineRunner,
)
from infrastructure.orchestration.secure_run import (
    SecureRunOptions,
    run_secure_pipeline,
)
from infrastructure.project.discovery import discover_projects


def _default_repo_root() -> Path:
    """Locate the repository root.

    The orchestration package lives at
    ``<repo_root>/infrastructure/orchestration/``, so the repo root is two
    parents up from this file.
    """
    return Path(__file__).resolve().parents[2]


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argparse parser.

    The CLI is deliberately small: one entry point plus a few flags. The
    legacy ``./run.sh --pipeline --core-only`` invocation continues to
    work as long as those flags are forwarded into this parser.
    """
    parser = argparse.ArgumentParser(
        prog="python -m infrastructure.orchestration",
        description="Research project pipeline orchestrator.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root (defaults to the file's grandparent).",
    )

    sub = parser.add_subparsers(dest="command")

    # 'pipeline' subcommand
    pipe = sub.add_parser("pipeline", help="Run a single-project pipeline.")
    pipe.add_argument("--project", required=False, help="Project name.")
    pipe.add_argument("--all-projects", action="store_true")
    pipe.add_argument("--core-only", action="store_true")
    pipe.add_argument("--skip-infra", action="store_true")
    pipe.add_argument("--skip-llm", action="store_true")
    pipe.add_argument("--resume", action="store_true")

    # 'multi' subcommand
    multi = sub.add_parser("multi", help="Run all-projects orchestration.")
    multi.add_argument("--core-only", action="store_true")
    multi.add_argument("--skip-infra", action="store_true")
    multi.add_argument("--skip-llm", action="store_true")
    multi.add_argument(
        "--no-executive-report",
        action="store_true",
        help="Disable the cross-project executive report.",
    )

    # 'secure' subcommand (secure_run.sh entry point)
    secure = sub.add_parser("secure", help="Run pipeline + steganography.")
    secure.add_argument("--project", required=False)
    secure.add_argument("--steganography-only", action="store_true")
    secure.add_argument("--skip-infra", action="store_true")
    secure.add_argument("--core-only", action="store_true")
    secure.add_argument("--resume", action="store_true")

    # 'menu' subcommand (diagnostic only)
    menu_p = sub.add_parser("menu", help="Render the interactive menu.")
    menu_p.add_argument("--project", default=None)

    # 'list-projects' subcommand
    sub.add_parser("list-projects", help="List discovered projects, one per line.")

    return parser


# --- helpers ---------------------------------------------------------------


def _resolve_repo_root(ns: argparse.Namespace) -> Path:
    return Path(ns.repo_root) if ns.repo_root else _default_repo_root()


def _cmd_pipeline(ns: argparse.Namespace) -> int:
    repo_root = _resolve_repo_root(ns)
    runner = PipelineRunner(repo_root=repo_root)
    if ns.all_projects:
        return runner.run_multi(
            MultiProjectInvocation(
                skip_infra=ns.skip_infra,
                skip_llm=ns.skip_llm or ns.core_only,
            )
        )
    if not ns.project:
        # Default to the first discovered project (parity with run.sh
        # picking template_code_project when present).
        names = discover_qualified_names(repo_root)
        if not names:
            print("No projects discovered.", file=sys.stderr)
            return 1
        project = "template_code_project" if "template_code_project" in names else names[0]
    else:
        project = validate_project_slug(ns.project, repo_root)

    return runner.run(
        PipelineInvocation(
            project=project,
            skip_infra=ns.skip_infra,
            skip_llm=ns.skip_llm,
            resume=ns.resume,
            core_only=ns.core_only,
        )
    )


def _cmd_multi(ns: argparse.Namespace) -> int:
    repo_root = _resolve_repo_root(ns)
    runner = PipelineRunner(repo_root=repo_root)
    return runner.run_multi(
        MultiProjectInvocation(
            skip_infra=ns.skip_infra,
            skip_llm=ns.skip_llm or ns.core_only,
            run_executive_report=not ns.no_executive_report,
        )
    )


def _cmd_secure(ns: argparse.Namespace) -> int:
    repo_root = _resolve_repo_root(ns)
    return run_secure_pipeline(
        repo_root,
        SecureRunOptions(
            project=ns.project,
            steganography_only=ns.steganography_only,
            skip_infra=ns.skip_infra,
            core_only=ns.core_only,
            resume=ns.resume,
        ),
    )


def _cmd_menu(ns: argparse.Namespace) -> int:
    repo_root = _resolve_repo_root(ns)
    project = ns.project
    if project is None:
        names = discover_qualified_names(repo_root)
        project = "template_code_project" if "template_code_project" in names else (names[0] if names else "(none)")
    print(render_menu(project))
    return 0


def _cmd_list_projects(ns: argparse.Namespace) -> int:
    repo_root = _resolve_repo_root(ns)
    for name in discover_qualified_names(repo_root):
        print(name)
    return 0


def _interactive(
    repo_root: Path,
    *,
    reader=input,
    runner: PipelineRunner | None = None,
    stage_runner=None,
) -> int:
    """Run the interactive menu loop.

    Args:
        reader: Zero-arg callable that returns the next user input line.
            Production calls pass :func:`input`; tests pass a queue.
        runner: Optional :class:`PipelineRunner` (tests inject a stub).
        stage_runner: Optional stage dispatcher (tests inject a stub).
    """
    if runner is None:
        runner = PipelineRunner(repo_root=repo_root)
    projects = discover_projects(repo_root)
    if not projects:
        print("No projects discovered under projects/", file=sys.stderr)
        return 1

    qualified = [p.qualified_name for p in projects]
    current = "template_code_project" if "template_code_project" in qualified else qualified[0]

    while True:
        print(render_menu(current))
        try:
            raw = reader().strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        if raw in {"q", "Q"}:
            return 0
        if raw in {"p", "P"}:
            picked = select_project_interactive(projects, current=current, reader=reader)
            if picked is None:
                return 0
            if picked != "all":
                current = picked
            continue
        if raw in {"i", "I"}:
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
            rc = _dispatch_menu_key(key, current, repo_root, runner, stage_runner=stage_runner)
            if rc != 0:
                print(f"Last operation exited with code {rc}", file=sys.stderr)
                break
            # Sole "All projects core (fast)" succeeds — show runner summary only,
            # do not redraw the interactive menu (matches ./run.sh option d UX).
            if len(keys) == 1 and key == "d":
                return 0


_STAGE_KEY_MAP: dict[str, str] = {
    "0": "setup",
    "1": "tests",
    "2": "analysis",
    "3": "render_pdf",
    "4": "validate",
    "5": "copy",
    "6": "llm_reviews",
    "7": "llm_translations",
}


def _dispatch_menu_key(
    key: str,
    project: str,
    repo_root: Path,
    runner: PipelineRunner,
    *,
    stage_runner=None,
) -> int:
    """Dispatch a single menu key (used by the interactive loop).

    Args:
        stage_runner: Optional callable ``(stage_key, project, repo_root) -> int``
            used to dispatch single-stage runs. Production callers leave it
            as ``None`` (subprocess dispatch); tests inject a stub.
    """
    if key == "8":
        return runner.run(PipelineInvocation(project=project, core_only=True))
    if key == "9":
        return runner.run(PipelineInvocation(project=project))
    if key == "f":
        return runner.run(PipelineInvocation(project=project, skip_infra=True))
    if key in {"a", "b", "c", "d"}:
        skip_infra = key in {"b", "d"}
        skip_llm = key in {"c", "d"}
        return runner.run_multi(MultiProjectInvocation(skip_infra=skip_infra, skip_llm=skip_llm))
    if key in _STAGE_KEY_MAP:
        if stage_runner is not None:
            return stage_runner(_STAGE_KEY_MAP[key], project, repo_root)
        return _subprocess_stage(_STAGE_KEY_MAP[key], project, repo_root)
    return 1


def _subprocess_stage(stage: str, project: str, repo_root: Path) -> int:  # pragma: no cover
    """Default stage dispatcher — invokes scripts/execute_pipeline.py.

    Excluded from coverage because subprocess invocation requires the full
    pipeline executor to be runnable; it is exercised by smoke tests.
    """
    import subprocess

    cmd = [
        sys.executable,
        str(repo_root / "scripts" / "execute_pipeline.py"),
        "--project",
        project,
        "--stage",
        stage,
    ]
    return subprocess.run(cmd, cwd=str(repo_root), check=False).returncode


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point. Returns process exit code."""
    parser = build_parser()
    ns = parser.parse_args(argv)

    if ns.command is None:
        # No subcommand → interactive menu (parity with bare ./run.sh)
        return _interactive(_resolve_repo_root(ns))

    dispatch = {
        "pipeline": _cmd_pipeline,
        "multi": _cmd_multi,
        "secure": _cmd_secure,
        "menu": _cmd_menu,
        "list-projects": _cmd_list_projects,
    }
    return dispatch[ns.command](ns)


if __name__ == "__main__":  # pragma: no cover - module entry point
    raise SystemExit(main())
