"""Symlink private lifecycle projects into the template checkout.

The private companion repo (default: the sibling ``<repo_root.parent>/projects``,
i.e. ``docxology/projects``) holds real work in five lifecycle folders, each
mirrored into a same-named *typed subfolder* under ``<repo_root>/projects/``:

- ``active/``    — symlinked into ``projects/active/``   and rendered every run
- ``working/``   — symlinked into ``projects/working/``   (not rendered)
- ``published/`` — symlinked into ``projects/published/`` (not rendered)
- ``archive/``   — symlinked into ``projects/archive/``   (not rendered)
- ``other/``     — symlinked into ``projects/other/``     (not rendered)

The public canonical exemplars live in ``projects/templates/`` and are tracked
natively in this repo — they are NOT part of the private companion repo and are
never linked.

Because ``projects/`` is on the pythonpath, a symlink
``projects/active/<name>`` -> ``<private>/active/<name>`` resolves transparently
for imports, discovery (:func:`infrastructure.project.discovery.discover_projects`),
validation, and rendering — *as if* the project were a native child of the typed
subfolder. A private lifecycle entry may itself be a symlink to a sibling
self-versioned repo; the resolved canonical repo remains the single source of
truth. Execution stays inside the template checkout, so ``infrastructure/``
resolves natively and no git submodule / vendored copy is needed.

The ``working``/``published``/``archive``/``other`` mirrors are excluded from the
default render set by :func:`discover_projects` (only ``templates`` and ``active``
are rendered). They make backburner, published, retired, and miscellaneous work
visible to agents and humans without adding those projects to the render set.

Safety invariants (never violated):

- Only symlinks whose raw target points into the matching private lifecycle
  folder are "managed"; resolved-target equality is used only to normalize
  links created by older versions. A real directory or an unmanaged symlink is
  never unlinked or overwritten.
- Public canonical exemplars and any ``*.md`` file are never touched.
- No-op (and no error) when the private repo is absent — a public-only checkout
  (CI, fresh clone) behaves exactly as it did before this module existed.
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass, field
from pathlib import Path

from infrastructure.core.logging.utils import get_logger
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

logger = get_logger(__name__)

#: Bare directory names of the public exemplars that must never be managed as
#: symlinks. ``PUBLIC_PROJECT_NAMES`` are qualified (``templates/<name>``); the
#: linker compares against bare child names, so strip the program prefix.
PROTECTED_NAMES: frozenset[str] = frozenset(Path(name).name for name in PUBLIC_PROJECT_NAMES)
#: Private root lifecycle subdirectories.
ACTIVE_SUBDIR = "active"
WORKING_SUBDIR = "working"
PUBLISHED_SUBDIR = "published"
ARCHIVE_SUBDIR = "archive"
OTHER_SUBDIR = "other"
#: The full lifecycle signature that identifies the private companion repo.
LIFECYCLE_SUBDIRS = (
    ACTIVE_SUBDIR,
    WORKING_SUBDIR,
    PUBLISHED_SUBDIR,
    ARCHIVE_SUBDIR,
    OTHER_SUBDIR,
)
#: Mapping from private lifecycle subdirectory to local template mirror.
#: Each lifecycle folder mirrors into a same-named typed subfolder under
#: ``projects/``. The public ``projects/templates/`` exemplars are tracked
#: natively and never linked.
LIFECYCLE_LINK_DIRS: dict[str, str] = {
    ACTIVE_SUBDIR: "projects/active",
    WORKING_SUBDIR: "projects/working",
    PUBLISHED_SUBDIR: "projects/published",
    ARCHIVE_SUBDIR: "projects/archive",
    OTHER_SUBDIR: "projects/other",
}
#: Optional one-line config file (gitignored) overriding the private root path.
CONFIG_FILENAME = ".private_projects_root"
#: Environment variable (highest precedence) for the private root path.
ENV_VAR = "TEMPLATE_PRIVATE_PROJECTS_ROOT"
#: When set (any non-empty value), the orchestration CLI skips auto link-sync.
SKIP_ENV_VAR = "TEMPLATE_SKIP_LINK_SYNC"


@dataclass
class LinkSyncResult:
    """Outcome of a link-sync call.

    Entries in ``created``, ``updated``, ``removed``, and ``skipped`` are
    repo-relative paths such as ``projects/active/alpha`` or
    ``projects/archive/old_project``.
    """

    created: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    private_root: Path | None = None

    @property
    def changed(self) -> bool:
        """True when the filesystem was (or would be) mutated."""
        return bool(self.created or self.updated or self.removed)

    def summary(self) -> str:
        """One-line human-readable summary."""
        if self.private_root is None:
            return "link-sync: no private projects root found (no-op)"
        return (
            f"link-sync @ {self.private_root}: "
            f"{len(self.created)} created, {len(self.updated)} updated, "
            f"{len(self.removed)} removed, {len(self.skipped)} skipped"
        )


def private_projects_root(repo_root: Path) -> Path | None:
    """Resolve the private projects repo root, or ``None`` when unavailable.

    Resolution order (first match wins):

    1. ``$TEMPLATE_PRIVATE_PROJECTS_ROOT`` (``~`` and ``$VARS`` expanded)
    2. ``<repo_root>/.private_projects_root`` (one-line path, gitignored)
    3. sibling ``<repo_root.parent>/projects``

    Explicit candidates (env, config) are accepted if they contain an
    ``active/`` subdirectory. The **implicit sibling fallback** is held to a
    stricter bar — it must contain the full
    ``active/``+``working/``+``published/``+``archive/``+``other/`` lifecycle
    signature — so a coincidental sibling ``projects/active/`` on another
    developer's machine or a CI runner can never be mistaken for the private
    companion repo and silently linked into the public tree.

    Args:
        repo_root: Template repository root (directory containing ``projects/``).

    Returns:
        Absolute resolved path to the private root, or ``None``.
    """
    repo_root = Path(repo_root)
    # (candidate, require_full_lifecycle_signature)
    candidates: list[tuple[Path, bool]] = []

    env = os.environ.get(ENV_VAR)
    if env:
        candidates.append((Path(os.path.expanduser(os.path.expandvars(env))), False))

    config = repo_root / CONFIG_FILENAME
    if config.is_file():
        line = config.read_text(encoding="utf-8").strip()
        if line:
            candidates.append((Path(os.path.expanduser(os.path.expandvars(line))), False))

    candidates.append((repo_root.parent / "projects", True))

    for cand, require_full in candidates:
        if not (cand / ACTIVE_SUBDIR).is_dir():
            continue
        if require_full and not all((cand / sub).is_dir() for sub in LIFECYCLE_SUBDIRS):
            continue
        return cand.resolve()
    return None


def _source_dirs(private_root: Path, lifecycle_subdir: str) -> list[Path]:
    """Return directories under a private lifecycle folder (sorted, no hidden)."""
    active_dir = private_root / lifecycle_subdir
    if not active_dir.is_dir():
        return []
    sources: list[Path] = []
    for child in sorted(active_dir.iterdir()):
        if child.name.startswith("."):
            continue
        if not child.is_dir():
            continue
        sources.append(child)
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


def _lifecycle_for_link(path: Path) -> str | None:
    """Infer the expected private lifecycle from a local mirror path.

    Mirror directories are nested (``projects/active``, ``projects/working``,
    …), so a managed symlink sits at ``projects/<lifecycle>/<name>``. Match on
    the trailing path segments of the symlink's parent against each mapped
    mirror directory.
    """
    parent_parts = path.parent.parts
    for lifecycle, link_dir in LIFECYCLE_LINK_DIRS.items():
        link_parts = Path(link_dir).parts
        if parent_parts[-len(link_parts) :] == link_parts:
            return lifecycle
    return None


def is_managed_symlink(path: Path, private_root: Path) -> bool:
    """True iff *path* is a symlink the syncer manages.

    A managed link points at the private lifecycle subtree expected for its
    local mirror directory:

    - ``projects/active/*``    resolves into ``private/active/*``
    - ``projects/working/*``   resolves into ``private/working/*``
    - ``projects/published/*`` resolves into ``private/published/*``
    - ``projects/archive/*``   resolves into ``private/archive/*``
    - ``projects/other/*``     resolves into ``private/other/*``

    Real directories (``is_symlink`` False), foreign symlinks, and deliberate
    user links into a different lifecycle all return ``False``, so pruning and
    repointing can never touch a link the syncer did not create.
    """
    if not path.is_symlink():
        return False
    lifecycle = _lifecycle_for_link(path)
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
    result: LinkSyncResult,
    *,
    prune: bool,
    dry_run: bool,
) -> None:
    """Synchronize one lifecycle folder into one local mirror directory."""
    link_dir = repo_root / link_dir_name
    if not dry_run:
        link_dir.mkdir(parents=True, exist_ok=True)

    sources = _source_dirs(private_root, lifecycle_subdir)
    wanted: dict[str, Path] = {src.name: src for src in sources}

    if dry_run and not link_dir.exists():
        for name in sorted(wanted):
            if name in PROTECTED_NAMES:
                result.skipped.append(f"{link_dir_name}/{name} (protected exemplar)")
            else:
                result.created.append(f"{link_dir_name}/{name}")
        return

    for name, src in wanted.items():
        target = link_dir / name
        display = _repo_relative(target, repo_root)
        if name in PROTECTED_NAMES:
            result.skipped.append(f"{display} (protected exemplar)")
            continue
        if target.is_symlink():
            if _symlink_points_to(target, src):
                continue  # already correct — idempotent
            if is_managed_symlink(target, private_root) or _safe_resolve(target) == src.resolve():
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
                target.symlink_to(src)
            result.created.append(display)

    if prune and link_dir.exists():
        for child in sorted(link_dir.iterdir()):
            if child.name in wanted or child.name in PROTECTED_NAMES:
                continue
            display = _repo_relative(child, repo_root)
            try:
                if is_managed_symlink(child, private_root):
                    if not dry_run:
                        child.unlink()
                    result.removed.append(display)
            except OSError as exc:  # one bad link must not abort the whole sync
                logger.warning("link-sync: could not prune %s: %s", display, exc)


def sync_private_project_links(
    repo_root: Path,
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
        private_root = private_projects_root(repo_root)
    result = LinkSyncResult(private_root=private_root)
    if private_root is None:
        return result
    private_root = Path(private_root).resolve()
    result.private_root = private_root

    for lifecycle, link_dir in LIFECYCLE_LINK_DIRS.items():
        _sync_lifecycle_links(
            repo_root,
            private_root,
            lifecycle,
            link_dir,
            result,
            prune=prune,
            dry_run=dry_run,
        )

    return result


def sync_active_links(
    repo_root: Path,
    private_root: Path | None = None,
    *,
    prune: bool = True,
    dry_run: bool = False,
) -> LinkSyncResult:
    """Compatibility wrapper for the lifecycle-aware linker.

    Historically this function synced only ``active/`` into ``projects/``. It
    now delegates to :func:`sync_private_project_links`, which mirrors all five
    lifecycle folders (``active``/``working``/``published``/``archive``/``other``)
    into same-named typed subfolders under ``projects/`` — only ``active`` is
    rendered.
    """
    return sync_private_project_links(repo_root, private_root, prune=prune, dry_run=dry_run)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m infrastructure.project.linking",
        description=("Symlink lifecycle projects from the private docxology/projects repo into the template checkout."),
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Template repo root (default: this file's grandparent's parent).",
    )
    parser.add_argument(
        "--private-root",
        type=Path,
        default=None,
        help="Override the private projects root (default: auto-resolve).",
    )
    parser.add_argument("--dry-run", action="store_true", help="Report without changing anything.")
    parser.add_argument("--no-prune", action="store_true", help="Do not remove stale managed links.")
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns process exit code (0 on success)."""
    ns = _build_parser().parse_args(argv)
    repo_root = ns.repo_root or Path(__file__).resolve().parents[2]
    result = sync_private_project_links(
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


if __name__ == "__main__":  # pragma: no cover - module entry point
    raise SystemExit(main())
