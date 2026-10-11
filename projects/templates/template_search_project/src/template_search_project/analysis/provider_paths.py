"""Resolve the actual selected platform package for project review inventories."""

from __future__ import annotations

import ast
from collections.abc import Iterator
from pathlib import Path

import infrastructure


def platform_package_root() -> Path:
    """Use the loaded provider origin, whether a checkout or installed wheel."""
    origin = infrastructure.__file__
    if origin is None:
        raise ValueError("the selected platform package has no source origin")
    package = Path(origin).resolve(strict=True).parent
    if not (package / "__init__.py").is_file():
        raise ValueError("the selected platform package has no Python source directory")
    return package


def platform_import_modules(tree: ast.AST) -> Iterator[str]:
    """Yield absolute platform modules for both supported Python import forms."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            modules = [node.module]
        else:
            continue
        for module in modules:
            if module == "infrastructure" or module.startswith("infrastructure."):
                yield module


def platform_module_exists(module: str, package_root: Path) -> bool:
    """Check a module's actual Python source without executing its imports."""
    if module == "infrastructure":
        return (package_root / "__init__.py").is_file()
    relative = Path(*module.split(".")[1:])
    return (package_root / relative.with_suffix(".py")).is_file() or (package_root / relative / "__init__.py").is_file()
