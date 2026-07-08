"""Symlink private lifecycle fonds into the template checkout.

Implementation lives in :mod:`infrastructure.core.sidecar_linking`.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from infrastructure.core.project_paths import find_repo_root
from infrastructure.core.sidecar_linking import (
    LinkSyncResult,
    SidecarLinkConfig,
    is_managed_symlink as _is_managed_symlink,
    resolve_private_root,
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


def sync_active_fond_links(
    repo_root: Path,
    private_root: Path | None = None,
    *,
    prune: bool = True,
    dry_run: bool = False,
) -> LinkSyncResult:
    """Synchronize active fond links."""
    return sync_private_fond_links(repo_root, private_root, prune=prune, dry_run=dry_run)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m infrastructure.fonds.linking",
        description="Symlink lifecycle fonds from the private sidecar into the template checkout.",
    )
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--private-root", type=Path, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-prune", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    ns = _build_parser().parse_args(argv)
    repo_root = ns.repo_root or find_repo_root()
    result = sync_private_fond_links(
        repo_root,
        ns.private_root,
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


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
