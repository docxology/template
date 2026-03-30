"""AST helpers for repository scanner import verification."""

from __future__ import annotations

import ast
from pathlib import Path

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


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
    """Return True if all named symbols exist in repo_root/src/{module_name}.py."""
    module_path = repo_root / "src" / f"{module_name}.py"
    if not module_path.exists():
        return False

    try:
        content = module_path.read_text(encoding="utf-8")
        tree = ast.parse(content)

        defined: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                defined.add(node.name)
            elif isinstance(node, ast.ClassDef):
                defined.add(node.name)

        return all(item in defined for item in items)
    except (OSError, UnicodeDecodeError, SyntaxError) as e:
        logger.debug("Failed to verify imports in module %s: %s", module_name, e)
        return False
