"""Tests for ``infrastructure/core/pytest_marker_exprs.py``."""

from __future__ import annotations

import shlex
import tomllib
from pathlib import Path

from infrastructure.core.testing.pytest_marker_exprs import (
    build_pytest_marker_expression,
    repository_marker_expression,
)

ROOT = Path(__file__).resolve().parents[3]


def _addopts_marker_expression(root: Path) -> str:
    """Return the ``-m`` expression pytest receives from ``pyproject.toml``."""
    metadata = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    addopts = metadata["tool"]["pytest"]["ini_options"]["addopts"]
    arguments = shlex.split(addopts)
    return arguments[arguments.index("-m") + 1]


def test_pyproject_addopts_marker_expression_matches_builder() -> None:
    """The inline ``addopts`` text may not drift from the builder's defaults."""
    assert _addopts_marker_expression(ROOT) == repository_marker_expression()


def test_default_triple_skip_matches_repo_gate() -> None:
    assert build_pytest_marker_expression(
        skip_requires_ollama=True,
        skip_slow=True,
        skip_bench=True,
    ) == (
        "not requires_ollama and not requires_docker and not network and not slow and not bench and not benchmark "
        "and not performance and not long_running and not private_project "
        "and not external_fixture"
    )


def test_include_slow_still_skips_long_running_ci_project_job_expression() -> None:
    assert (
        build_pytest_marker_expression(
            skip_requires_ollama=True,
            skip_slow=False,
            skip_bench=True,
        )
        == "not requires_ollama and not requires_docker and not network and not bench and not benchmark and not performance and not long_running and not private_project and not external_fixture"
    )


def test_include_ollama_include_slow_still_skips_bench() -> None:
    assert (
        build_pytest_marker_expression(
            skip_requires_ollama=False,
            skip_slow=False,
            skip_bench=True,
        )
        == "not requires_docker and not network and not bench and not benchmark and not performance and not long_running and not private_project and not external_fixture"
    )


def test_all_skips_disabled_returns_none() -> None:
    assert (
        build_pytest_marker_expression(
            skip_requires_ollama=False,
            skip_slow=False,
            skip_bench=False,
            skip_requires_docker=False,
            skip_network=False,
            skip_long_running=False,
            skip_private_project=False,
            skip_external_fixture=False,
        )
        is None
    )


def test_only_slow_skip() -> None:
    assert (
        build_pytest_marker_expression(
            skip_requires_ollama=False,
            skip_slow=True,
            skip_bench=False,
            skip_requires_docker=False,
            skip_network=False,
        )
        == "not slow and not long_running and not private_project and not external_fixture"
    )


def test_include_long_running_omits_long_running_filter() -> None:
    assert (
        build_pytest_marker_expression(
            skip_requires_ollama=True,
            skip_slow=False,
            skip_bench=True,
            skip_long_running=False,
        )
        == "not requires_ollama and not requires_docker and not network and not bench and not benchmark and not performance and not private_project and not external_fixture"
    )
