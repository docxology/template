"""Registry of link-sync hooks for orchestration entrypoints."""

from __future__ import annotations

import os
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TextIO

from infrastructure.core.sidecar_linking import LinkSyncResult, write_link_sync_deltas
from infrastructure.fonds.linking import SKIP_ENV_VAR as FONDS_SKIP_ENV_VAR
from infrastructure.fonds.linking import sync_private_fond_links
from infrastructure.project.linking import SKIP_ENV_VAR as PROJECTS_SKIP_ENV_VAR
from infrastructure.project.linking import sync_private_project_links
from infrastructure.rules.linking import SKIP_ENV_VAR as RULES_SKIP_ENV_VAR
from infrastructure.rules.linking import sync_private_rule_links
from infrastructure.tools.linking import SKIP_ENV_VAR as TOOLS_SKIP_ENV_VAR
from infrastructure.tools.linking import sync_private_tool_links

LinkSyncHook = Callable[[Path], LinkSyncResult]
_HOOKS: list[LinkSyncHook] = []


def register_link_sync(hook: LinkSyncHook) -> None:
    """Process register link sync."""
    _HOOKS.append(hook)


def registered_link_sync_hooks() -> Sequence[LinkSyncHook]:
    """Process registered link sync hooks."""
    return tuple(_HOOKS)


def _sync_if_enabled(skip_var: str, sync_fn: LinkSyncHook, repo_root: Path) -> LinkSyncResult:
    if os.environ.get(skip_var):
        return LinkSyncResult()
    return sync_fn(repo_root)


def _hook_for(skip_var: str, sync_fn: LinkSyncHook) -> LinkSyncHook:
    """Bind one resource tree's skip variable to its sync function."""

    def hook(repo_root: Path) -> LinkSyncResult:
        return _sync_if_enabled(skip_var, sync_fn, repo_root)

    return hook


def maybe_sync_all_links(repo_root: Path) -> list[LinkSyncResult]:
    """Process maybe sync all links."""
    return [hook(repo_root) for hook in _HOOKS]


def print_link_sync_result(result: LinkSyncResult, *, stream: TextIO | None = None) -> None:
    """Print link sync result to stderr (or *stream*)."""
    out = stream or sys.stderr
    print(f"[link-sync] {result.summary()}", file=out)
    write_link_sync_deltas(result, stream=out)


def print_link_sync_results(results: Sequence[LinkSyncResult], *, stream: TextIO | None = None) -> None:
    """Print link sync results to stdout."""
    for result in results:
        if result.changed:
            print_link_sync_result(result, stream=stream)


#: Resource trees in the order their sync hooks run on every entrypoint.
_LINK_SYNC_SOURCES: tuple[tuple[str, LinkSyncHook], ...] = (
    (PROJECTS_SKIP_ENV_VAR, sync_private_project_links),
    (FONDS_SKIP_ENV_VAR, sync_private_fond_links),
    (RULES_SKIP_ENV_VAR, sync_private_rule_links),
    (TOOLS_SKIP_ENV_VAR, sync_private_tool_links),
)

for _skip_var, _sync_fn in _LINK_SYNC_SOURCES:
    register_link_sync(_hook_for(_skip_var, _sync_fn))

__all__ = [
    "LinkSyncHook",
    "maybe_sync_all_links",
    "print_link_sync_result",
    "print_link_sync_results",
    "register_link_sync",
    "registered_link_sync_hooks",
]
