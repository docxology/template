"""Generic sidecar lifecycle symlink sync for template checkouts."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class SidecarLinkConfig:
    protected_names: frozenset[str]
    lifecycle_subdirs: tuple[str, ...]
    required_private_root_subdirs: tuple[str, ...]
    lifecycle_link_dirs: dict[str, str]
    config_filename: str
    env_var: str
    skip_env_var: str
    ignored_lifecycle_entry_names: frozenset[str] = frozenset({"output"})


@dataclass
class LinkSyncResult:
    created: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    private_root: Path | None = None

    @property
    def changed(self) -> bool:
        return bool(self.created or self.updated or self.removed)

    def summary(self) -> str:
        if self.private_root is None:
            return "link-sync: no private projects root found (no-op)"
        return (
            f"link-sync @ {self.private_root}: "
            f"{len(self.created)} created, {len(self.updated)} updated, "
            f"{len(self.removed)} removed, {len(self.skipped)} skipped"
        )


def resolve_private_root(repo_root: Path, config: SidecarLinkConfig) -> Path | None:
    repo_root = Path(repo_root)
    candidates: list[tuple[Path, bool]] = []
    env = os.environ.get(config.env_var)
    if env:
        candidates.append((Path(os.path.expanduser(os.path.expandvars(env))), False))
    config_path = repo_root / config.config_filename
    if config_path.is_file():
        line = config_path.read_text(encoding="utf-8").strip()
        if line:
            candidates.append((Path(os.path.expanduser(os.path.expandvars(line))), False))
    candidates.append((repo_root.parent / "projects", True))
    for cand, require_full in candidates:
        if not any((cand / sub).is_dir() for sub in config.lifecycle_subdirs):
            continue
        if require_full and not all((cand / sub).is_dir() for sub in config.required_private_root_subdirs):
            continue
        return cand.resolve()
    return None


def _source_dirs(private_root: Path, lifecycle_subdir: str, config: SidecarLinkConfig) -> list[tuple[str, Path]]:
    """Return ``(relative_name, path)`` pairs for projects under a lifecycle folder.

    A direct child directory is a project, addressed by its bare name. A child
    directory whose name starts with ``_`` is a category grouping — its direct
    children are the actual projects, addressed as ``"<category>/<name>"``.
    Category nesting is exactly one level deep; a category's children are
    never themselves treated as categories. The leading underscore also sorts
    category groupings ahead of plain lowercase project names in a listing.
    """
    lifecycle_dir = private_root / lifecycle_subdir
    if not lifecycle_dir.is_dir():
        return []
    sources: list[tuple[str, Path]] = []
    for child in sorted(lifecycle_dir.iterdir()):
        if child.name in config.ignored_lifecycle_entry_names or not child.is_dir():
            continue
        if child.name.startswith("_"):
            for grandchild in sorted(child.iterdir()):
                if grandchild.name.startswith(".") or grandchild.name in config.ignored_lifecycle_entry_names:
                    continue
                if not grandchild.is_dir():
                    continue
                sources.append((f"{child.name}/{grandchild.name}", grandchild))
            continue
        if child.name.startswith("."):
            continue
        sources.append((child.name, child))
    return sources


def _safe_resolve(path: Path) -> Path:
    """Resolve *path*, tolerating broken links and symlink loops.

    ``Path.resolve()`` raises ``RuntimeError`` on a symlink loop (and, rarely,
    ``OSError``); ``os.path.realpath`` collapses a loop to a path without
    raising. We must never let a stray loop link under ``projects/`` crash the
    whole CLI, so all resolution goes through here.
    """
    try:
        return path.resolve()
    except (OSError, RuntimeError):
        return Path(os.path.realpath(path))


def _raw_symlink_target(path: Path) -> Path | None:
    """Return the absolute raw target path for a symlink without resolving chains."""
    if not path.is_symlink():
        return None
    raw = Path(os.readlink(path))
    if raw.is_absolute():
        return raw
    return (path.parent / raw).resolve()


def _repo_relative(path: Path, repo_root: Path) -> str:
    """Return a stable POSIX-style path for reporting."""
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _lifecycle_for_link(path: Path, config: SidecarLinkConfig) -> str | None:
    """Infer the expected private lifecycle from a local mirror path.

    Mirror directories are nested (``projects/active``, ``projects/working``,
    …), so a managed symlink sits at ``projects/<lifecycle>/<name>`` or, under
    a category grouping, ``projects/<lifecycle>/_<category>/<name>``. Match on
    the trailing path segments of the symlink's parent (or grandparent, for a
    category-nested link) against each mapped mirror directory.
    """
    parent_parts = path.parent.parts
    for lifecycle, link_dir in config.lifecycle_link_dirs.items():
        link_parts = Path(link_dir).parts
        if parent_parts[-len(link_parts) :] == link_parts:
            return lifecycle
        if (
            len(parent_parts) > len(link_parts)
            and parent_parts[-1].startswith("_")
            and parent_parts[-len(link_parts) - 1 : -1] == link_parts
        ):
            return lifecycle
    return None


def is_managed_symlink(path: Path, private_root: Path, config: SidecarLinkConfig) -> bool:
    """True iff *path* is a symlink the syncer manages.

    A managed link points at the private lifecycle subtree expected for its
    local mirror directory:

    - ``projects/active/*``    resolves into ``private/active/*``
    - ``projects/working/*``   resolves into ``private/working/*``
    - ``projects/ongoing/*``   resolves into ``private/ongoing/*``
    - ``projects/published/*`` resolves into ``private/published/*``
    - ``projects/archive/*``   resolves into ``private/archive/*``
    - ``projects/other/*``     resolves into ``private/other/*``

    Real directories (``is_symlink`` False), foreign symlinks, and deliberate
    user links into a different lifecycle all return ``False``, so pruning and
    repointing can never touch a link the syncer did not create.
    """
    if not path.is_symlink():
        return False
    lifecycle = _lifecycle_for_link(path, config)
    if lifecycle is None:
        return False
    lifecycle_root = (private_root / lifecycle).resolve()
    for target in (_raw_symlink_target(path), _safe_resolve(path)):
        if target is None:
            continue
        try:
            target.relative_to(lifecycle_root)
            return True
        except ValueError:
            continue
    return False


def _symlink_points_to(path: Path, expected: Path) -> bool:
    """Return whether *path* points directly at the expected lifecycle entry."""
    raw = _raw_symlink_target(path)
    return raw == expected


def _sync_lifecycle_links(
    repo_root: Path,
    private_root: Path,
    lifecycle_subdir: str,
    link_dir_name: str,
    config: SidecarLinkConfig,
    result: LinkSyncResult,
    *,
    prune: bool,
    dry_run: bool,
) -> None:
    """Synchronize one lifecycle folder into one local mirror directory."""
    link_dir = repo_root / link_dir_name
    if not dry_run:
        link_dir.mkdir(parents=True, exist_ok=True)

    sources = _source_dirs(private_root, lifecycle_subdir, config)
    wanted: dict[str, Path] = dict(sources)

    if dry_run and not link_dir.exists():
        for name in sorted(wanted):
            if name in config.protected_names:
                result.skipped.append(f"{link_dir_name}/{name} (protected exemplar)")
            else:
                result.created.append(f"{link_dir_name}/{name}")
        return

    for name, src in wanted.items():
        target = link_dir / name
        display = _repo_relative(target, repo_root)
        if name in config.protected_names:
            result.skipped.append(f"{display} (protected exemplar)")
            continue
        if target.is_symlink():
            if _symlink_points_to(target, src):
                continue  # already correct — idempotent
            if is_managed_symlink(target, private_root, config) or _safe_resolve(target) == src.resolve():
                # A managed link at a stale target — repoint.
                if not dry_run:
                    target.unlink()
                    target.symlink_to(src)
                result.updated.append(display)
            else:
                # A foreign/unmanaged symlink sharing the name — never clobber it.
                result.skipped.append(f"{display} (unmanaged symlink)")
                logger.warning("link-sync: %s is an unmanaged symlink; left untouched", display)
        elif target.exists():
            # A real file/dir with the same name — never overwrite it.
            result.skipped.append(f"{display} (real path exists)")
            logger.warning("link-sync: %s shadows private source; left untouched", display)
        else:
            if not dry_run:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.symlink_to(src)
            result.created.append(display)

    if prune and link_dir.exists():
        _prune_lifecycle_dir(link_dir, wanted, private_root, config, result, repo_root, dry_run=dry_run)


def _prune_lifecycle_dir(
    dir_path: Path,
    wanted: dict[str, Path],
    private_root: Path,
    config: SidecarLinkConfig,
    result: LinkSyncResult,
    repo_root: Path,
    *,
    dry_run: bool,
    name_prefix: str = "",
) -> bool:
    """Remove managed links under *dir_path* no longer present in *wanted*.

    Descends one level into category directories (name starting with ``_``)
    so nested ``_<category>/<name>`` entries are pruned the same as flat ones.
    A category directory is only ``rmdir()``-ed once it is left empty *by this
    prune* (i.e. it held at least one managed link that got removed) — an
    unmanaged real ``_``-prefixed directory a user created (empty or not) is
    never touched, preserving the "never unlink/remove a real directory"
    invariant.

    Returns whether anything was actually removed under *dir_path*.
    """
    removed_any = False
    for child in sorted(dir_path.iterdir()):
        rel_name = f"{name_prefix}{child.name}"
        if child.is_dir() and not child.is_symlink() and child.name.startswith("_"):
            child_removed_any = _prune_lifecycle_dir(
                child, wanted, private_root, config, result, repo_root, dry_run=dry_run, name_prefix=f"{rel_name}/"
            )
            removed_any = removed_any or child_removed_any
            if not dry_run and child_removed_any and not any(child.iterdir()):
                child.rmdir()
            continue
        if rel_name in wanted or child.name in config.protected_names:
            continue
        display = _repo_relative(child, repo_root)
        try:
            if is_managed_symlink(child, private_root, config):
                if not dry_run:
                    child.unlink()
                result.removed.append(display)
                removed_any = True
        except OSError as exc:  # one bad link must not abort the whole sync
            logger.warning("link-sync: could not prune %s: %s", display, exc)
    return removed_any


def sync_private_links(
    repo_root: Path,
    config: SidecarLinkConfig,
    private_root: Path | None = None,
    *,
    prune: bool = True,
    dry_run: bool = False,
) -> LinkSyncResult:
    """Mirror private project lifecycle folders via local symlinks.

    For each directory under the private root's lifecycle folders, a matching
    symlink is created (or repointed) in the template checkout:

    - ``active/<name>``    -> ``projects/active/<name>``
    - ``working/<name>``   -> ``projects/working/<name>``
    - ``ongoing/<name>``   -> ``projects/ongoing/<name>``
    - ``published/<name>`` -> ``projects/published/<name>``
    - ``archive/<name>``   -> ``projects/archive/<name>``
    - ``other/<name>``     -> ``projects/other/<name>``

    When *prune* is true, managed symlinks whose source has left its lifecycle
    folder are removed from that lifecycle's local mirror.

    Public canonical exemplars and any real path are never overwritten or
    removed (recorded under ``skipped``). When no private root is found the
    call is a no-op returning an empty result.

    Args:
        repo_root: Template repository root.
        private_root: Override for the private root (default: auto-resolve).
        prune: Remove managed symlinks no longer backed by their lifecycle source.
        dry_run: Report planned actions without mutating the filesystem.

    Returns:
        A :class:`LinkSyncResult` describing what changed (or would change).
    """
    repo_root = Path(repo_root).resolve()
    if private_root is None:
        private_root = resolve_private_root(repo_root, config)
    result = LinkSyncResult(private_root=private_root)
    if private_root is None:
        return result
    private_root = Path(private_root).resolve()
    result.private_root = private_root

    for lifecycle, link_dir in config.lifecycle_link_dirs.items():
        _sync_lifecycle_links(
            repo_root,
            private_root,
            lifecycle,
            link_dir,
            config,
            result,
            prune=prune,
            dry_run=dry_run,
        )

    return result


__all__ = ["LinkSyncResult", "SidecarLinkConfig", "is_managed_symlink", "resolve_private_root", "sync_private_links"]
