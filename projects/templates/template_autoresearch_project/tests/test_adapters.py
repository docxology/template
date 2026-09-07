"""Offline second-adapter and common evidence-envelope tests."""

from __future__ import annotations

import pytest

from src.adapters import ADAPTER_RESULT_SCHEMA, available_adapters, run_quadratic_adapter


def test_quadratic_adapter_is_deterministic_and_budgeted() -> None:
    first = run_quadratic_adapter(budget=4)
    second = run_quadratic_adapter(budget=4)
    assert first == second
    assert first.selected_parameter == 1.0
    assert first.selected_metric > first.baseline_metric
    assert first.to_dict()["schema"] == ADAPTER_RESULT_SCHEMA
    assert first.to_dict()["offline"] is True


def test_adapter_registry_has_distinct_offline_task() -> None:
    assert available_adapters() == ("mnist", "quadratic_fixture")


def test_quadratic_adapter_rejects_empty_budget() -> None:
    with pytest.raises(ValueError, match="budget"):
        run_quadratic_adapter(budget=0)
