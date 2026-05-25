"""Marker contracts for LLM integration tests."""

from __future__ import annotations

import ast
from pathlib import Path


LLM_TEST_DIR = Path(__file__).parent


def _decorator_names(node: ast.ClassDef) -> set[str]:
    names: set[str] = set()
    for decorator in node.decorator_list:
        current: ast.expr = decorator.func if isinstance(decorator, ast.Call) else decorator
        while isinstance(current, ast.Attribute):
            names.add(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            names.add(current.id)
    return names


def _uses_real_ollama_fixture(node: ast.ClassDef) -> bool:
    for item in node.body:
        if not isinstance(item, ast.FunctionDef):
            continue
        if any(arg.arg == "ensure_ollama_for_tests" for arg in item.args.args):
            return True
    return False


def test_classes_using_real_ollama_fixture_are_marked_requires_ollama() -> None:
    offenders: list[str] = []
    for path in sorted(LLM_TEST_DIR.glob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            if _uses_real_ollama_fixture(node) and "requires_ollama" not in _decorator_names(node):
                offenders.append(f"{path.name}:{node.name}")

    assert offenders == []
