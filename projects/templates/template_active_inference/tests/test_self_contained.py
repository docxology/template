"""Standalone self-containment guard.

This template is published as its own GitHub repository, so its code must never
depend on the monorepo's ``infrastructure/`` layer or any sibling project. These
tests are the enforcement: they fail if any ``infrastructure`` (or cross-project)
import is introduced into ``src/``, ``scripts/`` or ``tests/``, and they prove —
in a clean room with ``infrastructure`` removed from the import system — that every
``src`` module imports on its own.

Pure stdlib (ast, importlib) so the guard itself is self-contained.
"""

from __future__ import annotations

import ast
import builtins
import importlib
import pkgutil
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
FORBIDDEN_ROOTS = ("infrastructure", "projects")
# Directories whose .py files must stay free of monorepo imports.
GUARDED_DIRS = ("src", "scripts", "tests")


def _forbidden_imports(py_file: Path) -> list[str]:
    """Return forbidden top-level module roots imported by ``py_file``."""
    try:
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
    except SyntaxError:  # pragma: no cover - a syntax error is a different test's job
        return []
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in FORBIDDEN_ROOTS:
                    hits.append(f"{py_file.name}: import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            # Absolute imports only (node.level == 0); relative imports stay in-package.
            if node.level == 0 and node.module:
                root = node.module.split(".")[0]
                if root in FORBIDDEN_ROOTS:
                    hits.append(f"{py_file.name}: from {node.module} import ...")
    return hits


def test_no_infrastructure_or_cross_project_imports() -> None:
    """No src/scripts/tests file imports `infrastructure` or another project."""
    violations: list[str] = []
    for rel in GUARDED_DIRS:
        base = PROJECT_ROOT / rel
        if not base.is_dir():
            continue
        for py_file in base.rglob("*.py"):
            if ".egg-info" in py_file.parts:
                continue
            violations.extend(_forbidden_imports(py_file))
    assert not violations, "monorepo imports break standalone publishability:\n" + "\n".join(violations)


def test_every_src_module_imports_with_infrastructure_blocked() -> None:
    """Clean-room proof: every src module imports with `infrastructure` removed.

    Installs an import hook that raises on any `infrastructure` import, then imports
    every discovered src module. A standalone checkout has no `infrastructure`, so a
    hidden runtime dependency would surface here, not in production.
    """
    real_import = builtins.__import__

    def blocking_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "infrastructure" or name.startswith("infrastructure."):
            raise AssertionError(f"self-containment violation: imported {name}")
        return real_import(name, *args, **kwargs)  # type: ignore[arg-type]

    violations: list[str] = []
    imported = 0
    builtins.__import__ = blocking_import  # type: ignore[assignment]
    try:
        for mod in pkgutil.walk_packages([str(SRC)]):
            try:
                importlib.import_module(mod.name)
                imported += 1
            except AssertionError as exc:
                violations.append(f"{mod.name}: {exc}")
            except Exception as exc:  # noqa: BLE001 - only infra-caused failures are violations
                if "infrastructure" in str(exc):
                    violations.append(f"{mod.name}: {exc}")
    finally:
        builtins.__import__ = real_import  # type: ignore[assignment]

    assert imported > 0, "no src modules were discovered"
    assert not violations, "src modules require infrastructure at import time:\n" + "\n".join(violations)


@pytest.mark.parametrize("required", ["pyproject.toml", "README.md", "src", "tests", "manuscript"])
def test_standalone_repo_skeleton_present(required: str) -> None:
    """A standalone GitHub repo needs these top-level entries."""
    assert (PROJECT_ROOT / required).exists(), f"standalone repo missing {required}"
