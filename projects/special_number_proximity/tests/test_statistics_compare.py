"""Tests for batch statistics and comparison helpers."""

import math

import numpy as np
import pytest

from statistics_compare import (
    batch_min_q_squared_errors,
    batch_min_rational_distances,
    compare_constant_table,
    empirical_percentile_rank,
    reference_percentiles,
    summarize_vs_reference,
)


def test_batch_min_rational_distances() -> None:
    xs = np.array([0.25, 1.0 / 3.0, math.pi])
    d = batch_min_rational_distances(xs, q_max=20)
    assert d.shape == (3,)
    assert d[0] == 0.0
    assert d[1] == 0.0
    assert d[2] > 0.0


def test_empirical_percentile_rank_edges() -> None:
    ref = np.array([0.1, 0.2, 0.3, 0.4])
    assert empirical_percentile_rank(0.05, ref) == 0.0
    assert empirical_percentile_rank(0.5, ref) == 1.0


def test_empirical_percentile_rank_empty_reference() -> None:
    assert empirical_percentile_rank(0.1, np.array([])) == 0.5


def test_summarize_vs_reference_keys() -> None:
    rng = np.random.default_rng(42)
    ref = batch_min_rational_distances(rng.random(200), q_max=40)
    row = summarize_vs_reference("pi", math.pi, 40, ref)
    assert row["name"] == "pi"
    assert row["q_max"] == 40
    assert "min_distance" in row
    assert row["reference_n"] == 200
    assert row["use_fractional_part"] is False


def test_compare_constant_table() -> None:
    rng = np.random.default_rng(7)
    ref = batch_min_rational_distances(rng.random(50), q_max=25)
    rows = compare_constant_table({"a": 0.5, "b": math.sqrt(2.0)}, 25, ref)
    assert len(rows) == 2
    assert {r["name"] for r in rows} == {"a", "b"}


def test_batch_min_rational_distances_empty_auto() -> None:
    out = batch_min_rational_distances(np.array([]), q_max=10, implementation="auto")
    assert out.size == 0


def test_batch_min_rational_distances_vectorized_empty() -> None:
    out = batch_min_rational_distances(np.array([]), q_max=10, implementation="vectorized")
    assert out.size == 0


def test_batch_scalar_matches_vectorized() -> None:
    rng = np.random.default_rng(11)
    xs = rng.random(24)
    q_max = 22
    a = batch_min_rational_distances(xs, q_max, implementation="scalar")
    b = batch_min_rational_distances(xs, q_max, implementation="vectorized")
    np.testing.assert_allclose(a, b, rtol=0.0, atol=1e-14)


def test_batch_min_q_squared_scalar_matches_vectorized() -> None:
    rng = np.random.default_rng(13)
    xs = rng.random(18)
    q_max = 16
    a = batch_min_q_squared_errors(xs, q_max, implementation="scalar")
    b = batch_min_q_squared_errors(xs, q_max, implementation="vectorized")
    np.testing.assert_allclose(a, b, rtol=0.0, atol=1e-14)


def test_batch_min_q_squared_empty() -> None:
    out = batch_min_q_squared_errors(np.array([]), q_max=8, implementation="auto")
    assert out.size == 0
    out_v = batch_min_q_squared_errors(np.array([]), q_max=8, implementation="vectorized")
    assert out_v.size == 0


def test_reference_percentiles_nonempty_and_empty() -> None:
    ref = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    p = reference_percentiles(ref)
    assert p["p50"] == pytest.approx(3.0)
    empty = reference_percentiles(np.array([]))
    assert math.isnan(empty["p50"])


def test_summarize_vs_reference_with_q_squared_and_fractional() -> None:
    rng = np.random.default_rng(19)
    ref_d = batch_min_rational_distances(rng.random(80), q_max=35)
    ref_q = batch_min_q_squared_errors(rng.random(80), q_max=35)
    row = summarize_vs_reference("pi", math.pi, 35, ref_d, ref_q)
    assert "min_q_squared_error" in row
    assert "empirical_percentile_rank_q_squared" in row
    row_frac = summarize_vs_reference(
        "big_pi",
        math.pi + 100.0,
        35,
        ref_d,
        ref_q,
        use_fractional_part=True,
    )
    row_plain = summarize_vs_reference("pi", math.pi, 35, ref_d, ref_q)
    assert row_frac["min_distance"] == pytest.approx(row_plain["min_distance"], rel=0.0, abs=1e-12)


def test_compare_constant_table_with_q_squared() -> None:
    rng = np.random.default_rng(23)
    ref_d = batch_min_rational_distances(rng.random(60), q_max=28)
    ref_q = batch_min_q_squared_errors(rng.random(60), q_max=28)
    rows = compare_constant_table(
        {"e": math.e},
        28,
        ref_d,
        reference_q_squared=ref_q,
    )
    assert len(rows) == 1
    assert "min_q_squared_error" in rows[0]
