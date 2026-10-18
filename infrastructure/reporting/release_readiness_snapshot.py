"""Confined one-read snapshots shared by facts and their receipt hashes."""

from __future__ import annotations

import hashlib
import json
import math
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import read_bytes_confined
from infrastructure.core.pipeline.fingerprint_files import anchored_parent
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

PUBLIC_ROOT_FILES = frozenset(
    {
        ".cursorrules",
        ".dockerignore",
        ".gitattributes",
        ".gitignore",
        ".gitmodules",
        ".ignore",
        ".pre-commit-config.yaml",
        ".python-version",
        "AGENTS.md",
        "CHANGELOG.md",
        "CITATION.cff",
        "CLAUDE.md",
        "CONTRIBUTING.md",
        "ISA.md",
        "LICENSE",
        "MAINTAINERS.md",
        "README.md",
        "START_HERE.md",
        "STATUS.md",
        "TO-DO.md",
        "bandit.yaml",
        "conftest.py",
        "intent.yaml",
        "package-lock.json",
        "package.json",
        "pyproject.toml",
        "run.config.example.yaml",
        "run.sh",
        "secure_run.sh",
        "uv.lock",
    }
)
_ROOT_OBSERVATIONS = frozenset({"docs_lint.json", "lint.json", "readiness_receipt.json"})
_PROJECT_PREFIXES = frozenset(Path(name).parts for name in PUBLIC_PROJECT_NAMES)
_OUTPUT_PREFIXES = _PROJECT_PREFIXES | frozenset((Path(name).name,) for name in PUBLIC_PROJECT_NAMES) | {("readiness",)}
_PROJECT_PREFIX_DEPTHS = frozenset(len(prefix) for prefix in _PROJECT_PREFIXES)
_OUTPUT_PREFIX_DEPTHS = frozenset(len(prefix) for prefix in _OUTPUT_PREFIXES)


def _has_public_prefix(parts: tuple[str, ...], prefixes: frozenset[tuple[str, ...]], depths: frozenset[int]) -> bool:
    """Compare lexical components without reconstructing every public project path.

    These immutable sets derive only from Source's roster. Filesystem custody
    remains a fresh observation for every path and every unchanged check.
    """
    return any(parts[:depth] in prefixes for depth in depths)


def json_object_from_bytes(content: bytes) -> dict[str, Any]:
    """Decode retained JSON objects without ambiguous fields at any depth."""

    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"acceptance artifact repeats JSON field: {key}")
            result[key] = value
        return result

    value = json.loads(content, object_pairs_hook=unique_object)
    if not isinstance(value, dict):
        raise ValueError("acceptance artifact must be a JSON object")
    return value


@dataclass(frozen=True)
class ArtifactSnapshot:
    """One exact file observation; a second discovery cannot replace its facts."""

    path: Path
    relative: str
    content: bytes
    sha256: str
    identity: tuple[int, int, int, int]

    def json_object(self) -> dict[str, Any]:
        """Reject non-object evidence and ambiguous duplicate fields at any depth."""
        return json_object_from_bytes(self.content)


class SnapshotReader:
    """Read each public path once; detect mutation before the report completes."""

    def __init__(
        self,
        repo_root: Path,
        *,
        hosted_origin: Any = None,
        native_operation: Any = None,
        native_producer_operation: Any = None,
        native_control_operation: Any = None,
        operation_deadline: float | None = None,
    ) -> None:
        if operation_deadline is not None and (
            type(operation_deadline) not in (int, float) or not math.isfinite(operation_deadline)
        ):
            raise ValueError("snapshot reader needs an original finite operation deadline")
        self.root = repo_root.resolve()
        self.operation_deadline = operation_deadline
        self.hosted_origin = hosted_origin
        # Live external context only; receipt decoding never populates this.
        self.native_operation = native_operation
        # Explicit live owner only; never inferred from retained receipt DATA.
        self.native_producer_operation = native_producer_operation
        # A genuinely completed distinct original control; never receipt DATA.
        self.native_control_operation = native_control_operation
        # Cache origin authentication only; no gate or logical execution decisions.
        self.hosted_origin_authorizations: dict[str, Any] = {}
        self.snapshots: dict[Path, ArtifactSnapshot] = {}
        self.validated_exports: dict[str, str] = {}
        self.validated_export_commits: dict[str, str] = {}

    def _public_lexical_path(self, relative: str) -> Path:
        """Apply public scope policy without granting filesystem authority."""
        if not isinstance(relative, str) or not relative or "\\" in relative or "\0" in relative:
            raise ValueError("artifact path must be a public repository-relative string")
        path = Path(relative)
        if path.is_absolute() or not path.parts or ".." in path.parts:
            raise ValueError("artifact path is absolute or traverses outside public scope")
        parts = path.parts
        if any(
            part == ".private_projects_root"
            or part == ".env"
            or part.startswith(".env.")
            and not part.endswith((".example", ".template"))
            for part in parts
        ):
            raise ValueError("artifact references a private credential/control filename")
        if len(parts) == 1 and parts[0] not in PUBLIC_ROOT_FILES | _ROOT_OBSERVATIONS:
            raise ValueError("root artifact is outside the source-owned public file policy")
        if parts[0] == "projects" and not _has_public_prefix(parts[1:], _PROJECT_PREFIXES, _PROJECT_PREFIX_DEPTHS):
            raise ValueError("artifact path references a private or unknown project")
        if parts[0] == "output" and not _has_public_prefix(parts[1:], _OUTPUT_PREFIXES, _OUTPUT_PREFIX_DEPTHS):
            raise ValueError("artifact path references private or unknown output")
        if parts[0] in {"fonds", "rules", "tools"} and not path.is_relative_to(Path(parts[0]) / "templates"):
            raise ValueError("artifact references private resource state")
        if parts[0] == ".agents" and not path.is_relative_to(Path(".agents/skills")):
            raise ValueError("artifact references private agent state")
        if len(parts) > 1 and parts[0] not in {
            "projects",
            "output",
            "docs",
            "infrastructure",
            "scripts",
            "tests",
            ".github",
            "fonds",
            "rules",
            "tools",
            ".agents",
        }:
            raise ValueError("artifact path is outside public evidence roots")
        return self.root / path

    def public_path(self, relative: str) -> Path:
        """Reject private, absolute, traversal, and symlink artifact references."""
        absolute = self._public_lexical_path(relative)
        parts = Path(relative).parts
        component = absolute
        # Admission fixes exactly len(parts) lexical components below root.
        for _ in parts:
            if component.is_symlink():
                raise ValueError("artifact path contains a symlink")
            component = component.parent
        resolved = absolute.resolve()
        try:
            common: str | None = os.path.commonpath((resolved, self.root))
        except ValueError:
            common = None
        if common is None or Path(common) != self.root:
            raise ValueError("artifact path escapes the repository")
        return absolute

    @staticmethod
    def _identity(path: Path) -> tuple[int, int, int, int]:
        stat = path.stat()
        return stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns

    def read(self, relative: str, *, max_bytes: int = 64 * 1024 * 1024) -> ArtifactSnapshot:
        """Hash and parse the same bytes; refuse mid-read modification."""
        if type(max_bytes) is not int or not 0 < max_bytes <= 64 * 1024 * 1024:
            raise ValueError("snapshot requires a positive bounded byte ceiling")
        path = self.public_path(relative)
        if path not in self.snapshots:
            before = self._identity(path)
            content = read_bytes_confined(self.root, path, max_bytes=max_bytes)
            if before != self._identity(path):
                raise ValueError("acceptance artifact changed while being read")
            self.snapshots[path] = ArtifactSnapshot(
                path,
                Path(relative).as_posix(),
                content,
                hashlib.sha256(content).hexdigest(),
                before,
            )
        if len(self.snapshots[path].content) > max_bytes:
            raise ValueError("held snapshot exceeds the admitted byte ceiling")
        return self.snapshots[path]

    def unchanged(self) -> bool:
        """Check every held identity through fresh, closing-checked directories.

        A directory handle is shared only within this invocation. No path or
        inode observation authorizes a later call; Source's enclosing directory,
        Git and implementation checks remain independent.
        """
        try:
            root, snapshots = self.root, self.snapshots
            if type(snapshots) is not dict:
                return False
            held = tuple(snapshots.items())
            groups: dict[Path, list[ArtifactSnapshot]] = {}
            for path, item in held:
                if path != item.path or self._public_lexical_path(item.relative) != path:
                    return False
                groups.setdefault(path.parent, []).append(item)
            if os.open not in os.supports_dir_fd or os.stat not in os.supports_dir_fd or not hasattr(os, "O_NOFOLLOW"):
                valid = all(
                    self.public_path(item.relative) == item.path and self._identity(item.path) == item.identity
                    for _, item in held
                )
            else:
                valid = True
                for parent, items in groups.items():
                    with anchored_parent(parent / ".snapshot-directory-witness") as descriptor:
                        if descriptor is None:
                            return False
                        for item in items:
                            observed = os.stat(item.path.name, dir_fd=descriptor, follow_symlinks=False)
                            identity = observed.st_ino, observed.st_size, observed.st_mtime_ns, observed.st_ctime_ns
                            if not stat.S_ISREG(observed.st_mode) or identity != item.identity:
                                return False
            return (
                valid
                and self.root == root
                and self.snapshots is snapshots
                and len(snapshots) == len(held)
                and all(snapshots.get(path) is item for path, item in held)
            )
        except (OSError, ValueError):
            return False
