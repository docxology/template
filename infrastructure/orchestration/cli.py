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

import argparse
import os
import sys
from collections.abc import Sequence
from pathlib import Path

from infrastructure.core.project_paths import find_repo_root
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
from infrastructure.core.pipeline.single_stage import execute_single_stage
from infrastructure.core.pipeline.stage_registry import MENU_KEY_TO_STAGE
from infrastructure.project.discovery import discover_projects
from infrastructure.project.linking import SKIP_ENV_VAR, sync_private_project_links


def _default_repo_root() -> Path:
    """Locate the repository root.

    The orchestration package lives at
    ``<repo_root>/infrastructure/orchestration/``; delegate to the shared
    ``find_repo_root`` helper rather than hard-coding the parent depth here.
    """
    return find_repo_root()


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
    #
    # Two modes are supported:
    #   1. Pipeline + steganography  — requires --project.
    #   2. Steganography-only        — --steganography-only; if no --project,
    #      every discovered project under projects/ is post-processed.
    secure = sub.add_parser(
        "secure",
        help="Run pipeline + steganography (or steganography-only).",
        description=(
            "Secure manuscript pipeline. Runs the standard pipeline for "
            "one project and then applies cryptographic PDF watermarking "
            "(steganography) to every emitted PDF. Use --steganography-only "
            "to skip the pipeline phase and post-process existing PDFs "
            "under projects/<name>/output/pdf/ (or output/<name>/pdf/)."
        ),
        epilog=(
            "Examples:\n"
            "  ./secure_run.sh --project my_project\n"
            "      Full pipeline + steganography for one project.\n"
            "\n"
            "  ./secure_run.sh --project my_project --core-only\n"
            "      Pipeline without LLM stages, then steganography.\n"
            "\n"
            "  ./secure_run.sh --steganography-only --project my_project\n"
            "      Skip the pipeline; only post-process one project's PDFs.\n"
            "\n"
            "  ./secure_run.sh --steganography-only\n"
            "      Skip the pipeline; post-process every discovered project.\n"
            "\n"
            "  ./secure_run.sh --deterministic --project my_project\n"
            "      Pin embedded build timestamp to `git log -1 --format=%cI`\n"
            "      so two consecutive runs produce byte-identical PDFs."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    secure.add_argument(
        "--project",
        required=False,
        help=(
            "Project slug under projects/. Required for the pipeline phase; "
            "optional with --steganography-only (omit to sweep all projects)."
        ),
    )
    secure.add_argument(
        "--steganography-only",
        action="store_true",
        help=(
            "Skip the pipeline phase and only run steganography on existing "
            "PDFs. Use after a prior pipeline run to re-apply or refresh "
            "watermarks without re-rendering."
        ),
    )
    secure.add_argument(
        "--skip-infra",
        action="store_true",
        help="Skip Layer-1 infrastructure tests during the pipeline phase.",
    )
    secure.add_argument(
        "--core-only",
        action="store_true",
        help="Run the 8-stage core pipeline (no LLM review / translations).",
    )
    secure.add_argument(
        "--resume",
        action="store_true",
        help="Resume the pipeline from the last checkpoint.",
    )
    secure.add_argument(
        "--deterministic",
        action="store_true",
        help=(
            "Pin steganography build timestamp to the latest commit's "
            "author date (sets STEGANOGRAPHY_DETERMINISTIC=1) so two "
            "consecutive runs emit byte-identical PDFs."
        ),
    )

    # 'menu' subcommand (diagnostic only)
    menu_p = sub.add_parser("menu", help="Render the interactive menu.")
    menu_p.add_argument("--project", default=None)

    # 'list-projects' subcommand
    sub.add_parser("list-projects", help="List discovered projects, one per line.")

    # 'link-projects' subcommand — explicit sync of private lifecycle projects.
    link = sub.add_parser(
        "link-projects",
        help="Symlink private lifecycle projects into local mirrors.",
    )
    link.add_argument("--dry-run", action="store_true", help="Report without changing anything.")
    link.add_argument("--no-prune", action="store_true", help="Keep stale managed links.")

    return parser


# --- helpers ---------------------------------------------------------------


def _resolve_repo_root(ns: argparse.Namespace) -> Path:
    return Path(ns.repo_root) if ns.repo_root else _default_repo_root()


def _maybe_sync_links(repo_root: Path) -> None:
    """Best-effort: sync private lifecycle project symlinks.

    Runs on every CLI invocation so ``run.sh`` renders active projects as native
    and keeps working/published/archive/other projects visible in non-rendered
    mirrors.
    Deliberately non-fatal: a missing/unreadable private repo must never break
    the pipeline, so failures print a visible warning (not silently swallowed)
    and the CLI continues. Disable with ``$TEMPLATE_SKIP_LINK_SYNC`` or when no
    private root is present (the call is then a pure no-op).
    """
    if os.environ.get(SKIP_ENV_VAR):
        return
    try:
        result = sync_private_project_links(repo_root)
    except (OSError, RuntimeError) as exc:  # fs hiccup / symlink loop — surface, don't crash CLI
        print(f"[link-sync] warning: {exc}", file=sys.stderr)
        return
    if result.changed:
        print(f"[link-sync] {result.summary()}", file=sys.stderr)


def _cmd_link_projects(ns: argparse.Namespace) -> int:
    repo_root = _resolve_repo_root(ns)
    result = sync_private_project_links(
        repo_root,
        prune=not ns.no_prune,
        dry_run=ns.dry_run,
    )
    print(result.summary())
    for name in result.created:
        print(f"  + {name}")
    for name in result.updated:
        print(f"  ~ {name}")
    for name in result.removed:
        print(f"  - {name}")
    for name in result.skipped:
        print(f"  . {name}")
    return 0


def _default_project_name(names: list[str]) -> str:
    """Pick the canonical template project when present, else the first name.

    This mirrors the behaviour of the interactive menu in ``_interactive``,
    which always displays the exemplar project first (sorted list).
    """
    canon = "template_code_project"
    if canon in names:
        return canon
    return names[0]


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
        # Default to the canonical template project if present (parity with
        # run.sh interactive menu), otherwise fall back to the first
        # discovered project alphabetically.
        names = discover_qualified_names(repo_root)
        if not names:
            print("No projects discovered.", file=sys.stderr)
            return 1
        project = _default_project_name(names)
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
    # --deterministic is honoured by infrastructure.steganography.config at
    # call time (not import time), so setting the env var here propagates
    # to the downstream processor without touching the shell wrapper.
    if getattr(ns, "deterministic", False):
        os.environ["STEGANOGRAPHY_DETERMINISTIC"] = "1"
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
        project = names[0] if names else "(none)"
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
    current = qualified[0]

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

        if raw in {"q", "Q"}:
            return 0
        if raw in {"p", "P"}:
            picked = select_project_interactive(
                projects,
                current=current,
                reader=reader,
                writer=sys.stdout,
            )
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
            # Sole "All projects core (fast)" — exit the menu loop after the
            # detailed end-of-run report is printed, regardless of pass/fail.
            # The user does not want the menu redrawn after option d.
            if len(keys) == 1 and key == "d":
                if rc != 0:
                    print(f"Last operation exited with code {rc}", file=sys.stderr)
                return rc
            if rc != 0:
                print(f"Last operation exited with code {rc}", file=sys.stderr)
                break


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
    if key in MENU_KEY_TO_STAGE:
        stage = MENU_KEY_TO_STAGE[key]
        if stage_runner is not None:
            return stage_runner(stage, project, repo_root)
        return execute_single_stage(stage, project, repo_root)
    return 1


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point. Returns process exit code."""
    parser = build_parser()
    ns = parser.parse_args(argv)

    # Auto-sync the private repo's lifecycle projects into local symlink
    # mirrors. The explicit `link-projects` command does its own sync, so skip
    # it here.
    if ns.command != "link-projects":
        _maybe_sync_links(_resolve_repo_root(ns))

    if ns.command is None:
        # No subcommand → interactive menu (parity with bare ./run.sh)
        return _interactive(_resolve_repo_root(ns))

    dispatch = {
        "pipeline": _cmd_pipeline,
        "multi": _cmd_multi,
        "secure": _cmd_secure,
        "menu": _cmd_menu,
        "list-projects": _cmd_list_projects,
        "link-projects": _cmd_link_projects,
    }
    return dispatch[ns.command](ns)


if __name__ == "__main__":  # pragma: no cover - module entry point
    raise SystemExit(main())
