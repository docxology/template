"""Extra statistics_compare helpers."""

from __future__ import annotations

import math

import numpy as np
import pytest

from statistics_compare import (
    empirical_percentile_rank,
    empirical_percentile_rank_midrank,
    reference_distribution_summary,
)


def test_midrank_at_tie() -> None:
    ref = np.array([0.1, 0.2, 0.2, 0.3])
    assert empirical_percentile_rank(0.2, ref) == 0.25
    # below=1, equal=2 → (1 + 0.5*2) / 4 = 0.5
    assert empirical_percentile_rank_midrank(0.2, ref) == pytest.approx(0.5)


def test_midrank_matches_strict_when_no_ties() -> None:
    ref = np.array([0.1, 0.2, 0.3])
    v = 0.25
    assert empirical_percentile_rank_midrank(v, ref) == pytest.approx(
        empirical_percentile_rank(v, ref)
    )


def test_midrank_empty_reference() -> None:
    empty = np.array([], dtype=np.float64)
    assert empirical_percentile_rank_midrank(0.3, empty) == 0.5


def test_reference_summary_nonempty() -> None:
    ref = np.array([0.01, 0.02, 0.03, 0.04, 0.05])
    s = reference_distribution_summary(ref)
    assert s["n"] == 5.0
    assert s["min"] == pytest.approx(0.01)
    assert s["max"] == pytest.approx(0.05)
    assert s["median"] == pytest.approx(0.03)


def test_reference_summary_empty() -> None:
    s = reference_distribution_summary(np.array([]))
    assert s["n"] == 0.0
    assert math.isnan(s["median"])
    assert math.isnan(s["p05"])
    assert math.isnan(s["p95"])


def test_reference_percentiles_direct() -> None:
    from statistics_compare import reference_percentiles

    ref = np.linspace(0.1, 1.0, 50)
    p = reference_percentiles(ref, levels=(10.0, 90.0))
    assert p["p10"] == pytest.approx(np.percentile(ref, 10))
    assert p["p90"] == pytest.approx(np.percentile(ref, 90))
