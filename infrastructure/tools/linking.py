"""Symlink private lifecycle tools into the template checkout.

Generic symlink mechanics and the shared ``linking`` command live in
:mod:`infrastructure.core.sidecar_linking`; this module supplies the tools
pool's :data:`TOOLS_LINK_CONFIG` and its thin public wrappers.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from infrastructure.core.sidecar_linking import (
    LinkSyncResult,
    SidecarLinkConfig,
    build_link_sync_parser,
    is_managed_symlink as _is_managed_symlink,
    resolve_private_root,
    run_link_sync_cli,
    sync_private_links,
)
from infrastructure.tools.public_scope import PUBLIC_TOOL_NAMES

WORKING_SUBDIR = "working"
ARCHIVE_SUBDIR = "archive"
LIFECYCLE_SUBDIRS = (WORKING_SUBDIR, ARCHIVE_SUBDIR)
REQUIRED_PRIVATE_ROOT_SUBDIRS = (WORKING_SUBDIR, ARCHIVE_SUBDIR)
LIFECYCLE_LINK_DIRS: dict[str, str] = {
    WORKING_SUBDIR: "tools/working",
    ARCHIVE_SUBDIR: "tools/archive",
}
PROTECTED_NAMES: frozenset[str] = frozenset(Path(name).name for name in PUBLIC_TOOL_NAMES)
CONFIG_FILENAME = ".tools_root"
ENV_VAR = "TEMPLATE_TOOLS_ROOT"
SKIP_ENV_VAR = "TEMPLATE_SKIP_TOOL_LINK_SYNC"
IGNORED_LIFECYCLE_ENTRY_NAMES: frozenset[str] = frozenset({"output"})
PROG = "python -m infrastructure.tools.linking"
DESCRIPTION = "Symlink lifecycle tools from the private sidecar into the template checkout."

TOOLS_LINK_CONFIG = SidecarLinkConfig(
    protected_names=PROTECTED_NAMES,
    lifecycle_subdirs=LIFECYCLE_SUBDIRS,
    required_private_root_subdirs=REQUIRED_PRIVATE_ROOT_SUBDIRS,
    lifecycle_link_dirs=LIFECYCLE_LINK_DIRS,
    config_filename=CONFIG_FILENAME,
    env_var=ENV_VAR,
    skip_env_var=SKIP_ENV_VAR,
    ignored_lifecycle_entry_names=IGNORED_LIFECYCLE_ENTRY_NAMES,
)


def private_tools_root(repo_root: Path) -> Path | None:
    """Return the private tools root root path."""
    return resolve_private_root(repo_root, TOOLS_LINK_CONFIG)


def is_managed_symlink(path: Path, private_root: Path) -> bool:
    """Check whether managed symlink."""
    return _is_managed_symlink(path, private_root, TOOLS_LINK_CONFIG)


def sync_private_tool_links(
    repo_root: Path,
    private_root: Path | None = None,
    *,
    prune: bool = True,
    dry_run: bool = False,
) -> LinkSyncResult:
    """Synchronize private tool links."""
    return sync_private_links(
        repo_root,
        TOOLS_LINK_CONFIG,
        private_root,
        prune=prune,
        dry_run=dry_run,
    )


def _build_parser() -> argparse.ArgumentParser:
    return build_link_sync_parser(prog=PROG, description=DESCRIPTION)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    return run_link_sync_cli(TOOLS_LINK_CONFIG, prog=PROG, description=DESCRIPTION, argv=argv)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
