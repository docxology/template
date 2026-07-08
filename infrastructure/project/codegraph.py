"""Local CodeGraph integration helpers.

CodeGraph is an optional developer/agent index. The template treats its
``.codegraph/`` database as local generated state, never as repo data.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from infrastructure.project.git_guards import (
    ALLOWED_PROJECTS_TOPLEVEL,
    ALLOWED_PROJECT_DIRS,
)

CODEGRAPH_EXECUTABLE = "codegraph"
CODEGRAPH_INDEX_DIR = ".codegraph"
CODEGRAPH_IGNORE_ENTRIES: tuple[str, ...] = (".codegraph/", "**/.codegraph/")


@dataclass(frozen=True)
class CodeGraphCommand:
    """A shell command recommendation without executing it."""

    argv: tuple[str, ...]
    cwd: Path
    description: str

    @property
    def display(self) -> str:
        """Return a copy-pasteable command string for documentation output."""
        return " ".join(self.argv)


def is_codegraph_available(executable: str = CODEGRAPH_EXECUTABLE) -> bool:
    """Return whether the CodeGraph executable is on PATH."""
    return shutil.which(executable) is not None


def canonical_codegraph_target(path: Path) -> Path:
    """Resolve a repo or project target before building CodeGraph commands."""
    return path.expanduser().resolve()


def build_codegraph_init_command(path: Path, *, index: bool = True) -> CodeGraphCommand:
    """Build the recommended CodeGraph initialization command for ``path``."""
    target = canonical_codegraph_target(path)
    argv = [CODEGRAPH_EXECUTABLE, "init", str(target)]
    if index:
        argv.append("--index")
    return CodeGraphCommand(
        argv=tuple(argv),
        cwd=target,
        description="Initialize and optionally index a local CodeGraph target.",
    )


def build_codegraph_files_command(path: Path) -> CodeGraphCommand:
    """Build a JSON file-list command for scope verification."""
    target = canonical_codegraph_target(path)
    return CodeGraphCommand(
        argv=(CODEGRAPH_EXECUTABLE, "files", str(target), "--json"),
        cwd=target,
        description="List indexed CodeGraph files as JSON.",
    )


def build_scope_check_command(path: Path) -> CodeGraphCommand:
    """Build the first command in the CodeGraph scope verification workflow."""
    target = canonical_codegraph_target(path)
    return CodeGraphCommand(
        argv=(CODEGRAPH_EXECUTABLE, "files", str(target), "--json"),
        cwd=target,
        description=(
            "Run codegraph files as JSON, then verify that ignored private projects are absent from the index."
        ),
    )


def unexpected_indexed_project_paths(indexed_paths: Iterable[str]) -> list[str]:
    """Return indexed ``projects/`` paths outside the public template scope."""
    unexpected: list[str] = []
    for path in indexed_paths:
        normalized = path.replace("\\", "/").lstrip("./")
        if not normalized.startswith("projects/"):
            continue
        if ALLOWED_PROJECTS_TOPLEVEL.match(normalized):
            continue
        if any(normalized.startswith(prefix) for prefix in ALLOWED_PROJECT_DIRS):
            continue
        unexpected.append(normalized)
    return sorted(set(unexpected))


def extract_paths_from_files_payload(payload: str) -> list[str]:
    """Extract file paths from CodeGraph JSON output.

    CodeGraph JSON output can evolve, so this accepts common path-key shapes
    and recursively walks lists/dicts rather than binding to one schema.
    """
    data = json.loads(payload)
    paths: set[str] = set()

    def visit(value: Any) -> None:
        """Visit an AST node during traversal."""
        if isinstance(value, str):
            if "/" in value or "\\" in value:
                paths.add(value)
            return
        if isinstance(value, list):
            for item in value:
                visit(item)
            return
        if isinstance(value, dict):
            for key in ("path", "relativePath", "relative_path", "file"):
                candidate = value.get(key)
                if isinstance(candidate, str):
                    paths.add(candidate)
            for item in value.values():
                visit(item)

    visit(data)
    return sorted(paths)


def verify_codegraph_scope_payload(payload: str) -> list[str]:
    """Return private/local project paths found in a CodeGraph files payload."""
    return unexpected_indexed_project_paths(extract_paths_from_files_payload(payload))


__all__ = [
    "CODEGRAPH_EXECUTABLE",
    "CODEGRAPH_IGNORE_ENTRIES",
    "CODEGRAPH_INDEX_DIR",
    "CodeGraphCommand",
    "build_codegraph_files_command",
    "build_codegraph_init_command",
    "build_scope_check_command",
    "canonical_codegraph_target",
    "extract_paths_from_files_payload",
    "is_codegraph_available",
    "unexpected_indexed_project_paths",
    "verify_codegraph_scope_payload",
]
