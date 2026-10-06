"""Tests for infrastructure.core.analysis_timeout."""

from __future__ import annotations

import pytest

from infrastructure.core.analysis_timeout import analysis_run_timeout_seconds, parse_analysis_script_timeout_sec


@pytest.mark.parametrize(
    ("env", "expected"),
    [
        ({}, 7200.0),
        ({"ANALYSIS_SCRIPT_TIMEOUT_SEC": ""}, 7200.0),
        ({"ANALYSIS_SCRIPT_TIMEOUT_SEC": "7200"}, 7200.0),
        ({"ANALYSIS_SCRIPT_TIMEOUT_SEC": " 3600 "}, 3600.0),
        ({"ANALYSIS_SCRIPT_TIMEOUT_SEC": "0.125"}, 0.125),
    ],
)
def test_parse_analysis_script_timeout_sec(env: dict[str, str], expected: float) -> None:
    assert parse_analysis_script_timeout_sec(env) == expected


@pytest.mark.parametrize("value", ["0", "none", "UNLIMITED", "inf", "-inf", "NaN", "-1", "not-a-number"])
def test_invalid_analysis_timeout_refuses_unbounded_or_silent_fallback(value: str) -> None:
    with pytest.raises(ValueError, match="positive finite"):
        parse_analysis_script_timeout_sec({"ANALYSIS_SCRIPT_TIMEOUT_SEC": value})


def test_finite_leaf_budget_cannot_overflow_composed_run_budget() -> None:
    environment = {"ANALYSIS_SCRIPT_TIMEOUT_SEC": "1e308"}
    assert analysis_run_timeout_seconds(1, environment) == 1e308
    with pytest.raises(ValueError, match="Composed analysis run timeout must be finite"):
        analysis_run_timeout_seconds(2, environment)
    assert analysis_run_timeout_seconds(0, {}) == 0
