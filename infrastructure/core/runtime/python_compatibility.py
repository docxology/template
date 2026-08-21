"""Static Python 3.10 syntax and standard-library compatibility audit."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class PythonCompatibilityIssue:
    """One unguarded source construct unavailable on Python 3.10."""

    path: str
    line: int
    rule: str
    message: str


_POST_310_IMPORTS: dict[str, frozenset[str]] = {
    "asyncio": frozenset({"TaskGroup"}),
    "datetime": frozenset({"UTC"}),
    "enum": frozenset({"StrEnum"}),
    "typing": frozenset({"LiteralString", "NotRequired", "Required", "Self", "TypeVarTuple", "Unpack"}),
}
_POST_310_ATTRIBUTES: dict[str, frozenset[str]] = {
    "asyncio": frozenset({"TaskGroup"}),
    "datetime": frozenset({"UTC"}),
    "enum": frozenset({"StrEnum"}),
    "typing": frozenset({"LiteralString", "NotRequired", "Required", "Self", "TypeVarTuple", "Unpack"}),
}


def scan_python_310_compatibility(
    paths: Iterable[Path],
    *,
    repo_root: Path,
) -> tuple[PythonCompatibilityIssue, ...]:
    """Scan Python files for 3.10-incompatible syntax and unguarded APIs."""
    issues: list[PythonCompatibilityIssue] = []
    resolved_root = repo_root.resolve()
    for source_path, display in _python_files_and_displays(paths, resolved_root):
        try:
            source = source_path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(source_path), feature_version=(3, 10))
        except SyntaxError as exc:
            issues.append(
                PythonCompatibilityIssue(
                    display,
                    exc.lineno or 0,
                    "PY310.SYNTAX",
                    exc.msg,
                )
            )
            continue
        except (OSError, UnicodeError) as exc:
            issues.append(PythonCompatibilityIssue(display, 0, "PY310.READ", str(exc)))
            continue

        # Fast path: only build parent map and inspect AST nodes if the source
        # contains potential post-3.10 identifiers or imports.
        if any(
            token in source
            for token in (
                "tomllib",
                "TaskGroup",
                "UTC",
                "StrEnum",
                "LiteralString",
                "NotRequired",
                "Required",
                "Self",
                "TypeVarTuple",
                "Unpack",
            )
        ):
            parents = _parent_map(tree)
            issues.extend(_api_issues(tree, parents, display))
    return tuple(sorted(issues, key=lambda issue: (issue.path, issue.line, issue.rule)))


def _python_files_and_displays(paths: Iterable[Path], resolved_root: Path) -> tuple[tuple[Path, str], ...]:
    """Enumerate source files, resolving each path exactly ONCE.

    Each candidate is resolved a single time; the resolved path keys the
    de-duplication dict and the resolved path + ``resolved_root`` produce the
    display string, so ``scan_python_310_compatibility`` performs no second
    filesystem resolution pass over the source tree.
    """
    entries: dict[str, tuple[Path, str]] = {}
    for path in paths:
        candidates = (path,) if path.is_file() else path.rglob("*.py") if path.is_dir() else ()
        for candidate in candidates:
            if any(part in {".venv", "__pycache__", "site-packages"} for part in candidate.parts):
                continue
            resolved = candidate.resolve()
            entries[resolved.as_posix()] = (resolved, _display_path(resolved, resolved_root))
    return tuple(entries[key] for key in sorted(entries))


def _parent_map(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    return {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}


def _api_issues(
    tree: ast.AST,
    parents: dict[ast.AST, ast.AST],
    path: str,
) -> list[PythonCompatibilityIssue]:
    issues: list[PythonCompatibilityIssue] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "tomllib" and not _is_compatibility_guarded(node, parents):
                    issues.append(_api_issue(path, node, "tomllib"))
        elif isinstance(node, ast.ImportFrom):
            unavailable = _POST_310_IMPORTS.get(node.module or "", frozenset())
            for alias in node.names:
                if alias.name in unavailable and not _is_compatibility_guarded(node, parents):
                    issues.append(_api_issue(path, node, f"{node.module}.{alias.name}"))
        elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            unavailable = _POST_310_ATTRIBUTES.get(node.value.id, frozenset())
            if node.attr in unavailable and not _is_compatibility_guarded(node, parents):
                issues.append(_api_issue(path, node, f"{node.value.id}.{node.attr}"))
    return issues


def _is_compatibility_guarded(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> bool:
    current = parents.get(node)
    while current is not None:
        if isinstance(current, ast.Try) and any(_handler_catches_import_error(handler) for handler in current.handlers):
            return True
        if isinstance(current, ast.If) and "version_info" in ast.unparse(current.test):
            return True
        current = parents.get(current)
    return False


def _handler_catches_import_error(handler: ast.ExceptHandler) -> bool:
    names: set[str] = set()
    if isinstance(handler.type, ast.Name):
        names.add(handler.type.id)
    elif isinstance(handler.type, ast.Tuple):
        names.update(item.id for item in handler.type.elts if isinstance(item, ast.Name))
    return bool(names & {"ImportError", "ModuleNotFoundError"})


def _api_issue(path: str, node: ast.AST, api: str) -> PythonCompatibilityIssue:
    return PythonCompatibilityIssue(
        path,
        getattr(node, "lineno", 0),
        "PY310.API",
        f"{api} requires Python 3.11+; guard it and provide a 3.10 fallback",
    )


def _display_path(path: Path, resolved_root: Path) -> str:
    """Return *path* (already resolved) relative to *resolved_root*.

    ``resolved_root`` is resolved once by the caller; ``path`` is pre-resolved
    by ``_python_files_and_displays``, so this performs no filesystem syscalls.
    """
    try:
        return path.relative_to(resolved_root).as_posix()
    except ValueError:
        return path.as_posix()


__all__ = ["PythonCompatibilityIssue", "scan_python_310_compatibility"]
