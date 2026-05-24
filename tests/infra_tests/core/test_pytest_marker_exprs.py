"""Tests for ``infrastructure/core/pytest_marker_exprs.py``."""

from __future__ import annotations

from infrastructure.core.pytest_marker_exprs import build_pytest_marker_expression


def test_default_triple_skip_matches_repo_gate() -> None:
    assert (
        build_pytest_marker_expression(
            skip_requires_ollama=True,
            skip_slow=True,
            skip_bench=True,
        )
        == (
            "not requires_ollama and not slow and not bench "
            "and not private_project and not external_fixture"
        )
    )


def test_include_slow_matches_ci_project_job_expression() -> None:
    assert (
        build_pytest_marker_expression(
            skip_requires_ollama=True,
            skip_slow=False,
            skip_bench=True,
        )
        == "not requires_ollama and not bench and not private_project and not external_fixture"
    )


def test_include_ollama_include_slow_still_skips_bench() -> None:
    assert (
        build_pytest_marker_expression(
            skip_requires_ollama=False,
            skip_slow=False,
            skip_bench=True,
        )
        == "not bench and not private_project and not external_fixture"
    )


def test_all_skips_disabled_returns_none() -> None:
    assert (
        build_pytest_marker_expression(
            skip_requires_ollama=False,
            skip_slow=False,
            skip_bench=False,
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
        )
        == "not slow and not private_project and not external_fixture"
    )
