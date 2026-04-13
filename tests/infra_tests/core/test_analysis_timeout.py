"""Tests for infrastructure.core.analysis_timeout."""

from __future__ import annotations

import pytest

from infrastructure.core.analysis_timeout import parse_analysis_script_timeout_sec


@pytest.mark.parametrize(
    ("env", "expected"),
    [
        ({}, 7200.0),
        ({"ANALYSIS_SCRIPT_TIMEOUT_SEC": ""}, 7200.0),
        ({"ANALYSIS_SCRIPT_TIMEOUT_SEC": "7200"}, 7200.0),
        ({"ANALYSIS_SCRIPT_TIMEOUT_SEC": " 3600 "}, 3600.0),
        ({"ANALYSIS_SCRIPT_TIMEOUT_SEC": "0"}, None),
        ({"ANALYSIS_SCRIPT_TIMEOUT_SEC": "none"}, None),
        ({"ANALYSIS_SCRIPT_TIMEOUT_SEC": "UNLIMITED"}, None),
        ({"ANALYSIS_SCRIPT_TIMEOUT_SEC": "inf"}, None),
        ({"ANALYSIS_SCRIPT_TIMEOUT_SEC": "-1"}, 7200.0),
        ({"ANALYSIS_SCRIPT_TIMEOUT_SEC": "not-a-number"}, 7200.0),
    ],
)
def test_parse_analysis_script_timeout_sec(
    env: dict[str, str], expected: float | None
) -> None:
    assert parse_analysis_script_timeout_sec(env) == expected
