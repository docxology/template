"""Registry of link-sync hooks for orchestration entrypoints."""

from __future__ import annotations
import os
from collections.abc import Callable, Sequence
from pathlib import Path
from infrastructure.core.sidecar_linking import LinkSyncResult
from infrastructure.project.linking import SKIP_ENV_VAR, sync_private_project_links

LinkSyncHook = Callable[[Path], LinkSyncResult]
_HOOKS: list[LinkSyncHook] = []


def register_link_sync(hook: LinkSyncHook) -> None:
    _HOOKS.append(hook)


def registered_link_sync_hooks() -> Sequence[LinkSyncHook]:
    return tuple(_HOOKS)


def maybe_sync_all_links(repo_root: Path) -> list[LinkSyncResult]:
    if os.environ.get(SKIP_ENV_VAR):
        return []
    return [hook(repo_root) for hook in _HOOKS]


register_link_sync(sync_private_project_links)
__all__ = ["LinkSyncHook", "maybe_sync_all_links", "register_link_sync", "registered_link_sync_hooks"]
