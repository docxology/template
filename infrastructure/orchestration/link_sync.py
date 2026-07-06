"""Registry of link-sync hooks for orchestration entrypoints."""

from __future__ import annotations

import os
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TextIO

from infrastructure.core.sidecar_linking import LinkSyncResult
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
    _HOOKS.append(hook)


def registered_link_sync_hooks() -> Sequence[LinkSyncHook]:
    return tuple(_HOOKS)


def _sync_if_enabled(skip_var: str, sync_fn: LinkSyncHook, repo_root: Path) -> LinkSyncResult:
    if os.environ.get(skip_var):
        return LinkSyncResult()
    return sync_fn(repo_root)


def _sync_projects_if_enabled(repo_root: Path) -> LinkSyncResult:
    return _sync_if_enabled(PROJECTS_SKIP_ENV_VAR, sync_private_project_links, repo_root)


def _sync_fonds_if_enabled(repo_root: Path) -> LinkSyncResult:
    return _sync_if_enabled(FONDS_SKIP_ENV_VAR, sync_private_fond_links, repo_root)


def _sync_rules_if_enabled(repo_root: Path) -> LinkSyncResult:
    return _sync_if_enabled(RULES_SKIP_ENV_VAR, sync_private_rule_links, repo_root)


def _sync_tools_if_enabled(repo_root: Path) -> LinkSyncResult:
    return _sync_if_enabled(TOOLS_SKIP_ENV_VAR, sync_private_tool_links, repo_root)


def maybe_sync_all_links(repo_root: Path) -> list[LinkSyncResult]:
    return [hook(repo_root) for hook in _HOOKS]


def print_link_sync_result(result: LinkSyncResult, *, stream: TextIO | None = None) -> None:
    out = stream or sys.stderr
    print(f"[link-sync] {result.summary()}", file=out)
    for name in result.created:
        print(f"  + {name}", file=out)
    for name in result.updated:
        print(f"  ~ {name}", file=out)
    for name in result.removed:
        print(f"  - {name}", file=out)
    for name in result.skipped:
        print(f"  . {name}", file=out)


def print_link_sync_results(results: Sequence[LinkSyncResult], *, stream: TextIO | None = None) -> None:
    for result in results:
        if result.changed:
            print_link_sync_result(result, stream=stream)


register_link_sync(_sync_projects_if_enabled)
register_link_sync(_sync_fonds_if_enabled)
register_link_sync(_sync_rules_if_enabled)
register_link_sync(_sync_tools_if_enabled)

__all__ = [
    "LinkSyncHook",
    "maybe_sync_all_links",
    "print_link_sync_result",
    "print_link_sync_results",
    "register_link_sync",
    "registered_link_sync_hooks",
]
