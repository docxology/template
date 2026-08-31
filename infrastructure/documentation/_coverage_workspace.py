"""Disposable coverage-workspace construction and confinement helpers.

This private module owns the filesystem and Git mechanics used to measure a
public exemplar in a disposable repository-shaped copy.  Coverage policy
selection remains in :mod:`infrastructure.documentation.counts_coverage` and
is supplied here explicitly so the named exception table has one owner.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import tempfile
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from infrastructure.core.runtime.environment import get_subprocess_env
from infrastructure.core.subprocess_policy import SubprocessPolicy, run_with_policy

COVERAGE_SUPPORT_IDENTITY_MODE = "explicit-public-documentation-support-v1"
_COVERAGE_COPY_EXCLUDED_NAMES = frozenset(
    {
        ".benchmarks",
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "htmlcov",
    }
)
_COVERAGE_GIT_ENVIRONMENT_VARIABLES = frozenset(
    {
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_CEILING_DIRECTORIES",
        "GIT_COMMON_DIR",
        "GIT_DIR",
        "GIT_DISCOVERY_ACROSS_FILESYSTEM",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_TEMPLATE_DIR",
        "GIT_WORK_TREE",
    }
)
_COVERAGE_GIT_ENVIRONMENT_PREFIXES = ("GIT_CONFIG_",)


@dataclass(frozen=True)
class _CoverageSupportSpec:
    """One repository-level path needed by the isolated Active test tree."""

    relative_path: Path
    kind: str
    content_identity: bool


_COVERAGE_COPY_SUPPORT_SPECS = (
    _CoverageSupportSpec(Path("AGENTS.md"), "file", True),
    _CoverageSupportSpec(Path("projects/AGENTS.md"), "file", True),
    _CoverageSupportSpec(Path("docs/_generated/COUNTS.md"), "file", False),
    _CoverageSupportSpec(Path("docs/RUN_GUIDE.md"), "file", True),
    _CoverageSupportSpec(Path("docs/rules/memory_and_decision_records.md"), "file", True),
    _CoverageSupportSpec(Path("docs/guides/publishing-guide.md"), "file", True),
    _CoverageSupportSpec(Path("docs/guides/zenodo-doi-strategy.md"), "file", True),
    _CoverageSupportSpec(Path("docs/guides/manuscript-semantics.md"), "file", True),
    _CoverageSupportSpec(Path("manuscript/SYNTAX.md"), "file", False),
    _CoverageSupportSpec(Path("docs/maintenance/archival-targets.md"), "file", True),
    _CoverageSupportSpec(Path("docs/maintenance/exemplar-backlog-history.md"), "file", True),
    _CoverageSupportSpec(Path("infrastructure/publishing/README.md"), "file", True),
    _CoverageSupportSpec(Path("projects/templates/template_code_project"), "directory", False),
)

_CoveragePolicyFactory = Callable[[str, float], SubprocessPolicy]


def _coverage_measurement_data_file(repo_root: Path, name: str) -> Path:
    """Return an absolute, project-local coverage data path."""
    project_dir = repo_root.resolve() / "projects" / "templates" / name
    return project_dir / f".coverage.measure_{name}"


def _is_coverage_copy_excluded(name: str) -> bool:
    return name in _COVERAGE_COPY_EXCLUDED_NAMES or name == ".coverage" or name.startswith(".coverage.")


def _coverage_copy_ignore(_directory: str, names: list[str]) -> list[str]:
    return [name for name in names if _is_coverage_copy_excluded(name)]


def _reject_coverage_copy_symlinks(project_dir: Path) -> None:
    """Fail closed when a non-excluded project entry is a symlink."""
    if project_dir.is_symlink():
        raise RuntimeError(f"coverage measurement project root cannot be a symlink: {project_dir}")
    for directory, directory_names, file_names in os.walk(project_dir, topdown=True, followlinks=False):
        directory_names[:] = [name for name in directory_names if not _is_coverage_copy_excluded(name)]
        for name in (*directory_names, *file_names):
            if _is_coverage_copy_excluded(name):
                continue
            path = Path(directory) / name
            if path.is_symlink():
                relative = path.relative_to(project_dir)
                raise RuntimeError(f"coverage measurement copy refuses symlink: {relative}")


def _validated_public_exemplar_path(repo_root: Path, name: str) -> Path:
    """Resolve the repository root, then reject symlinks in the public path."""
    try:
        resolved_root = repo_root.resolve(strict=True)
    except OSError as exc:
        raise RuntimeError(f"coverage measurement repository root is unavailable: {repo_root}") from exc
    current = resolved_root
    for part in ("projects", "templates", name):
        current /= part
        try:
            metadata = current.lstat()
        except OSError as exc:
            raise RuntimeError(f"coverage measurement project path is unavailable: {current}") from exc
        if stat.S_ISLNK(metadata.st_mode):
            relative = current.relative_to(resolved_root)
            raise RuntimeError(f"coverage measurement project path component cannot be a symlink: {relative}")
        if not stat.S_ISDIR(metadata.st_mode):
            raise RuntimeError(f"coverage measurement project path component is not a directory: {current}")
    return current


def _validated_coverage_support_path(repo_root: Path, spec: _CoverageSupportSpec) -> Path:
    """Return one confined, symlink-free support source of the declared type."""
    relative = spec.relative_path
    if relative.is_absolute() or not relative.parts or any(part in {"", ".", ".."} for part in relative.parts):
        raise RuntimeError(f"coverage support path must be a normalized relative path: {relative}")
    root = repo_root.resolve(strict=True)
    current = root
    for index, part in enumerate(relative.parts):
        current /= part
        try:
            metadata = current.lstat()
        except OSError as exc:
            raise RuntimeError(f"coverage support path is unavailable: {relative}") from exc
        if stat.S_ISLNK(metadata.st_mode):
            raise RuntimeError(f"coverage support path cannot contain a symlink: {relative}")
        is_leaf = index == len(relative.parts) - 1
        if not is_leaf and not stat.S_ISDIR(metadata.st_mode):
            raise RuntimeError(f"coverage support path parent is not a directory: {relative}")
    if spec.kind == "file" and not stat.S_ISREG(metadata.st_mode):
        raise RuntimeError(f"coverage support path is not a regular file: {relative}")
    if spec.kind == "directory" and not stat.S_ISDIR(metadata.st_mode):
        raise RuntimeError(f"coverage support path is not a real directory: {relative}")
    if spec.kind not in {"file", "directory"}:
        raise RuntimeError(f"coverage support path has unsupported type {spec.kind!r}: {relative}")
    try:
        current.resolve(strict=True).relative_to(root)
    except ValueError as exc:
        raise RuntimeError(f"coverage support path escapes the repository: {relative}") from exc
    return current


def _coverage_support_identity(repo_root: Path) -> dict[str, object]:
    """Return the deterministic identity for Active's external documentation closure."""
    entries: list[dict[str, str]] = []
    for spec in _COVERAGE_COPY_SUPPORT_SPECS:
        source = _validated_coverage_support_path(repo_root, spec)
        entry = {
            "identity": "sha256" if spec.content_identity else "existence",
            "path": spec.relative_path.as_posix(),
            "type": spec.kind,
        }
        if spec.content_identity:
            entry["sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
        entries.append(entry)
    encoded = json.dumps(entries, allow_nan=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return {
        "algorithm": "sha256",
        "digest": hashlib.sha256(encoded).hexdigest(),
        "entries": entries,
        "mode": COVERAGE_SUPPORT_IDENTITY_MODE,
    }


def _ensure_disposable_support_directory(repository_root: Path, relative: Path) -> Path:
    """Create one destination directory without traversing a symlink."""
    root = repository_root.resolve(strict=True)
    current = root
    for part in relative.parts:
        current /= part
        try:
            metadata = current.lstat()
        except FileNotFoundError:
            current.mkdir()
        except OSError as exc:
            raise RuntimeError(f"coverage support destination is unavailable: {relative}") from exc
        else:
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
                raise RuntimeError(f"coverage support destination is not a real directory: {relative}")
    try:
        current.resolve(strict=True).relative_to(root)
    except ValueError as exc:
        raise RuntimeError(f"coverage support destination escapes the disposable repository: {relative}") from exc
    return current


def _copy_coverage_support_closure(repo_root: Path, measurement_repository: Path) -> None:
    """Copy the exact repository-level documentation closure into the disposable tree."""
    canonical_identity = _coverage_support_identity(repo_root)
    for spec in _COVERAGE_COPY_SUPPORT_SPECS:
        source = _validated_coverage_support_path(repo_root, spec)
        if spec.kind == "directory":
            _ensure_disposable_support_directory(measurement_repository, spec.relative_path)
            continue
        destination_parent = _ensure_disposable_support_directory(
            measurement_repository,
            spec.relative_path.parent,
        )
        destination = destination_parent / spec.relative_path.name
        if destination.exists() or destination.is_symlink():
            raise RuntimeError(f"coverage support destination already exists: {spec.relative_path}")
        shutil.copy2(source, destination, follow_symlinks=False)
        destination_metadata = destination.lstat()
        if not stat.S_ISREG(destination_metadata.st_mode):
            raise RuntimeError(f"coverage support destination is not a regular file: {spec.relative_path}")
    disposable_identity = _coverage_support_identity(measurement_repository)
    if disposable_identity != canonical_identity:
        raise RuntimeError("coverage support closure differs between canonical and disposable repositories")


def _coverage_git_environment() -> dict[str, str]:
    """Return an environment that cannot redirect Git reads or writes."""
    environment = dict(get_subprocess_env())
    for variable in tuple(environment):
        if variable in _COVERAGE_GIT_ENVIRONMENT_VARIABLES or variable.startswith(_COVERAGE_GIT_ENVIRONMENT_PREFIXES):
            environment.pop(variable, None)
    environment["GIT_CONFIG_GLOBAL"] = os.devnull
    environment["GIT_CONFIG_NOSYSTEM"] = "1"
    environment["GIT_CONFIG_SYSTEM"] = os.devnull
    return environment


def _run_coverage_git_with_policy_factory(
    argv: list[str],
    *,
    cwd: Path,
    action: str,
    process_policy_factory: _CoveragePolicyFactory,
) -> str:
    """Run one bounded Git context command and return its stripped output."""
    result = run_with_policy(
        argv,
        cwd=cwd,
        env=_coverage_git_environment(),
        policy=process_policy_factory("coverage-copy-git-context", 30),
    )
    if result.timed_out:
        raise RuntimeError(f"coverage measurement Git context timed out while {action}")
    if result.returncode != 0 or result.command_error:
        detail = result.command_error or result.stderr.strip() or result.stdout.strip() or "no diagnostic output"
        raise RuntimeError(f"coverage measurement Git context failed while {action}: {detail[-1000:]}")
    return result.stdout.strip()


def _confined_disposable_git_path(
    measurement_repository: Path,
    raw_path: str,
    *,
    label: str,
) -> Path:
    """Resolve one Git metadata path and require it to stay disposable."""
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = measurement_repository / candidate
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(measurement_repository.resolve(strict=True))
    except ValueError as exc:
        raise RuntimeError(f"coverage measurement disposable Git {label} escapes its project") from exc
    return resolved


def _provision_coverage_copy_git_context_with_policy_factory(
    repo_root: Path,
    environment_project: Path,
    measurement_repository: Path,
    measurement_project: Path,
    *,
    process_policy_factory: _CoveragePolicyFactory,
) -> None:
    """Give the disposable copy canonical commit identity without Git writes upstream."""
    canonical_root = repo_root.resolve(strict=True)
    discovered_root_text = _run_coverage_git_with_policy_factory(
        ["git", "-C", str(environment_project), "rev-parse", "--show-toplevel"],
        cwd=canonical_root,
        action="resolving the canonical repository root",
        process_policy_factory=process_policy_factory,
    )
    try:
        discovered_root = Path(discovered_root_text).resolve(strict=True)
    except OSError as exc:
        raise RuntimeError("coverage measurement Git context returned an unavailable repository root") from exc
    if discovered_root != canonical_root:
        raise RuntimeError(
            "coverage measurement project belongs to an unexpected Git repository: "
            f"{discovered_root} != {canonical_root}"
        )

    source_commit = _run_coverage_git_with_policy_factory(
        ["git", "-C", str(canonical_root), "rev-parse", "--verify", "HEAD^{commit}"],
        cwd=canonical_root,
        action="resolving the canonical source commit",
        process_policy_factory=process_policy_factory,
    )
    common_dir_text = _run_coverage_git_with_policy_factory(
        ["git", "-C", str(canonical_root), "rev-parse", "--git-common-dir"],
        cwd=canonical_root,
        action="resolving the canonical object store",
        process_policy_factory=process_policy_factory,
    )
    common_dir = Path(common_dir_text)
    if not common_dir.is_absolute():
        common_dir = canonical_root / common_dir
    try:
        object_store = (common_dir.resolve(strict=True) / "objects").resolve(strict=True)
    except OSError as exc:
        raise RuntimeError("coverage measurement canonical Git object store is unavailable") from exc
    if not object_store.is_dir():
        raise RuntimeError("coverage measurement canonical Git object store is not a directory")
    object_store_text = str(object_store)
    if "\n" in object_store_text or "\r" in object_store_text:
        raise RuntimeError("coverage measurement canonical Git object-store path contains a newline")

    empty_template = measurement_repository.parent / ".empty-git-template"
    empty_template.mkdir()
    _run_coverage_git_with_policy_factory(
        ["git", "init", "-q", f"--template={empty_template}", str(measurement_repository)],
        cwd=measurement_repository.parent,
        action="initializing disposable Git metadata",
        process_policy_factory=process_policy_factory,
    )
    disposable_git_dir = measurement_repository / ".git"
    try:
        git_metadata = disposable_git_dir.lstat()
    except OSError as exc:
        raise RuntimeError("coverage measurement disposable Git metadata is unavailable") from exc
    if stat.S_ISLNK(git_metadata.st_mode) or not stat.S_ISDIR(git_metadata.st_mode):
        raise RuntimeError("coverage measurement disposable Git metadata is not a real directory")

    git_paths = {
        "Git directory": _run_coverage_git_with_policy_factory(
            ["git", "-C", str(measurement_repository), "rev-parse", "--git-dir"],
            cwd=measurement_project,
            action="resolving the disposable Git directory",
            process_policy_factory=process_policy_factory,
        ),
        "common directory": _run_coverage_git_with_policy_factory(
            ["git", "-C", str(measurement_repository), "rev-parse", "--git-common-dir"],
            cwd=measurement_project,
            action="resolving the disposable common directory",
            process_policy_factory=process_policy_factory,
        ),
        "index": _run_coverage_git_with_policy_factory(
            ["git", "-C", str(measurement_repository), "rev-parse", "--git-path", "index"],
            cwd=measurement_project,
            action="resolving the disposable index",
            process_policy_factory=process_policy_factory,
        ),
        "index lock": _run_coverage_git_with_policy_factory(
            ["git", "-C", str(measurement_repository), "rev-parse", "--git-path", "index.lock"],
            cwd=measurement_project,
            action="resolving the disposable index lock",
            process_policy_factory=process_policy_factory,
        ),
        "HEAD lock": _run_coverage_git_with_policy_factory(
            ["git", "-C", str(measurement_repository), "rev-parse", "--git-path", "HEAD.lock"],
            cwd=measurement_project,
            action="resolving the disposable HEAD lock",
            process_policy_factory=process_policy_factory,
        ),
        "logs directory": _run_coverage_git_with_policy_factory(
            ["git", "-C", str(measurement_repository), "rev-parse", "--git-path", "logs"],
            cwd=measurement_project,
            action="resolving the disposable logs directory",
            process_policy_factory=process_policy_factory,
        ),
        "object write directory": _run_coverage_git_with_policy_factory(
            ["git", "-C", str(measurement_repository), "rev-parse", "--git-path", "objects"],
            cwd=measurement_project,
            action="resolving the disposable object write directory",
            process_policy_factory=process_policy_factory,
        ),
        "packed refs lock": _run_coverage_git_with_policy_factory(
            ["git", "-C", str(measurement_repository), "rev-parse", "--git-path", "packed-refs.lock"],
            cwd=measurement_project,
            action="resolving the disposable packed-refs lock",
            process_policy_factory=process_policy_factory,
        ),
        "refs directory": _run_coverage_git_with_policy_factory(
            ["git", "-C", str(measurement_repository), "rev-parse", "--git-path", "refs"],
            cwd=measurement_project,
            action="resolving the disposable refs directory",
            process_policy_factory=process_policy_factory,
        ),
    }
    confined_paths = {
        label: _confined_disposable_git_path(measurement_repository, raw_path, label=label)
        for label, raw_path in git_paths.items()
    }
    expected_git_dir = disposable_git_dir.resolve(strict=True)
    if confined_paths["Git directory"] != expected_git_dir or confined_paths["common directory"] != expected_git_dir:
        raise RuntimeError("coverage measurement disposable Git directory is not self-contained")
    if confined_paths["index"] != expected_git_dir / "index":
        raise RuntimeError("coverage measurement disposable Git index is not self-contained")
    if confined_paths["index lock"] != expected_git_dir / "index.lock":
        raise RuntimeError("coverage measurement disposable Git index lock is not self-contained")
    if confined_paths["HEAD lock"] != expected_git_dir / "HEAD.lock":
        raise RuntimeError("coverage measurement disposable Git HEAD lock is not self-contained")
    if confined_paths["logs directory"] != expected_git_dir / "logs":
        raise RuntimeError("coverage measurement disposable Git logs are not self-contained")
    if confined_paths["object write directory"] != expected_git_dir / "objects":
        raise RuntimeError("coverage measurement disposable Git object writes are not self-contained")
    if confined_paths["packed refs lock"] != expected_git_dir / "packed-refs.lock":
        raise RuntimeError("coverage measurement disposable Git packed-refs lock is not self-contained")
    if confined_paths["refs directory"] != expected_git_dir / "refs":
        raise RuntimeError("coverage measurement disposable Git refs are not self-contained")

    alternates_path = disposable_git_dir / "objects" / "info" / "alternates"
    alternates_path.parent.mkdir(parents=True, exist_ok=True)
    alternates_path.write_text(f"{object_store_text}\n", encoding="utf-8")
    _run_coverage_git_with_policy_factory(
        ["git", "-C", str(measurement_repository), "update-ref", "--no-deref", "HEAD", source_commit],
        cwd=measurement_repository,
        action="installing the disposable source commit",
        process_policy_factory=process_policy_factory,
    )
    disposable_commit = _run_coverage_git_with_policy_factory(
        ["git", "-C", str(measurement_project), "rev-parse", "--verify", "HEAD^{commit}"],
        cwd=measurement_project,
        action="verifying the disposable source commit",
        process_policy_factory=process_policy_factory,
    )
    if disposable_commit != source_commit:
        raise RuntimeError(
            "coverage measurement disposable source commit does not match canonical HEAD: "
            f"{disposable_commit} != {source_commit}"
        )
    disposable_top_level = _run_coverage_git_with_policy_factory(
        ["git", "-C", str(measurement_project), "rev-parse", "--show-toplevel"],
        cwd=measurement_project,
        action="verifying the disposable repository root",
        process_policy_factory=process_policy_factory,
    )
    if Path(disposable_top_level).resolve(strict=True) != measurement_repository.resolve(strict=True):
        raise RuntimeError("coverage measurement disposable Git top-level is not repository-shaped")


@contextmanager
def _coverage_measurement_workspace_with_policy_factory(
    repo_root: Path,
    name: str,
    *,
    disposable: bool,
    process_policy_factory: _CoveragePolicyFactory,
) -> Iterator[tuple[Path, Path]]:
    """Yield the environment and measurement projects for one policy decision."""
    environment_project = repo_root.resolve() / "projects" / "templates" / name
    if not disposable:
        yield environment_project, environment_project
        return

    environment_project = _validated_public_exemplar_path(repo_root, name)
    _reject_coverage_copy_symlinks(environment_project)
    with tempfile.TemporaryDirectory(prefix=f"coverage-measurement-{name}-") as temporary:
        measurement_repository = Path(temporary) / "repository"
        measurement_repository.mkdir()
        measurement_project = measurement_repository / "projects" / "templates" / name
        measurement_project.parent.mkdir(parents=True)
        shutil.copytree(
            environment_project,
            measurement_project,
            symlinks=True,
            ignore=_coverage_copy_ignore,
        )
        _reject_coverage_copy_symlinks(measurement_project)
        _copy_coverage_support_closure(repo_root, measurement_repository)
        _reject_coverage_copy_symlinks(measurement_repository)
        _provision_coverage_copy_git_context_with_policy_factory(
            repo_root,
            environment_project,
            measurement_repository,
            measurement_project,
            process_policy_factory=process_policy_factory,
        )
        yield environment_project, measurement_project


__all__ = [
    "COVERAGE_SUPPORT_IDENTITY_MODE",
    "_COVERAGE_COPY_EXCLUDED_NAMES",
    "_COVERAGE_COPY_SUPPORT_SPECS",
    "_COVERAGE_GIT_ENVIRONMENT_PREFIXES",
    "_COVERAGE_GIT_ENVIRONMENT_VARIABLES",
    "_CoverageSupportSpec",
    "_confined_disposable_git_path",
    "_copy_coverage_support_closure",
    "_coverage_copy_ignore",
    "_coverage_git_environment",
    "_coverage_measurement_data_file",
    "_coverage_measurement_workspace_with_policy_factory",
    "_coverage_support_identity",
    "_ensure_disposable_support_directory",
    "_is_coverage_copy_excluded",
    "_provision_coverage_copy_git_context_with_policy_factory",
    "_reject_coverage_copy_symlinks",
    "_run_coverage_git_with_policy_factory",
    "_validated_coverage_support_path",
    "_validated_public_exemplar_path",
]
