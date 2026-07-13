"""Structural regression tests for the SIA thin-orchestrator boundary."""

from __future__ import annotations

import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_src_never_imports_script_implementation() -> None:
    """Layer-2 source must not recover business logic from ``scripts/``."""
    for path in sorted((PROJECT_ROOT / "src").rglob("*.py")):
        modules = _imported_modules(path)
        assert "sia_loop_impl" not in modules, path
        assert all(module != "scripts" and not module.startswith("scripts.") for module in modules), path
        assert "sia_loop_impl" not in path.read_text(encoding="utf-8"), path


def test_cli_imports_project_adapter_and_legacy_module_is_absent() -> None:
    """The CLI must point inward to ``src`` and carry no second implementation."""
    script = PROJECT_ROOT / "scripts" / "run_sia_loop.py"
    assert "src.loop" in _imported_modules(script)
    assert not (PROJECT_ROOT / "scripts" / "sia_loop_impl.py").exists()
