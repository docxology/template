"""Symlink private lifecycle fonds into the template checkout.

Generic symlink mechanics and the shared ``linking`` command live in
:mod:`infrastructure.core.sidecar_linking`; this module supplies the fonds
pool's :data:`FONDS_LINK_CONFIG` and its thin public wrappers.
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
from infrastructure.fonds.public_scope import PUBLIC_FOND_NAMES

WORKING_SUBDIR = "working"
ARCHIVE_SUBDIR = "archive"
LIFECYCLE_SUBDIRS = (WORKING_SUBDIR, ARCHIVE_SUBDIR)
REQUIRED_PRIVATE_ROOT_SUBDIRS = (WORKING_SUBDIR, ARCHIVE_SUBDIR)
LIFECYCLE_LINK_DIRS: dict[str, str] = {
    WORKING_SUBDIR: "fonds/working",
    ARCHIVE_SUBDIR: "fonds/archive",
}
PROTECTED_NAMES: frozenset[str] = frozenset(Path(name).name for name in PUBLIC_FOND_NAMES)
CONFIG_FILENAME = ".fonds_root"
ENV_VAR = "TEMPLATE_FONDS_ROOT"
SKIP_ENV_VAR = "TEMPLATE_SKIP_FOND_LINK_SYNC"
IGNORED_LIFECYCLE_ENTRY_NAMES: frozenset[str] = frozenset({"output"})
PROG = "python -m infrastructure.fonds.linking"
DESCRIPTION = "Symlink lifecycle fonds from the private sidecar into the template checkout."

FONDS_LINK_CONFIG = SidecarLinkConfig(
    protected_names=PROTECTED_NAMES,
    lifecycle_subdirs=LIFECYCLE_SUBDIRS,
    required_private_root_subdirs=REQUIRED_PRIVATE_ROOT_SUBDIRS,
    lifecycle_link_dirs=LIFECYCLE_LINK_DIRS,
    config_filename=CONFIG_FILENAME,
    env_var=ENV_VAR,
    skip_env_var=SKIP_ENV_VAR,
    ignored_lifecycle_entry_names=IGNORED_LIFECYCLE_ENTRY_NAMES,
)


def private_fonds_root(repo_root: Path) -> Path | None:
    """Return the private fonds root root path."""
    return resolve_private_root(repo_root, FONDS_LINK_CONFIG)


def is_managed_symlink(path: Path, private_root: Path) -> bool:
    """Check whether managed symlink."""
    return _is_managed_symlink(path, private_root, FONDS_LINK_CONFIG)


def sync_private_fond_links(
    repo_root: Path,
    private_root: Path | None = None,
    *,
    prune: bool = True,
    dry_run: bool = False,
) -> LinkSyncResult:
    """Synchronize private fond links."""
    return sync_private_links(
        repo_root,
        FONDS_LINK_CONFIG,
        private_root,
        prune=prune,
        dry_run=dry_run,
    )


def _build_parser() -> argparse.ArgumentParser:
    return build_link_sync_parser(prog=PROG, description=DESCRIPTION)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    return run_link_sync_cli(FONDS_LINK_CONFIG, prog=PROG, description=DESCRIPTION, argv=argv)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
