"""Real-behavior tests for ``infrastructure.project`` lazy imports.

No mocks — verifies the ``__getattr__`` lazy loader in the package
``__init__`` resolves public symbols to their real underlying objects.

Import order matters: importing a submodule (e.g. ``from
infrastructure.project.codegraph import …``) sets that submodule as an
attribute on the parent package, which shadows ``__getattr__``.  We
therefore resolve the lazy attribute *first* and compare it against a
fresh ``importlib`` lookup of the real object afterwards.
"""

from __future__ import annotations

import importlib

import pytest

import infrastructure.project  # noqa: F401 — import side effects are part of the test


def _real_object(module_name: str, attr: str) -> object:
    """Look up *attr* on the real submodule without polluting the parent."""
    mod = importlib.import_module(module_name)
    return getattr(mod, attr)


# ---------------------------------------------------------------------------
# Lazy resolution — each test reads the lazy attribute before importing
# the submodule directly, so ``__getattr__`` is actually exercised.
# ---------------------------------------------------------------------------


def test_public_project_names_resolves_to_real_tuple() -> None:
    """``PUBLIC_PROJECT_NAMES`` is the real tuple from ``public_scope``."""
    value = infrastructure.project.PUBLIC_PROJECT_NAMES
    real = _real_object("infrastructure.project.public_scope", "PUBLIC_PROJECT_NAMES")
    assert value is real
    assert isinstance(value, tuple)


def test_public_project_names_callable_resolves() -> None:
    """``public_project_names`` resolves to a callable."""
    func = infrastructure.project.public_project_names
    real = _real_object("infrastructure.project.public_scope", "public_project_names")
    assert func is real
    assert callable(func)


def test_codegraph_command_resolves() -> None:
    """``CodeGraphCommand`` resolves to the class from the codegraph module."""
    value = infrastructure.project.CodeGraphCommand
    real = _real_object("infrastructure.project.codegraph", "CodeGraphCommand")
    assert value is real
    assert isinstance(value, type)


def test_copy_exemplar_resolves() -> None:
    """``copy_exemplar`` resolves to the real function."""
    func = infrastructure.project.copy_exemplar
    real = _real_object("infrastructure.project.copy_exemplar", "copy_exemplar")
    assert func is real
    assert callable(func)


def test_plan_copy_resolves() -> None:
    """``plan_copy`` resolves to the real function."""
    func = infrastructure.project.plan_copy
    real = _real_object("infrastructure.project.copy_exemplar", "plan_copy")
    assert func is real
    assert callable(func)


def test_copy_result_resolves() -> None:
    """``CopyResult`` resolves to the real class."""
    value = infrastructure.project.CopyResult
    real = _real_object("infrastructure.project.copy_exemplar", "CopyResult")
    assert value is real
    assert isinstance(value, type)


def test_nonexistent_attr_raises_attribute_error() -> None:
    """Unknown attribute access raises ``AttributeError``."""
    with pytest.raises(AttributeError, match="nonexistent_attr"):
        _ = infrastructure.project.nonexistent_attr  # noqa: F841
