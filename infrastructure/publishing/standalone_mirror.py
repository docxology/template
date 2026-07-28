"""Mirror public exemplars from the monorepo into their standalone repositories.

The monorepo is the render source of truth; each public exemplar also has a
standalone GitHub repository that serves as its publication mirror (see
``docs/guides/publication-runbook.md``). This module keeps those mirrors current.

Two properties are load-bearing, and both were learned by nearly getting them
wrong on 2026-07-28:

**Update-only.** The mirror legitimately holds files the monorepo does not track.
Exemplar ``output/`` is gitignored in the monorepo but published in the mirror —
``template_advanced_literature_review`` tracks 4 output files locally while its
mirror holds 228 — because the runbook says the mirror carries the rendered
artifacts. A sync that replaced the mirror's tracked set would therefore have
deleted 224 published artifacts from that repository alone. The trade this
accepts, stated rather than hidden: a file deleted in the monorepo is NOT removed
from the mirror. Destroying publication evidence is far more costly than leaving
a stale file, so removals stay a deliberate manual act.

**Symlinks are dereferenced.** Some exemplars share source by symlinking into a
sibling exemplar (``template_advanced_literature_review/src/analysis ->
../../template_literature_meta_analysis/src/analysis``). A standalone repository
has no sibling, so copying the link would leave it dangling — which is exactly
why that mirror was missing four entire source trees. Directory symlinks are
expanded into their tracked contents.

The file list always comes from ``git ls-files``, so untracked local noise
(``htmlcov/``, ``dist/``, ``.codegraph``, ``.venv``) can never reach a mirror.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

_REPOSITORY_CODE_RE = re.compile(r"^repository-code:\s*(\S+)", re.MULTILINE)


@dataclass(frozen=True)
class MirrorResult:
    """Outcome of syncing one exemplar into its standalone repository."""

    exemplar: str
    repository: str
    status: str
    added: int = 0
    modified: int = 0
    deleted: int = 0
    commit: str = ""

    @property
    def changed(self) -> int:
        """Total number of files the sync would write."""
        return self.added + self.modified + self.deleted


def _git(args: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(  # noqa: S603 - fixed argv, no shell
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=False
    )
    if check and proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args[:3])} failed in {cwd}: {proc.stderr.strip()}")
    return proc


def declared_repository(project_root: Path) -> str:
    """Return the standalone repository URL declared in ``CITATION.cff``."""
    citation = project_root / "CITATION.cff"
    if not citation.is_file():
        return ""
    match = _REPOSITORY_CODE_RE.search(citation.read_text(encoding="utf-8"))
    return match.group(1).strip().rstrip("/") if match else ""


def tracked_relative_paths(repo_root: Path, project_rel: str) -> list[str]:
    """Return exemplar-relative paths of every git-tracked file in the project."""
    prefix = f"{project_rel}/"
    listed = _git(["ls-files", project_rel], cwd=repo_root).stdout.split()
    return [path[len(prefix) :] for path in listed if path.startswith(prefix)]


def populate_mirror_tree(repo_root: Path, project_rel: str, destination: Path) -> int:
    """Copy the exemplar's tracked files into *destination*, dereferencing symlinks.

    Returns the number of files written. Existing files in *destination* that the
    monorepo does not track are left untouched — see the module docstring.
    """
    written = 0
    project_root = repo_root / project_rel
    for relative in tracked_relative_paths(repo_root, project_rel):
        source = project_root / relative
        target = destination / relative
        if source.is_symlink() and source.resolve().is_dir():
            resolved = source.resolve()
            try:
                resolved_rel = resolved.relative_to(repo_root)
            except ValueError:
                continue
            for inner in _git(["ls-files", str(resolved_rel)], cwd=repo_root).stdout.split():
                leaf = Path(inner).relative_to(resolved_rel)
                inner_target = target / leaf
                inner_target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(repo_root / inner, inner_target, follow_symlinks=True)
                written += 1
            continue
        if not source.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target, follow_symlinks=True)
        written += 1
    return written


def _classify(status_output: str) -> tuple[int, int, int]:
    added = modified = deleted = 0
    for line in status_output.splitlines():
        if not line.strip():
            continue
        code = line[:2]
        if code.startswith("A") or code.startswith("?"):
            added += 1
        elif code.startswith("D"):
            deleted += 1
        else:
            modified += 1
    return added, modified, deleted


def sync_exemplar(
    repo_root: Path,
    exemplar: str,
    *,
    commit: bool,
    source_revision: str,
    project_rel: str | None = None,
) -> MirrorResult:
    """Sync one exemplar into its standalone repository.

    With ``commit=False`` this reports what would change without cloning side
    effects persisting, which is the intended way to review a sync before it
    touches a public repository.
    """
    project_rel = project_rel or f"projects/templates/{exemplar}"
    project_root = repo_root / project_rel
    repository = declared_repository(project_root)
    if not repository:
        return MirrorResult(exemplar, "", "SKIP: no repository-code declared")

    with tempfile.TemporaryDirectory(prefix=f"mirror_{exemplar}_") as tmp:
        work = Path(tmp) / "repo"
        clone = _git(["clone", "--quiet", f"{repository}.git", str(work)], cwd=repo_root, check=False)
        if clone.returncode != 0:
            return MirrorResult(exemplar, repository, "SKIP: clone failed")

        populate_mirror_tree(repo_root, project_rel, work)
        _git(["add", "-A"], cwd=work)
        added, modified, deleted = _classify(_git(["status", "--porcelain"], cwd=work).stdout)
        if added + modified + deleted == 0:
            return MirrorResult(exemplar, repository, "up to date")
        if not commit:
            return MirrorResult(exemplar, repository, "WOULD SYNC", added, modified, deleted)

        message = (
            f"Sync from template monorepo\n\n"
            f"Source: {source_revision}\n"
            f"Mirrors the git-tracked project tree from {project_rel}/ per "
            "docs/guides/publication-runbook.md. Update-only: files the monorepo "
            "does not track (published output artifacts) are preserved."
        )
        _git(["commit", "--quiet", "-m", message], cwd=work)
        push = _git(["push", "origin", "HEAD"], cwd=work, check=False)
        if push.returncode != 0:
            return MirrorResult(exemplar, repository, "PUSH FAILED", added, modified, deleted)
        sha = _git(["rev-parse", "--short", "HEAD"], cwd=work).stdout.strip()
        return MirrorResult(exemplar, repository, "SYNCED", added, modified, deleted, sha)


__all__ = [
    "MirrorResult",
    "declared_repository",
    "populate_mirror_tree",
    "sync_exemplar",
    "tracked_relative_paths",
]
