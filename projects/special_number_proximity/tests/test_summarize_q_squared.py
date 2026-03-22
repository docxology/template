"""summarize_vs_reference with optional q-squared reference."""

from __future__ import annotations

import math

import numpy as np

from statistics_compare import compare_constant_table, summarize_vs_reference


def test_summarize_includes_q_squared_when_reference_provided() -> None:
    rng = np.random.default_rng(77)
    ref_d = rng.random(80)
    ref_q2 = rng.random(80) * 0.01
    row = summarize_vs_reference("pi", math.pi, 40, ref_d, ref_q2)
    assert "min_q_squared_error" in row
    assert "empirical_percentile_rank_q_squared" in row
    assert row["use_fractional_part"] is False


def test_summarize_fractional_flag() -> None:
    rng = np.random.default_rng(78)
    ref = rng.random(60)
    row = summarize_vs_reference("pi", math.pi, 50, ref, use_fractional_part=True)
    assert row["use_fractional_part"] is True


def test_compare_constant_table_with_q2() -> None:
    rng = np.random.default_rng(79)
    d = rng.random(30)
    q2 = rng.random(30) * 0.05
    rows = compare_constant_table({"x": 0.5}, 20, d, q2)
    assert len(rows) == 1
    assert rows[0]["min_q_squared_error"] == 0.0
