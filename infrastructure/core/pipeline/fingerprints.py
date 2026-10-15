"""Content identities for source trees and stable deliverables.

Control state and runtime observations are deliberately outside deliverable
identity. A symlink cannot silently authorize reuse of unexamined content.
"""

from __future__ import annotations

import hashlib
import json
import sys
import os
import stat
import sysconfig
from importlib.metadata import distributions
from pathlib import Path
from collections.abc import Callable, Mapping

from infrastructure.core.pipeline.fingerprint_files import anchored_parent, digest_file, open_directory

SOURCE_EXCLUSIONS = frozenset(
    {
        ".git",
        ".venv",
        ".lake",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".pipeline",
    }
)
_ROOT_SOURCE_CONTROLS = SOURCE_EXCLUSIONS | frozenset(
    {
        ".hypothesis",
        ".coverage",
        ".coverage.project",
        "coverage_project.json",
        "htmlcov",
        "build",
        "dist",
    }
)


def canonical_digest(value: object) -> str:
    """Hash a JSON-compatible value with one stable serialization."""
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def tree_records(
    path: Path,
    *,
    source: bool = False,
    stable_output: bool = False,
    excluded_roots: frozenset[Path] = frozenset(),
    excluded_names: frozenset[str] = frozenset(),
    control_output: bool = False,
    output_roots: tuple[Path, ...] = (),
    path_admission: Callable[[Path], None] | None = None,
) -> tuple[tuple[str, str, str], ...]:
    """Inventory regular content under held directories, including missing paths.

    Exact descendant names may be excluded before opening them. The nominated
    root itself remains observed, and the default name exclusion is empty.
    """
    records: list[tuple[str, str, str]] = []
    lexical_path = path.absolute()
    output_root = next((root.absolute() for root in output_roots if lexical_path.is_relative_to(root.absolute())), None)
    if not source and (control_output or stable_output) and output_root is None:
        output_root = next(
            (ancestor for ancestor in (lexical_path, *lexical_path.parents) if ancestor.name == "output"), None
        )
    output_tree = not source and (control_output or stable_output or output_root is not None)
    if output_tree and output_root is None:
        output_root = lexical_path if path.is_dir() else lexical_path.parent

    def included(child: Path, root_child: bool, source_child: bool) -> bool:
        if child.name in excluded_names or child.absolute() in excluded_roots:
            return False
        if source:
            if (
                child.name == "__pycache__"
                or child.suffix in {".pyc", ".pyo"}
                or (root_child and child.name in _ROOT_SOURCE_CONTROLS)
                or (source_child and child.name.endswith(".egg-info"))
            ):
                return False
        if output_tree:
            from infrastructure.core.pipeline.artifacts._inventory import _is_ignored_output_relative

            assert output_root is not None
            if _is_ignored_output_relative(child.absolute().relative_to(output_root)):
                return False
        return True

    def names(descriptor: int, current: Path) -> tuple[str, ...]:
        # Every child is constructed beneath this lexical directory. Derive
        # control depth once per census, retaining both fresh filesystem reads.
        root_child = current == lexical_path
        source_child = current.name == "src" and current.parent == lexical_path
        return tuple(
            name for name in sorted(os.listdir(descriptor)) if included(current / name, root_child, source_child)
        )

    def visit(current: Path, relative: str, parent: int, name: str) -> None:
        if path_admission is not None:
            path_admission(current)
        try:
            metadata = os.stat(name, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            records.append((relative, "missing", ""))
            return
        if stat.S_ISLNK(metadata.st_mode):
            raise ValueError(f"Content identity refuses symlink: {current}")
        if stat.S_ISREG(metadata.st_mode):
            records.append((relative, "file", digest_file(current, parent, name, metadata)))
        elif stat.S_ISDIR(metadata.st_mode):
            first_record = len(records)
            records.append((relative, "directory", ""))
            with open_directory(parent, name) as descriptor:
                opened = os.fstat(descriptor)
                if (opened.st_dev, opened.st_ino) != (metadata.st_dev, metadata.st_ino):
                    raise ValueError("Fingerprint directory changed before traversal")
                children = names(descriptor, current)
                for child_name in children:
                    visit(current / child_name, f"{relative}/{child_name}", descriptor, child_name)
                if children != names(descriptor, current):
                    raise ValueError("Fingerprint directory contents changed during traversal")
            if (
                output_tree
                and output_root is not None
                and current.absolute().relative_to(output_root) in {Path("reports"), Path("fulltext")}
                and not any(kind == "file" for _, kind, _ in records[first_record:])
            ):
                del records[first_record:]
        else:
            raise ValueError(f"Unsupported content type: {current}")

    with anchored_parent(lexical_path) as parent:
        if parent is None:
            records.append((".", "missing", ""))
        else:
            visit(lexical_path, ".", parent, lexical_path.name or ".")
    return tuple(records)


def paths_digest(
    paths: tuple[Path, ...],
    *,
    source: bool = False,
    stable_output: bool = False,
    excluded_roots: frozenset[Path] = frozenset(),
    excluded_names: frozenset[str] = frozenset(),
    control_output: bool = False,
    output_roots: tuple[Path, ...] = (),
    path_admission: Callable[[Path], None] | None = None,
) -> str:
    """Hash sorted path names and recursive contents without checkout-location dependence."""
    if not paths:
        return canonical_digest([])
    # Resolve a lexical common ancestor without following symlinks.
    base = Path(os.path.commonpath([str(path.absolute().parent) for path in paths]))
    return canonical_digest(
        [
            (
                str(path.absolute().relative_to(base)),
                tree_records(
                    path,
                    source=source,
                    stable_output=stable_output,
                    excluded_roots=excluded_roots,
                    excluded_names=excluded_names,
                    control_output=control_output,
                    output_roots=output_roots,
                    path_admission=path_admission,
                ),
            )
            for path in sorted(set(paths), key=lambda item: item.as_posix())
        ]
    )


def source_content_fingerprint(repo_root: Path, project_dir: Path, *, definition_path: Path | None = None) -> str:
    """Public source/configuration/lock bytes, independent of interpreter metadata."""
    observed = _observe_loaded_implementation()
    roots = [repo_root / "infrastructure", repo_root / "scripts", project_dir]
    implementation_root = Path(__file__).resolve().parents[2]
    if implementation_root != (repo_root / "infrastructure").resolve():
        roots.append(implementation_root)
    roots.extend(repo_root / name for name in ("pyproject.toml", "uv.lock", ".python-version", "pipeline.yaml"))
    if definition_path is not None:
        roots.append(definition_path)
    excluded = (project_dir / "output").absolute()
    reusable = {path: rows for path, rows in observed.items() if not excluded.is_relative_to(path)}
    paths = tuple(roots)
    base = Path(os.path.commonpath([str(path.absolute().parent) for path in paths]))
    return canonical_digest(
        [
            (
                str(path.absolute().relative_to(base)),
                reusable[path.absolute()]
                if path.absolute() in reusable
                else tree_records(path, source=True, excluded_roots=frozenset({excluded})),
            )
            for path in sorted(set(paths), key=lambda item: item.as_posix())
        ]
    )


def source_fingerprint_components(
    repo_root: Path, project_dir: Path, *, definition_path: Path | None = None
) -> dict[str, object]:
    """Observe the same source, Python, and tool payload used for admission."""
    content = source_content_fingerprint(repo_root, project_dir, definition_path=definition_path)
    python_identity = {
        "version": sys.version,
        "implementation": sys.implementation.name,
        "packages": sorted(
            (str(dist.metadata.get("Name", "")), dist.version)
            for dist in distributions(path=sorted({sysconfig.get_path("purelib"), sysconfig.get_path("platlib")}))
        ),
    }
    return {
        "source": content,
        "python": python_identity,
        "tools": effective_tool_identities(repo_root, project_dir),
    }


def source_fingerprint(repo_root: Path, project_dir: Path, *, definition_path: Path | None = None) -> str:
    """Conservative source and actual outer-runtime identity for one project."""
    return canonical_digest(source_fingerprint_components(repo_root, project_dir, definition_path=definition_path))


def tool_identities(
    *, project_dir: Path | None = None, environment: Mapping[str, str] | None = None
) -> dict[str, object]:
    """Bind effective executable and known backend bytes without acquisitions."""
    from infrastructure.core.pipeline.tool_bindings import collect_tool_bindings

    def bounded_identity(path: Path) -> object:
        with anchored_parent(path) as parent:
            if parent is None:
                return ((".", "missing", ""),)
            observed = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
            return ((".", "file", digest_file(path, parent, path.name, observed, max_bytes=512 * 1024 * 1024)),)

    return collect_tool_bindings(project_dir, os.environ if environment is None else environment, bounded_identity)


def effective_tool_identities(repo_root: Path, project_dir: Path) -> dict[str, object]:
    """Use the same effective environment that reaches actual stage scripts."""
    from infrastructure.core.pipeline.stages import build_stage_subprocess_env

    return tool_identities(project_dir=project_dir, environment=build_stage_subprocess_env(repo_root, project_dir))


def tool_reuse_refusal(repo_root: Path, project_dir: Path) -> str | None:
    """Opaque launcher identity cannot authorize a cached or resumed result."""
    unresolved = effective_tool_identities(repo_root, project_dir).get("unresolved_backends")
    if unresolved:
        return "Tool backend identity is unresolved; nominate the actual backend and start a fresh run"
    return None


_LOADED_IMPLEMENTATION_ROOT = Path(__file__).resolve().parents[2]
_LOADED_IMPLEMENTATION_PATHS = (_LOADED_IMPLEMENTATION_ROOT, _LOADED_IMPLEMENTATION_ROOT.parent / "scripts")
_LOADED_IMPLEMENTATION_DIGEST = paths_digest(_LOADED_IMPLEMENTATION_PATHS, source=True)


def _observe_loaded_implementation() -> dict[Path, tuple[tuple[str, str, str], ...]]:
    """Observe complete current trees once for this single admission boundary.

    These local rows preserve all source-file and directory semantics. They
    never survive this call boundary or replace the separate executed-code,
    stage/worker, cache/resume, or completion observations.
    """
    paths = _LOADED_IMPLEMENTATION_PATHS
    base = Path(os.path.commonpath([str(path.absolute().parent) for path in paths]))
    observed = {path.absolute(): tree_records(path, source=True) for path in paths}
    digest = canonical_digest(
        [
            (str(path.absolute().relative_to(base)), observed[path.absolute()])
            for path in sorted(set(paths), key=lambda item: item.as_posix())
        ]
    )
    if digest != _LOADED_IMPLEMENTATION_DIGEST:
        raise ValueError("Loaded infrastructure changed after import; restart the worker before resolving a new plan")
    return observed


def verify_loaded_implementation() -> None:
    """Refuse new plans from stale imported infrastructure in a reused worker."""
    _observe_loaded_implementation()


__all__ = ["canonical_digest", "paths_digest", "source_fingerprint", "tree_records", "verify_loaded_implementation"]
