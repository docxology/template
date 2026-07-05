"""Symlink private lifecycle projects into the template checkout.

The private companion repo (default: the sibling ``<repo_root.parent>/projects``)
mirrors lifecycle folders into typed subfolders under ``<repo_root>/projects/``.
Generic symlink mechanics live in :mod:`infrastructure.core.sidecar_linking`; this
module supplies the template project's ``PROJECT_LINK_CONFIG`` and CLI entrypoint.
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
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

PROTECTED_NAMES: frozenset[str] = frozenset(Path(name).name for name in PUBLIC_PROJECT_NAMES)
ACTIVE_SUBDIR = "active"
WORKING_SUBDIR = "working"
ONGOING_SUBDIR = "ongoing"
PUBLISHED_SUBDIR = "published"
ARCHIVE_SUBDIR = "archive"
OTHER_SUBDIR = "other"
LIFECYCLE_SUBDIRS = (
    ACTIVE_SUBDIR,
    WORKING_SUBDIR,
    ONGOING_SUBDIR,
    PUBLISHED_SUBDIR,
    ARCHIVE_SUBDIR,
    OTHER_SUBDIR,
)
REQUIRED_PRIVATE_ROOT_SUBDIRS = (WORKING_SUBDIR, ARCHIVE_SUBDIR)
LIFECYCLE_LINK_DIRS: dict[str, str] = {
    ACTIVE_SUBDIR: "projects/active",
    WORKING_SUBDIR: "projects/working",
    ONGOING_SUBDIR: "projects/ongoing",
    PUBLISHED_SUBDIR: "projects/published",
    ARCHIVE_SUBDIR: "projects/archive",
    OTHER_SUBDIR: "projects/other",
}
CONFIG_FILENAME = ".private_projects_root"
ENV_VAR = "TEMPLATE_PRIVATE_PROJECTS_ROOT"
SKIP_ENV_VAR = "TEMPLATE_SKIP_LINK_SYNC"
IGNORED_LIFECYCLE_ENTRY_NAMES: frozenset[str] = frozenset({"output"})

PROJECT_LINK_CONFIG = SidecarLinkConfig(
    protected_names=PROTECTED_NAMES,
    lifecycle_subdirs=LIFECYCLE_SUBDIRS,
    required_private_root_subdirs=REQUIRED_PRIVATE_ROOT_SUBDIRS,
    lifecycle_link_dirs=LIFECYCLE_LINK_DIRS,
    config_filename=CONFIG_FILENAME,
    env_var=ENV_VAR,
    skip_env_var=SKIP_ENV_VAR,
    ignored_lifecycle_entry_names=IGNORED_LIFECYCLE_ENTRY_NAMES,
)


def private_projects_root(repo_root: Path) -> Path | None:
    return resolve_private_root(repo_root, PROJECT_LINK_CONFIG)


def is_managed_symlink(path: Path, private_root: Path) -> bool:
    return _is_managed_symlink(path, private_root, PROJECT_LINK_CONFIG)


def sync_private_project_links(
    repo_root: Path,
    private_root: Path | None = None,
    *,
    prune: bool = True,
    dry_run: bool = False,
) -> LinkSyncResult:
    return sync_private_links(
        repo_root,
        PROJECT_LINK_CONFIG,
        private_root,
        prune=prune,
        dry_run=dry_run,
    )


def sync_active_links(
    repo_root: Path,
    private_root: Path | None = None,
    *,
    prune: bool = True,
    dry_run: bool = False,
) -> LinkSyncResult:
    return sync_private_project_links(repo_root, private_root, prune=prune, dry_run=dry_run)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m infrastructure.project.linking",
        description=("Symlink lifecycle projects from the private docxology/projects repo into the template checkout."),
    )
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--private-root", type=Path, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-prune", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    ns = _build_parser().parse_args(argv)
    repo_root = ns.repo_root or find_repo_root()
    result = sync_private_project_links(
        repo_root,
        ns.private_root,
        prune=not ns.no_prune,
        dry_run=ns.dry_run,
    )
    print(result.summary())
    for label, names in [
        ("+", result.created),
        ("~", result.updated),
        ("-", result.removed),
        (".", result.skipped),
    ]:
        for name in names:
            print(f"  {label} {name}")
    return 0


if __name__ == "__main__":  # pragma: no cover - module entry point
    raise SystemExit(main())
