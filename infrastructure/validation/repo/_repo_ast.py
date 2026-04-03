"""AST helpers for repository scanner import verification."""

from __future__ import annotations

import ast
from pathlib import Path

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


def _candidate_module_paths(repo_root: Path, module_name: str) -> list[Path]:
    """Return possible file locations for ``module_name`` within the repo."""
    module_path = Path(*module_name.split("."))
    candidates: list[Path] = []

    if module_path.parts:
        candidates.append(repo_root / module_path.with_suffix(".py"))
        candidates.append(repo_root / module_path / "__init__.py")

    if len(module_path.parts) == 1:
        candidates.append(repo_root / "src" / f"{module_name}.py")
        candidates.append(repo_root / "src" / module_name / "__init__.py")
        candidates.append(repo_root / "infrastructure" / f"{module_name}.py")
        candidates.append(repo_root / "infrastructure" / module_name / "__init__.py")

        projects_dir = repo_root / "projects"
        if projects_dir.is_dir():
            for src_dir in projects_dir.glob("*/src"):
                candidates.append(src_dir / f"{module_name}.py")
                candidates.append(src_dir / module_name / "__init__.py")

    # Preserve order while removing duplicates.
    return list(dict.fromkeys(candidates))


def _defined_symbols(module_path: Path) -> set[str]:
    """Return the function and class names defined in ``module_path``."""
    content = module_path.read_text(encoding="utf-8")
    tree = ast.parse(content)

    defined: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            defined.add(node.name)
        elif isinstance(node, ast.ClassDef):
            defined.add(node.name)

    return defined


def extract_imports(file_path: Path) -> dict[str, list[str]]:
    """Extract import module names and symbols from a Python file."""
    imports: dict[str, list[str]] = {}
    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports[alias.name] = []
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    if module not in imports:
                        imports[module] = []
                    imports[module].append(alias.name)
    except (OSError, UnicodeDecodeError, SyntaxError) as e:
        logger.debug("Failed to parse imports from script: %s", e)

    return imports


def verify_import(repo_root: Path, module_name: str, items: list[str]) -> bool:
    """Return True if all named symbols exist in a matching repo module."""
    for module_path in _candidate_module_paths(repo_root, module_name):
        if not module_path.exists():
            continue

        try:
            defined = _defined_symbols(module_path)
        except (OSError, UnicodeDecodeError, SyntaxError) as e:
            logger.debug("Failed to verify imports in module %s: %s", module_name, e)
            continue

        if all(item in defined for item in items):
            return True

    return False
