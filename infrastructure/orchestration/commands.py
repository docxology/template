"""Non-interactive command handlers for orchestration."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from infrastructure.core.project_paths import find_repo_root
from infrastructure.orchestration.discovery import discover_qualified_names, validate_project_slug
from infrastructure.orchestration.link_sync import (
    maybe_sync_all_links,
    print_link_sync_result,
    print_link_sync_results,
)
from infrastructure.orchestration.menu import render_menu
from infrastructure.orchestration.pipeline_runner import (
    MultiProjectInvocation,
    PipelineInvocation,
    PipelineRunner,
)
from infrastructure.orchestration.secure_run import SecureRunOptions, run_secure_pipeline
from infrastructure.project.linking import sync_private_project_links
from infrastructure.project.promotion import load_promotion_attestation


def default_repo_root() -> Path:
    """Locate the repository root through the shared project-path helper."""
    return find_repo_root()


def resolve_repo_root(ns: argparse.Namespace) -> Path:
    """Resolve an explicit repository root or discover the current checkout."""
    return Path(ns.repo_root) if ns.repo_root else default_repo_root()


def maybe_sync_links(repo_root: Path) -> None:
    """Best-effort sync of private lifecycle links for registered domains."""
    try:
        results = maybe_sync_all_links(repo_root)
    except (OSError, RuntimeError) as exc:
        print(f"[link-sync] warning: {exc}", file=sys.stderr)
        return
    print_link_sync_results(results)


def cmd_link_projects(ns: argparse.Namespace) -> int:
    """Synchronize private lifecycle project links."""
    result = sync_private_project_links(
        resolve_repo_root(ns),
        prune=not ns.no_prune,
        dry_run=ns.dry_run,
    )
    print_link_sync_result(result, stream=sys.stdout)
    return 0


def cmd_promotion_check(ns: argparse.Namespace) -> int:
    """Validate one promotion record and emit a secret-free decision."""
    result = load_promotion_attestation(ns.attestation)
    print(json.dumps(result.to_dict(), sort_keys=True))
    return 0


def default_project_name(names: list[str]) -> str:
    """Pick the canonical template project when present, else the first name."""
    canonical = "template_code_project"
    exact = [name for name in names if name == canonical or name.rsplit("/", 1)[-1] == canonical]
    return exact[0] if exact else names[0]


def cmd_pipeline(ns: argparse.Namespace, *, runner_factory: Any = PipelineRunner) -> int:
    """Run one project or route the all-projects compatibility flag."""
    repo_root = resolve_repo_root(ns)
    runner = runner_factory(repo_root=repo_root)
    if ns.all_projects:
        return int(
            runner.run_multi(
                MultiProjectInvocation(
                    skip_infra=ns.skip_infra,
                    skip_llm=ns.skip_llm or ns.core_only,
                )
            )
        )
    if not ns.project:
        names = discover_qualified_names(repo_root)
        if not names:
            print("No projects discovered.", file=sys.stderr)
            return 1
        project = default_project_name(names)
    else:
        project = validate_project_slug(ns.project, repo_root)
    return int(
        runner.run(
            PipelineInvocation(
                project=project,
                skip_infra=ns.skip_infra,
                skip_llm=ns.skip_llm,
                resume=ns.resume,
                core_only=ns.core_only,
                incremental=ns.incremental,
            )
        )
    )


def cmd_multi(ns: argparse.Namespace, *, runner_factory: Any = PipelineRunner) -> int:
    """Run the multi-project pipeline."""
    runner = runner_factory(repo_root=resolve_repo_root(ns))
    return int(
        runner.run_multi(
            MultiProjectInvocation(
                skip_infra=ns.skip_infra,
                skip_llm=ns.skip_llm or ns.core_only,
                run_executive_report=not ns.no_executive_report,
            )
        )
    )


def cmd_secure(ns: argparse.Namespace, *, secure_runner: Any = run_secure_pipeline) -> int:
    """Run secure pipeline orchestration with explicit option mapping."""
    if getattr(ns, "deterministic", False):
        os.environ["STEGANOGRAPHY_DETERMINISTIC"] = "1"
    return int(
        secure_runner(
            resolve_repo_root(ns),
            SecureRunOptions(
                project=ns.project,
                steganography_only=ns.steganography_only,
                skip_infra=ns.skip_infra,
                core_only=ns.core_only,
                resume=ns.resume,
                validate_kmyth=ns.validate_kmyth,
            ),
        )
    )


def cmd_menu(ns: argparse.Namespace) -> int:
    """Render the menu without entering the interactive loop."""
    repo_root = resolve_repo_root(ns)
    project = ns.project
    if project is None:
        names = discover_qualified_names(repo_root)
        project = names[0] if names else "(none)"
    print(render_menu(project))
    return 0


def cmd_list_projects(ns: argparse.Namespace) -> int:
    """List qualified project names."""
    for name in discover_qualified_names(resolve_repo_root(ns)):
        print(name)
    return 0


__all__ = [
    "cmd_link_projects",
    "cmd_list_projects",
    "cmd_menu",
    "cmd_multi",
    "cmd_pipeline",
    "cmd_promotion_check",
    "cmd_secure",
    "default_project_name",
    "default_repo_root",
    "maybe_sync_links",
    "resolve_repo_root",
]
