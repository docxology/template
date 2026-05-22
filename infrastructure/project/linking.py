"""Symlink ``active/`` projects from the private repo into ``projects/``.

The private companion repo (default: the sibling ``<repo_root.parent>/projects``,
i.e. ``docxology/projects``) holds real work in three lifecycle folders:

- ``active/``  — symlinked into ``<repo_root>/projects/`` and rendered every run
- ``passive/`` — backburner; never linked, never auto-run
- ``archive/`` — retired; never linked

Because ``projects/`` is a namespace-package directory on the pythonpath, a
symlink ``projects/<name>`` -> ``<private>/active/<name>`` resolves transparently
for imports, discovery (:func:`infrastructure.project.discovery.discover_projects`),
validation, and rendering — *as if* the project were a native child of
``projects/``. Execution stays inside the template checkout, so ``infrastructure/``
resolves natively and no git submodule / vendored copy is needed.

Safety invariants (never violated):

- Only symlinks whose resolved target lives **inside** the private root are
  "managed". A real directory or an unmanaged symlink is never unlinked or
  overwritten.
- The two canonical exemplars (``template_code_project``,
  ``template_prose_project``) and any ``*.md`` file are never touched.
- No-op (and no error) when the private repo is absent — a public-only checkout
  (CI, fresh clone) behaves exactly as it did before this module existed.
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass, field
from pathlib import Path

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)

#: Real directories under ``projects/`` that must never be managed as symlinks.
PROTECTED_NAMES: frozenset[str] = frozenset({"template_code_project", "template_prose_project"})
#: Subdirectory of the private root whose children are linked into ``projects/``.
ACTIVE_SUBDIR = "active"
#: The full lifecycle signature that identifies the private companion repo.
LIFECYCLE_SUBDIRS = ("active", "passive", "archive")
#: Optional one-line config file (gitignored) overriding the private root path.
CONFIG_FILENAME = ".private_projects_root"
#: Environment variable (highest precedence) for the private root path.
ENV_VAR = "TEMPLATE_PRIVATE_PROJECTS_ROOT"
#: When set (any non-empty value), the orchestration CLI skips auto link-sync.
SKIP_ENV_VAR = "TEMPLATE_SKIP_LINK_SYNC"


@dataclass
class LinkSyncResult:
    """Outcome of a :func:`sync_active_links` call (all names are basenames)."""

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
    stricter bar — it must contain the full ``active/``+``passive/``+``archive/``
    lifecycle signature — so a coincidental sibling ``projects/active/`` on
    another developer's machine or a CI runner can never be mistaken for the
    private companion repo and silently linked into the public tree.

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


def _active_sources(private_root: Path) -> list[Path]:
    """Return the directories under ``<private_root>/active/`` (sorted, no hidden)."""
    active_dir = private_root / ACTIVE_SUBDIR
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


def is_managed_symlink(path: Path, private_root: Path) -> bool:
    """True iff *path* is a symlink the syncer manages.

    A managed link is one that resolves into the private root's ``active/``
    subtree — the *only* place :func:`sync_active_links` ever points links. Real
    directories (``is_symlink`` False), foreign symlinks, and deliberate user
    links into ``passive/``/``archive/`` all return ``False``, so pruning and
    repointing can never touch a link the syncer did not create.
    """
    if not path.is_symlink():
        return False
    target = _safe_resolve(path)
    active_root = (private_root / ACTIVE_SUBDIR).resolve()
    try:
        target.relative_to(active_root)
    except ValueError:
        return False
    return True


def sync_active_links(
    repo_root: Path,
    private_root: Path | None = None,
    *,
    prune: bool = True,
    dry_run: bool = False,
) -> LinkSyncResult:
    """Make ``projects/`` mirror the private repo's ``active/`` folder via symlinks.

    For each directory under ``<private_root>/active/`` a symlink
    ``<repo_root>/projects/<name>`` is created (or repointed) to it. When
    *prune* is true, managed symlinks whose source has left ``active/`` (moved
    to ``passive/``/``archive/`` or deleted) are removed.

    The two canonical exemplars and any real path are never overwritten or
    removed (recorded under ``skipped``). When no private root is found the
    call is a no-op returning an empty result.

    Args:
        repo_root: Template repository root.
        private_root: Override for the private root (default: auto-resolve).
        prune: Remove managed symlinks no longer backed by an ``active/`` source.
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

    projects_dir = repo_root / "projects"
    if not dry_run:
        projects_dir.mkdir(parents=True, exist_ok=True)
    elif not projects_dir.exists():
        # Nothing on disk to compare against in a dry run.
        wanted_preview = {s.name for s in _active_sources(private_root)}
        result.created.extend(sorted(wanted_preview - PROTECTED_NAMES))
        return result

    wanted: dict[str, Path] = {src.name: src.resolve() for src in _active_sources(private_root)}

    for name, src in wanted.items():
        target = projects_dir / name
        if name in PROTECTED_NAMES:
            result.skipped.append(f"{name} (protected exemplar)")
            continue
        if target.is_symlink():
            if _safe_resolve(target) == src:
                continue  # already correct — idempotent
            if is_managed_symlink(target, private_root):
                # A managed link (points into active/) at a stale target — repoint.
                if not dry_run:
                    target.unlink()
                    target.symlink_to(src)
                result.updated.append(name)
            else:
                # A foreign/unmanaged symlink sharing the name — never clobber it.
                result.skipped.append(f"{name} (unmanaged symlink)")
                logger.warning("link-sync: %s is an unmanaged symlink; left untouched", name)
        elif target.exists():
            # A real file/dir with the same name — never overwrite it.
            result.skipped.append(f"{name} (real path exists)")
            logger.warning("link-sync: %s shadows active source; left untouched", name)
        else:
            if not dry_run:
                target.symlink_to(src)
            result.created.append(name)

    if prune:
        for child in sorted(projects_dir.iterdir()):
            if child.name in wanted or child.name in PROTECTED_NAMES:
                continue
            try:
                if is_managed_symlink(child, private_root):
                    if not dry_run:
                        child.unlink()
                    result.removed.append(child.name)
            except OSError as exc:  # one bad link must not abort the whole sync
                logger.warning("link-sync: could not prune %s: %s", child.name, exc)

    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m infrastructure.project.linking",
        description=(
            "Symlink active/ projects from the private docxology/projects repo "
            "into projects/ so run.sh renders them as native projects."
        ),
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
    result = sync_active_links(
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
