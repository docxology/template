"""Source/provider admission for standalone mirror exports.

Every consumed mirror input is admitted against the public repository's tracked
or committed Git tree before its bytes are read: the exemplar root, its tracked
paths, the declared standalone repository, each dereferenced provider link and
the pinned committed inventory. This module owns that admission only; export
materialization and publication live in ``standalone_mirror``.
"""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

from infrastructure.core.files.secure_write import read_bytes_confined
from infrastructure.project.public_reference_git import GitReference, committed_blobs, inventory
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.publishing._standalone_git import (
    _PUBLIC_ROOTS,
    _clean_source_records,
    _git,
    _git_head_status,
)
from infrastructure.publishing.publication_tree import _Budget

_REPOSITORY_CODE_RE = re.compile(r"^repository-code:\s*(\S+)", re.MULTILINE)
_REPOSITORY_URL_RE = re.compile(r"https://github\.com/[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9][A-Za-z0-9_.-]{0,99}")


def declared_repository(project_root: Path) -> str:
    """Read a confined citation and admit only a credential-free GitHub URL."""
    citation = project_root / "CITATION.cff"
    if not project_root.exists() or (not citation.exists() and not citation.is_symlink()):
        return ""
    content = read_bytes_confined(project_root, citation, max_bytes=1024 * 1024).decode("utf-8")
    match = _REPOSITORY_CODE_RE.search(content)
    if not match:
        return ""
    repository = match.group(1).rstrip("/").removesuffix(".git")
    if not _REPOSITORY_URL_RE.fullmatch(repository):
        raise ValueError("Standalone repository must be a credential-free canonical GitHub HTTPS URL")
    return repository


def _project_root(repo_root: Path, project_rel: str) -> Path:
    if project_rel not in {f"projects/{name}" for name in PUBLIC_PROJECT_NAMES}:
        raise ValueError("Standalone mirrors require a canonical public exemplar")
    project = repo_root / project_rel
    if project.resolve(strict=True) != project.absolute():
        raise ValueError("Public exemplar roots must not contain symlinks")
    return project


def _tracked_paths(repo_root: Path, prefix: str) -> list[str]:
    # NUL separators preserve legitimate spaces/newlines and avoid Git's quoted
    # path representation. '--' prevents option/pathspec reinterpretation.
    return [path for path in _git(["ls-files", "-z", "--", prefix], cwd=repo_root).stdout.split("\0") if path]


def _public_source(repo_root: Path, source: Path, provider_roots: tuple[Path, ...] = _PUBLIC_ROOTS) -> Path:
    resolved = source.resolve(strict=True)
    try:
        relative = resolved.relative_to(repo_root)
    except ValueError as exc:
        raise ValueError("Mirror source escapes the public repository") from exc
    if not any(relative.is_relative_to(root) for root in provider_roots):
        raise ValueError("Mirror source provider is outside the public rosters")
    return resolved


def clean_source_revision(repo_root: Path, supplied: str | None = None) -> str:
    """Admit an actual clean HEAD; user-supplied labels cannot grant source identity."""
    if supplied is not None and not re.fullmatch(r"[0-9a-f]{7,64}", supplied):
        raise ValueError("standalone source revision must be an actual hexadecimal HEAD identity")
    head, resolved, status = _git_head_status(repo_root, supplied)
    return _clean_source_records(head, resolved, status, supplied)


def _committed_files(
    repo_root: Path,
    revision: str,
    budget: _Budget,
    *,
    listed: str | None = None,
    pinned: list[GitReference] | None = None,
) -> dict[str, tuple[str, str]]:
    if listed is None:
        listed = _git(
            [
                "ls-tree",
                "-r",
                "-z",
                revision,
                "--",
                *(root.as_posix() for root in _PUBLIC_ROOTS),
                "infrastructure",
                "pyproject.toml",
            ],
            cwd=repo_root,
        ).stdout
    records: dict[str, tuple[str, str]] = {}
    links: dict[str, tuple[str, str]] = {}
    for entry in listed.split("\0"):
        if not entry:
            continue
        budget.check()
        header, path = entry.split("\t", 1)
        mode, kind, identity = header.split(" ")
        if path in records or path in links:
            raise ValueError("committed mirror input repeats a provider path")
        if (mode, kind) == ("160000", "commit"):
            links[path] = mode, identity
        elif kind == "blob" and mode in {"100644", "100755", "120000"}:
            records[path] = mode, identity
        else:
            raise ValueError("standalone source contains an unsupported committed provider")
        if len(records) + len(links) > budget.limits.max_files:
            raise ValueError("committed mirror input exceeds its finite entry limit")
    if links:
        if pinned is None:
            raise ValueError("pinned mirror source requires retained native reference custody")
        reference = inventory(repo_root, revision, budget.deadline)
        if {row.path: (row.mode, row.oid) for row in reference.gitlinks} != links:
            raise ValueError("pinned mirror declaration differs from its admitted source tree")
        selected = {
            row.path: (row.mode, row.oid)
            for row in reference.files
            if row.path == "pyproject.toml"
            or Path(row.path).is_relative_to("infrastructure")
            or any(Path(row.path).is_relative_to(root) for root in _PUBLIC_ROOTS)
        }
        if selected != records:
            raise ValueError("pinned mirror raw source inventory differs from its admitted source tree")
        for path, (row, _) in committed_blobs(reference).items():
            if any(path.startswith(prefix + "/") for prefix in links):
                if path in records:
                    raise ValueError("pinned mirror source repeats a committed provider")
                records[path] = row.mode, row.oid
                if len(records) > budget.limits.max_files:
                    raise ValueError("expanded committed mirror input exceeds its finite entry limit")
        pinned.append(reference)
    return records


def _verify_committed(relative: str, content: bytes, mode: str, committed: dict[str, tuple[str, str]]) -> None:
    record = committed.get(relative)
    if record is None or record[0] != mode:
        raise ValueError("mirror consumed provider differs from its committed path or mode")
    blob = b"blob " + str(len(content)).encode("ascii") + b"\0" + content
    # Git object identity is compared in its native format; the export receipt uses SHA-256.
    digest = hashlib.sha256(blob) if len(record[1]) == 64 else hashlib.sha1(blob, usedforsecurity=False)
    if digest.hexdigest() != record[1]:
        raise ValueError("mirror consumed bytes differ from the admitted source commit")


def _bound_source(
    repo_root: Path,
    source: Path,
    committed: dict[str, tuple[str, str]],
    budget: _Budget,
    provider_roots: tuple[Path, ...] = _PUBLIC_ROOTS,
) -> Path:
    """Check every dereferenced link against the admitted public Git tree."""
    candidate = source
    for _ in range(17):
        budget.check()
        try:
            parts = candidate.relative_to(repo_root).parts
        except ValueError as error:
            raise ValueError("mirror provider escapes the admitted public repository") from error
        if not any(Path(*parts).is_relative_to(root) for root in provider_roots):
            raise ValueError("mirror provider chain is outside the public rosters")
        for index in range(len(parts)):
            current = repo_root.joinpath(*parts[: index + 1])
            if current.is_symlink():
                link = os.readlink(current)
                _verify_committed(current.relative_to(repo_root).as_posix(), os.fsencode(link), "120000", committed)
                candidate = Path(os.path.normpath(current.parent / link / Path(*parts[index + 1 :])))
                break
        else:
            return _public_source(repo_root, candidate, provider_roots)
    raise ValueError("mirror refuses recursive or excessive provider links")


def tracked_relative_paths(repo_root: Path, project_rel: str) -> list[str]:
    """Return exemplar-relative paths of every git-tracked file in the project."""
    repo_root = repo_root.resolve()
    _project_root(repo_root, project_rel)
    prefix = f"{project_rel}/"
    listed = _tracked_paths(repo_root, project_rel)
    return [path[len(prefix) :] for path in listed if path.startswith(prefix)]
