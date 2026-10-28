"""Explicit source-provider admission for tests that consume platform sources.

This selects source-integration inputs, not the installed Python distribution.
An external checkout is nominated by its absolute path and exact Git commit.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
import time
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

SOURCE_ROOT_ENV = "TEMPLATE_AUTORESEARCH_SOURCE_ROOT"
SOURCE_COMMIT_ENV = "TEMPLATE_AUTORESEARCH_SOURCE_COMMIT"
PROJECT_PATH = Path("projects/templates/template_autoresearch_project")
_SOURCE_ROOTS = (
    "infrastructure",
    "scripts",
    PROJECT_PATH.as_posix(),
    "pyproject.toml",
    "uv.lock",
    ".python-version",
    "README.md",
    "LICENSE",
)
_IGNORED_NAMES = frozenset(
    {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", "htmlcov", "output", "dist", "build"}
)
_REQUIRED_SOURCE_FILES = frozenset(
    {
        "pyproject.toml",
        (PROJECT_PATH / "pyproject.toml").as_posix(),
        "infrastructure/__init__.py",
        "infrastructure/_version.py",
        "infrastructure/core/pipeline/pipeline.yaml",
        "scripts/pipeline/stage_01_test.py",
    }
)


def _ignored(name: str) -> bool:
    return name in _IGNORED_NAMES or name.startswith(".coverage") or name.endswith((".egg-info", ".pyc"))


def _git(root: Path, *arguments: str) -> str:
    """Read native Git state without ambient Git routing or optional locks."""
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    environment.update(
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_OPTIONAL_LOCKS="0",
        GIT_NO_REPLACE_OBJECTS="1",
    )
    result = subprocess.run(
        ["git", "-c", "core.fsmonitor=false", "-C", str(root), *arguments],
        env=environment,
        check=False,
        text=True,
        capture_output=True,
        timeout=15,
    )
    if result.returncode:
        raise ValueError("platform source provider Git identity is unavailable")
    return result.stdout.rstrip("\n")


def _read_source(path: Path) -> bytes:
    """Read regular current bytes; source providers may not redirect files."""
    if path.resolve(strict=True) != path.absolute():
        raise ValueError("platform source provider contains a source symlink")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_size > 64 * 1024 * 1024:
            raise ValueError("platform source provider contains an unsupported source file")
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            content = stream.read(64 * 1024 * 1024 + 1)
        after = os.fstat(descriptor)
        fields = ("st_dev", "st_ino", "st_mode", "st_size", "st_mtime_ns", "st_ctime_ns")
        if any(getattr(before, field) != getattr(after, field) for field in fields) or len(content) != before.st_size:
            raise ValueError("platform source provider changed during its source read")
        return content
    finally:
        os.close(descriptor)


def _source_records(root: Path) -> tuple[tuple[str, str, str, str], ...]:
    """Bind the actual platform and canonical exemplar sources consumed here."""
    records = []
    count = 0
    total = 0
    deadline = time.monotonic() + 30
    for relative in _SOURCE_ROOTS:
        selected = root / relative
        pending = [selected]
        while pending:
            if time.monotonic() >= deadline:
                raise ValueError("platform source provider exceeds the source inventory deadline")
            path = pending.pop()
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise ValueError("platform source provider contains a source symlink")
            name = path.relative_to(root).as_posix()
            count += 1
            if count > 20_000:
                raise ValueError("platform source provider exceeds the source inventory budget")
            if stat.S_ISDIR(mode):
                records.append((name, "directory", "", ""))
                children = []
                for child in path.iterdir():
                    if time.monotonic() >= deadline:
                        raise ValueError("platform source provider exceeds the source inventory deadline")
                    if _ignored(child.name):
                        continue
                    children.append(child)
                    if count + len(pending) + len(children) > 20_000:
                        raise ValueError("platform source provider exceeds the source inventory budget")
                pending.extend(sorted(children, reverse=True))
            else:
                content = _read_source(path)
                _validate_metadata(name, content)
                total += len(content)
                if total > 256 * 1024 * 1024:
                    raise ValueError("platform source provider exceeds the source byte budget")
                blob = hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content, usedforsecurity=False)
                records.append((name, "file", hashlib.sha256(content).hexdigest(), blob.hexdigest()))
    files = {name for name, kind, _, _ in records if kind == "file"}
    if not _REQUIRED_SOURCE_FILES.issubset(files):
        raise ValueError("platform source provider lacks required canonical source contracts")
    return tuple(records)


def source_identity(root: Path) -> str:
    """Fingerprint current source bytes independently of Git status shortcuts."""
    return _records_identity(_source_records(root))


def _records_identity(records: tuple[tuple[str, str, str, str], ...]) -> str:
    return hashlib.sha256(json.dumps(records, separators=(",", ":")).encode()).hexdigest()


def _validate_metadata(relative: str, held_content: bytes) -> None:
    """Validate the identical held bytes used for the source and Git hashes."""
    if relative == "pyproject.toml":
        metadata = tomllib.loads(held_content.decode())
        if (
            metadata.get("project", {}).get("name") != "research-project-template"
            or metadata["project"].get("version") != "4.3.0"
        ):
            raise ValueError("platform source provider must declare research-project-template 4.3.0")
    elif relative == (PROJECT_PATH / "pyproject.toml").as_posix():
        project = tomllib.loads(held_content.decode())
        if (
            project.get("project", {}).get("name") != "template_autoresearch_project"
            or project.get("tool", {}).get("template", {}).get("platform_version") != "4.3.0"
        ):
            raise ValueError("platform source provider lacks the canonical Autoresearch 4.3.0 contract")


@dataclass(frozen=True)
class SourceProvider:
    """A source input binding, deliberately separate from installed-wheel origin."""

    root: Path
    identity: str
    commit: str | None

    def assert_unchanged(self) -> None:
        if source_identity(self.root) != self.identity:
            raise ValueError("platform source provider changed after test admission")
        if self.commit is not None:
            _validate_commit(self.root, self.commit)


def _validate_commit(root: Path, commit: str) -> tuple[tuple[str, str, str, str], ...]:
    if Path(_git(root, "rev-parse", "--show-toplevel")).resolve() != root:
        raise ValueError("platform source provider must be the nominated Git checkout root")
    if _git(root, "rev-parse", "HEAD") != commit:
        raise ValueError("platform source provider HEAD differs from its nominated exact commit")
    if _git(root, "status", "--porcelain", "--untracked-files=all"):
        raise ValueError("external platform source provider must have clean committed source")
    committed = {}
    for entry in _git(root, "ls-tree", "-r", "-z", commit, "--", *_SOURCE_ROOTS).split("\0"):
        if not entry:
            continue
        descriptor, path = entry.split("\t", 1)
        mode, kind, blob = descriptor.split(" ")
        if any(_ignored(part) for part in Path(path).parts):
            continue
        if kind != "blob" or mode not in {"100644", "100755"}:
            raise ValueError("external platform source provider has an unsupported committed source")
        committed[path] = blob
    records = _source_records(root)
    current = {path: blob for path, kind, _, blob in records if kind == "file"}
    if current.keys() != committed.keys():
        raise ValueError("external platform source provider file set differs from its exact committed source")
    for path, blob in current.items():
        if committed.get(path) != blob:
            raise ValueError("external platform source provider bytes differ from its exact committed source")
    if _git(root, "rev-parse", "HEAD") != commit or _git(root, "status", "--porcelain", "--untracked-files=all"):
        raise ValueError("external platform source provider changed during its committed source admission")
    return records


def resolve_source_provider(project: Path, environment: Mapping[str, str]) -> SourceProvider:
    """Use an exact canonical ancestor or a deliberate commit-bound provider."""
    project = project.resolve(strict=True)
    nominated_root = environment.get(SOURCE_ROOT_ENV)
    nominated_commit = environment.get(SOURCE_COMMIT_ENV)
    if nominated_root is not None or nominated_commit is not None:
        if not nominated_root or not nominated_commit or not re.fullmatch(r"[0-9a-f]{40}", nominated_commit):
            raise ValueError(f"{SOURCE_ROOT_ENV} and {SOURCE_COMMIT_ENV} require an absolute path and exact 40-hex SHA")
        candidate = Path(nominated_root)
        if not candidate.is_absolute():
            raise ValueError("platform source provider path must be absolute")
        root = candidate.resolve(strict=True)
        records = _validate_commit(root, nominated_commit)
        return SourceProvider(root, _records_identity(records), nominated_commit)
    for root in project.parents:
        if root / PROJECT_PATH == project:
            return SourceProvider(root, source_identity(root), None)
    raise ValueError(
        f"standalone source integration requires {SOURCE_ROOT_ENV} and {SOURCE_COMMIT_ENV}; "
        "an infrastructure directory or installed wheel does not nominate a source checkout"
    )
