"""Real-behavior tests for ``infrastructure.benchmark`` lazy imports.

No mocks — verifies the ``__getattr__`` lazy loader in the package
``__init__`` resolves public symbols to their real underlying objects.

Import order matters: importing a submodule directly sets it as an
attribute on the parent package, which shadows ``__getattr__``.  We
therefore resolve the lazy attribute *first* and compare it against a
fresh ``importlib`` lookup of the real object afterwards.
"""

from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path

import pytest

import infrastructure.benchmark  # noqa: F401 — import side effects are part of the test


def _real_object(module_name: str, attr: str) -> object:
    """Look up *attr* on the real submodule without polluting the parent."""
    mod = importlib.import_module(module_name)
    return getattr(mod, attr)


# ---------------------------------------------------------------------------
# Lazy resolution — each test reads the lazy attribute before importing
# the submodule directly, so ``__getattr__`` is actually exercised.
# ---------------------------------------------------------------------------


def test_rubric_score_resolves() -> None:
    """``RubricScore`` resolves to the class from the rubrics module."""
    value = infrastructure.benchmark.RubricScore
    real = _real_object("infrastructure.benchmark.rubrics", "RubricScore")
    assert value is real
    assert isinstance(value, type)


def test_rubric_set_resolves() -> None:
    """``RubricSet`` resolves to the class from the rubrics module."""
    value = infrastructure.benchmark.RubricSet
    real = _real_object("infrastructure.benchmark.rubrics", "RubricSet")
    assert value is real
    assert isinstance(value, type)


def test_score_rubric_resolves() -> None:
    """``score_rubric`` resolves to the real function from the rubrics module."""
    func = infrastructure.benchmark.score_rubric
    real = _real_object("infrastructure.benchmark.rubrics", "score_rubric")
    assert func is real
    assert callable(func)


def test_benchmark_manifest_resolves() -> None:
    """``BenchmarkManifest`` resolves from the template_harness module."""
    value = infrastructure.benchmark.BenchmarkManifest
    real = _real_object("infrastructure.benchmark.template_harness", "BenchmarkManifest")
    assert value is real
    assert isinstance(value, type)


def test_load_benchmark_manifest_resolves() -> None:
    """``load_benchmark_manifest`` resolves from the template_harness module."""
    func = infrastructure.benchmark.load_benchmark_manifest
    real = _real_object("infrastructure.benchmark.template_harness", "load_benchmark_manifest")
    assert func is real
    assert callable(func)


def test_nonexistent_attr_raises_attribute_error() -> None:
    """Unknown attribute access raises ``AttributeError``."""
    with pytest.raises(AttributeError, match="nonexistent"):
        _ = infrastructure.benchmark.nonexistent  # noqa: F841


def test_package_module_exposes_real_cli_help() -> None:
    """The documented package command must resolve to the real harness CLI."""
    repo_root = Path(__file__).resolve().parents[3]
    result = subprocess.run(
        [sys.executable, "-m", "infrastructure.benchmark", "--help"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Run template benchmark manifests" in result.stdout
