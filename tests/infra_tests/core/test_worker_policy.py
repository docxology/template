"""Tests for the shared bounded worker policy."""

from __future__ import annotations

import pytest

from infrastructure.core.worker_policy import clamp_worker_count, resolve_bounded_workers


def test_explicit_worker_count_is_capped_to_items() -> None:
    assert clamp_worker_count(8, 3) == 3


def test_worker_count_rejects_non_positive_requests() -> None:
    with pytest.raises(ValueError, match="workers must be positive"):
        clamp_worker_count(0, 3)


def test_environment_override_is_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TEMPLATE_PROJECT_WORKERS", "8")
    assert (
        resolve_bounded_workers(
            env_name="TEMPLATE_PROJECT_WORKERS",
            item_count=3,
            default_cap=4,
            cpu_reserve=1,
        )
        == 3
    )


def test_invalid_environment_can_fall_back(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MULTI_PROJECT_MAX_WORKERS", "invalid")
    assert resolve_bounded_workers(env_name="MULTI_PROJECT_MAX_WORKERS", item_count=2, invalid="fallback") >= 1


def test_invalid_environment_can_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PYTEST_XDIST_WORKERS", "invalid")
    with pytest.raises(ValueError, match="PYTEST_XDIST_WORKERS"):
        resolve_bounded_workers(env_name="PYTEST_XDIST_WORKERS")
