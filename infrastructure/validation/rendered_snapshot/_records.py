"""Record-set builders: stage/source/config fingerprints for rendered snapshots.

Split from :mod:`infrastructure.validation.rendered_snapshot` (line-count
gate); the parent module imports these functions directly. Private companion —
the public API stays in ``rendered_snapshot``.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from pathlib import Path

from infrastructure.core.pipeline.artifacts import compute_sha256
from infrastructure.core.project_paths import resolve_source_manuscript_dir
from infrastructure.validation.rendered_snapshot._scan import (
    CACHE_PARTS as _CACHE_PARTS,
    FileRecord,
    Fingerprint,
    is_relative_to,
    RenderedSnapshotError,
    cached_records,
    iter_tree_files,
    relative_record,
    source_repository_boundary,
)

_IMPLEMENTATION_ROOTS = ("infrastructure", "scripts")


def _fingerprint(records: Iterable[FileRecord]) -> Fingerprint:
    normalized = sorted(records, key=lambda record: record.key)
    digest = hashlib.sha256()
    for record in normalized:
        digest.update(record.key.encode())
        digest.update(b"\0")
        digest.update(compute_sha256(record.path).encode())
        digest.update(b"\n")
    return Fingerprint(digest.hexdigest(), len(normalized))


def _stage_records(repo_root: Path) -> list[FileRecord]:
    records: list[FileRecord] = []
    for relative in _IMPLEMENTATION_ROOTS:
        stage_root = repo_root / relative
        records.extend(
            relative_record(record, repo_root)
            for record in iter_tree_files(
                stage_root,
                repo_root=repo_root,
                excluded_parts=_CACHE_PARTS,
            )
        )
    cached = cached_records(records, repo_root)
    if not cached:
        raise RenderedSnapshotError("STAGE_SOURCE_MISSING", "no cached stage implementation files found")
    return cached


_ROOT_CONFIG_PATHS = (".gitignore", ".python-version", "pyproject.toml", "uv.lock")
_CONFIG_SUFFIXES = frozenset({".toml", ".yaml", ".yml"})
_CONFIG_NAMES = frozenset(
    {
        ".python-version",
        ".zenodo.json",
        "CITATION.cff",
        "Dockerfile",
        "codemeta.json",
        "environment.yml",
        "uv.lock",
    }
)


def _is_config_path(path: str) -> bool:
    candidate = Path(path.split(" -> ", maxsplit=1)[0])
    name = candidate.name
    return (
        candidate.suffix.lower() in _CONFIG_SUFFIXES
        or name in _CONFIG_NAMES
        or name.startswith("requirements")
        or "config" in name.lower()
    )


def _project_records(
    repo_root: Path,
    project_root: Path,
    *,
    lexical_project_root: Path,
) -> tuple[list[FileRecord], list[FileRecord]]:
    source: list[FileRecord] = []
    config: list[FileRecord] = []
    project_repository = source_repository_boundary(repo_root, lexical_project_root, project_root)
    external_project = project_repository != repo_root.resolve()
    manuscript_root = resolve_source_manuscript_dir(project_root).absolute()
    # The project tree is what this snapshot describes, so the project root is a
    # permitted containment root even when the project is symlinked in from
    # outside the repository. The stage-implementation walk keeps the
    # repository-only boundary: stage code must live in the repository.
    for raw_record in iter_tree_files(
        project_root,
        repo_root=project_repository,
        extra_root=project_root,
    ):
        record = relative_record(raw_record, project_root)
        candidate = Path(record.key.split(" -> ", maxsplit=1)[0])
        if candidate.parts and candidate.parts[0] == "docs":
            display = project_root / candidate
            if not is_relative_to(display.absolute(), manuscript_root):
                continue
        if candidate.name in {"AGENTS.md", "README.md", "SYNTAX.md", "TO-DO.md", "TODO.md"}:
            continue
        (config if _is_config_path(record.key) else source).append(record)
    for relative in _ROOT_CONFIG_PATHS:
        path = repo_root / relative
        if path.is_file():
            config.append(FileRecord(f"@root/{relative}", path))
    source = cached_records(source, repo_root, require_worktrees=external_project)
    config = cached_records(config, repo_root, require_worktrees=external_project)
    if not source:
        raise RenderedSnapshotError("PROJECT_SOURCE_MISSING", "no cached project source files found")
    if not config:
        raise RenderedSnapshotError("PROJECT_CONFIG_MISSING", "no cached project configuration files found")
    return source, config
