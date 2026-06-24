"""Tests for analysis.temporal_analysis module.

Validates publication trend analysis and growth rate estimation
using hand-crafted paper datasets with known temporal patterns.
"""

import math

import pytest

from analysis.temporal_analysis import compute_temporal_metrics, estimate_growth_rate
from literature.models import Paper


# ── Helpers ───────────────────────────────────────────────────────────


def _make_papers_with_years(year_counts: dict[int, int]) -> list[Paper]:
    """Create papers with specified year distribution.

    Args:
        year_counts: Dict mapping year -> number of papers to create.

    Returns:
        List of Paper objects.
    """
    papers = []
    idx = 0
    for year, count in year_counts.items():
        for _ in range(count):
            papers.append(
                Paper(
                    title=f"Paper {idx}",
                    year=year,
                    doi=f"10.1000/p{idx}",
                )
            )
            idx += 1
    return papers


# ── compute_temporal_metrics ─────────────────────────────────────────


class TestComputeTemporalMetrics:
    """Tests for compute_temporal_metrics."""

    def test_year_counts(self):
        """Year counts match input distribution."""
        distribution = {2015: 2, 2016: 3, 2017: 5, 2018: 8}
        papers = _make_papers_with_years(distribution)
        metrics = compute_temporal_metrics(papers)

        assert metrics["year_counts"][2015] == 2
        assert metrics["year_counts"][2016] == 3
        assert metrics["year_counts"][2017] == 5
        assert metrics["year_counts"][2018] == 8

    def test_cumulative_counts(self):
        """Cumulative counts accumulate correctly."""
        distribution = {2015: 2, 2016: 3, 2017: 5, 2018: 8}
        papers = _make_papers_with_years(distribution)
        metrics = compute_temporal_metrics(papers)

        assert metrics["cumulative"][2015] == 2
        assert metrics["cumulative"][2016] == 5  # 2+3
        assert metrics["cumulative"][2017] == 10  # 2+3+5
        assert metrics["cumulative"][2018] == 18  # 2+3+5+8

    def test_first_last_year(self):
        """First and last year are correct."""
        distribution = {2015: 2, 2016: 3, 2017: 5, 2018: 8}
        papers = _make_papers_with_years(distribution)
        metrics = compute_temporal_metrics(papers)

        assert metrics["first_year"] == 2015
        assert metrics["last_year"] == 2018

    def test_total_papers(self):
        """Total papers count all papers with valid years."""
        distribution = {2015: 2, 2016: 3, 2017: 5, 2018: 8}
        papers = _make_papers_with_years(distribution)
        metrics = compute_temporal_metrics(papers)

        assert metrics["total_papers"] == 18

    def test_peak_year(self):
        """Peak year has the most publications."""
        distribution = {2015: 2, 2016: 3, 2017: 5, 2018: 8}
        papers = _make_papers_with_years(distribution)
        metrics = compute_temporal_metrics(papers)

        assert metrics["peak_year"] == 2018

    def test_gap_years_filled_with_zero(self):
        """Years with no papers between first and last are filled as 0."""
        distribution = {2015: 2, 2018: 5}
        papers = _make_papers_with_years(distribution)
        metrics = compute_temporal_metrics(papers)

        assert metrics["year_counts"][2016] == 0
        assert metrics["year_counts"][2017] == 0
        # Cumulative should reflect the gap
        assert metrics["cumulative"][2016] == 2
        assert metrics["cumulative"][2017] == 2
        assert metrics["cumulative"][2018] == 7

    def test_single_year(self):
        """Corpus with papers in only one year."""
        papers = _make_papers_with_years({2020: 10})
        metrics = compute_temporal_metrics(papers)

        assert metrics["first_year"] == 2020
        assert metrics["last_year"] == 2020
        assert metrics["total_papers"] == 10
        assert metrics["peak_year"] == 2020
        assert metrics["year_counts"] == {2020: 10}
        assert metrics["cumulative"] == {2020: 10}

    def test_papers_without_year_skipped(self):
        """Papers with year=None are excluded from metrics."""
        papers = [
            Paper(title="With Year", year=2020, doi="10.1/a"),
            Paper(title="Without Year", year=None, doi="10.1/b"),
            Paper(title="With Year 2", year=2020, doi="10.1/c"),
        ]
        metrics = compute_temporal_metrics(papers)
        assert metrics["total_papers"] == 2
        assert metrics["year_counts"] == {2020: 2}

    def test_no_valid_years_raises(self):
        """Raises ValueError when no papers have valid years."""
        papers = [Paper(title="No Year", year=None)]
        with pytest.raises(ValueError, match="No papers have a valid year"):
            compute_temporal_metrics(papers)

    def test_empty_list_raises(self):
        """Raises ValueError for empty paper list."""
        with pytest.raises(ValueError, match="No papers have a valid year"):
            compute_temporal_metrics([])


# ── estimate_growth_rate ─────────────────────────────────────────────


class TestEstimateGrowthRate:
    """Tests for estimate_growth_rate."""

    def test_annual_growth_rates(self):
        """Growth rates are computed correctly per year."""
        year_counts = {2015: 2, 2016: 4, 2017: 8, 2018: 16}
        result = estimate_growth_rate(year_counts)

        # Each year doubles: growth rate = 1.0 (100%)
        assert result["annual_growth_rates"][2016] == pytest.approx(1.0)
        assert result["annual_growth_rates"][2017] == pytest.approx(1.0)
        assert result["annual_growth_rates"][2018] == pytest.approx(1.0)

    def test_mean_growth_rate(self):
        """Mean growth rate is average of annual rates."""
        year_counts = {2015: 2, 2016: 4, 2017: 8, 2018: 16}
        result = estimate_growth_rate(year_counts)

        assert result["mean_growth_rate"] == pytest.approx(1.0)

    def test_doubling_time(self):
        """Doubling time = ln(2)/ln(1+rate)."""
        year_counts = {2015: 2, 2016: 4, 2017: 8, 2018: 16}
        result = estimate_growth_rate(year_counts)

        expected = math.log(2) / math.log(1 + 1.0)  # = 1.0 year
        assert result["doubling_time"] == pytest.approx(expected, abs=1e-6)

    def test_cagr(self):
        """CAGR = (end/start)^(1/years) - 1."""
        year_counts = {2015: 2, 2016: 4, 2017: 8, 2018: 16}
        result = estimate_growth_rate(year_counts)

        expected_cagr = (16 / 2) ** (1 / 3) - 1  # 3 years
        assert result["cagr"] == pytest.approx(expected_cagr, abs=1e-6)

    def test_zero_previous_year_skipped(self):
        """Years where previous count was 0 are skipped in growth rates."""
        year_counts = {2015: 0, 2016: 5, 2017: 10}
        result = estimate_growth_rate(year_counts)

        # 2016 growth rate is skipped (prev=0)
        assert 2016 not in result["annual_growth_rates"]
        # 2017: (10-5)/5 = 1.0
        assert result["annual_growth_rates"][2017] == pytest.approx(1.0)

    def test_declining_counts(self):
        """Negative growth when counts decrease."""
        year_counts = {2020: 10, 2021: 8, 2022: 4}
        result = estimate_growth_rate(year_counts)

        # 2021: (8-10)/10 = -0.2
        assert result["annual_growth_rates"][2021] == pytest.approx(-0.2)
        # 2022: (4-8)/8 = -0.5
        assert result["annual_growth_rates"][2022] == pytest.approx(-0.5)

    def test_doubling_time_none_for_negative_rate(self):
        """Doubling time is None when mean growth rate <= 0."""
        year_counts = {2020: 10, 2021: 8, 2022: 4}
        result = estimate_growth_rate(year_counts)

        assert result["mean_growth_rate"] < 0
        assert result["doubling_time"] is None

    def test_less_than_two_years_raises(self):
        """Raises ValueError with fewer than 2 years."""
        with pytest.raises(ValueError, match="Need at least 2 years"):
            estimate_growth_rate({2020: 5})

    def test_constant_counts(self):
        """Zero growth rate when counts are constant."""
        year_counts = {2015: 5, 2016: 5, 2017: 5}
        result = estimate_growth_rate(year_counts)

        assert result["mean_growth_rate"] == pytest.approx(0.0)
        assert result["doubling_time"] is None
        assert result["cagr"] == pytest.approx(0.0)

    def test_mixed_growth(self):
        """Mixed growth rates averaged correctly."""
        # 2015:4, 2016:8 => rate=1.0, 2017:6 => rate=-0.25
        year_counts = {2015: 4, 2016: 8, 2017: 6}
        result = estimate_growth_rate(year_counts)

        assert result["annual_growth_rates"][2016] == pytest.approx(1.0)
        assert result["annual_growth_rates"][2017] == pytest.approx(-0.25)
        assert result["mean_growth_rate"] == pytest.approx(0.375)
