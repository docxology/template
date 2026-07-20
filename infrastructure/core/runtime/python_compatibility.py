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
    for source_path in _python_files(paths):
        display = _display_path(source_path, repo_root)
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
        parents = _parent_map(tree)
        issues.extend(_api_issues(tree, parents, display))
    return tuple(sorted(issues, key=lambda issue: (issue.path, issue.line, issue.rule)))


def _python_files(paths: Iterable[Path]) -> tuple[Path, ...]:
    files: dict[str, Path] = {}
    for path in paths:
        candidates = (path,) if path.is_file() else path.rglob("*.py") if path.is_dir() else ()
        for candidate in candidates:
            if any(part in {".venv", "__pycache__", "site-packages"} for part in candidate.parts):
                continue
            files[candidate.resolve().as_posix()] = candidate
    return tuple(files[key] for key in sorted(files))


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


def _display_path(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


__all__ = ["PythonCompatibilityIssue", "scan_python_310_compatibility"]
