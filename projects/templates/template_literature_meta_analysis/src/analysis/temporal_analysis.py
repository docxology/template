"""Publication trend analysis for the literature corpus.

Computes temporal metrics such as publication counts per year,
cumulative growth, annual growth rates, and doubling times.
"""

from __future__ import annotations

import logging
import math
from collections import Counter

from literature.models import Paper

logger = logging.getLogger(__name__)


def compute_temporal_metrics(papers: list[Paper]) -> dict:
    """Compute temporal publication metrics from a list of papers.

    Args:
        papers: List of Paper objects (papers without a year are skipped).

    Returns:
        Dictionary with keys:
            year_counts: Dict mapping year (int) -> count
            cumulative: Dict mapping year (int) -> cumulative count
            first_year: Earliest publication year
            last_year: Latest publication year
            total_papers: Total number of papers with valid years
            peak_year: Year with the most publications

    Raises:
        ValueError: If no papers have a valid year.
    """
    # Filter papers that have a valid year
    years = [p.year for p in papers if p.year is not None]

    if not years:
        raise ValueError("No papers have a valid year")

    year_counts_raw = Counter(years)
    first_year = min(year_counts_raw)
    last_year = max(year_counts_raw)

    # Build complete year range (fill gaps with 0)
    year_counts: dict[int, int] = {}
    for yr in range(first_year, last_year + 1):
        year_counts[yr] = year_counts_raw.get(yr, 0)

    # Cumulative counts
    cumulative: dict[int, int] = {}
    running = 0
    for yr in range(first_year, last_year + 1):
        running += year_counts[yr]
        cumulative[yr] = running

    # Peak year: year with maximum count; ties go to earliest
    peak_year = max(year_counts, key=lambda y: (year_counts[y], -y))

    # 3-year moving average for annual counts
    smoothed_annual: dict[int, float] = {}
    sorted_years = sorted(year_counts.keys())
    for i, yr in enumerate(sorted_years):
        window = []
        for j in range(max(0, i - 1), min(len(sorted_years), i + 2)):
            window.append(year_counts[sorted_years[j]])
        smoothed_annual[yr] = sum(window) / len(window) if window else 0.0

    return {
        "year_counts": year_counts,
        "smoothed_annual": smoothed_annual,
        "cumulative": cumulative,
        "first_year": first_year,
        "last_year": last_year,
        "total_papers": len(years),
        "peak_year": peak_year,
    }


def estimate_growth_rate(year_counts: dict[int, int]) -> dict:
    """Estimate annual growth rates from year-count data.

    Args:
        year_counts: Dictionary mapping year (int) -> publication count.

    Returns:
        Dictionary with keys:
            annual_growth_rates: Dict of year -> fractional growth rate
                (only for years where the previous year had > 0 papers)
            mean_growth_rate: Average of the annual growth rates
            doubling_time: Estimated years to double at the mean rate
                (ln(2) / ln(1 + mean_growth_rate)), or None if rate <= 0
            cagr: Compound annual growth rate over the full period

    Raises:
        ValueError: If year_counts has fewer than 2 entries.
    """
    if len(year_counts) < 2:
        raise ValueError("Need at least 2 years to compute growth rates")

    sorted_years = sorted(year_counts.keys())

    # Annual growth rates
    annual_growth_rates: dict[int, float] = {}
    for i in range(1, len(sorted_years)):
        prev_year = sorted_years[i - 1]
        curr_year = sorted_years[i]
        prev_count = year_counts[prev_year]
        curr_count = year_counts[curr_year]

        if prev_count > 0:
            rate = (curr_count - prev_count) / prev_count
            annual_growth_rates[curr_year] = rate
        elif curr_count > 0:
            # Zero-to-non-zero: field emergence; log but exclude from mean
            logger.debug(
                "Year %d had 0 prior-year papers → %d (emergence year, excluded from mean growth)",
                curr_year,
                curr_count,
            )

    # Mean growth rate
    if annual_growth_rates:
        mean_growth_rate = sum(annual_growth_rates.values()) / len(annual_growth_rates)
    else:
        mean_growth_rate = 0.0

    # Doubling time
    if mean_growth_rate > 0:
        doubling_time = math.log(2) / math.log(1 + mean_growth_rate)
    else:
        doubling_time = None

    # CAGR: (end_year_count / start_year_count)^(1/years) - 1
    # Standard bibliometric measure: annualised growth rate of yearly
    # publication volume between the first and last observed years.
    # Measures field *activity* growth, not cumulative corpus size growth.
    first_year = sorted_years[0]
    last_year = sorted_years[-1]
    n_years = last_year - first_year

    start_count = year_counts[first_year]
    end_count = year_counts[last_year]

    if start_count == 0:
        cagr = float("inf") if end_count > 0 else 0.0
    elif n_years > 0 and end_count > 0:
        cagr = (end_count / start_count) ** (1 / n_years) - 1
    else:
        cagr = 0.0

    return {
        "annual_growth_rates": annual_growth_rates,
        "mean_growth_rate": mean_growth_rate,
        "doubling_time": doubling_time,
        "cagr": cagr,
    }


def compute_subfield_timeline(
    classified: dict[str, list[Paper]],
) -> dict[str, dict[str, int]]:
    """Build per-subfield publication counts keyed by year string.

    Args:
        classified: Mapping of subfield name to papers in that subfield.

    Returns:
        ``{subfield: {year_str: count}}`` omitting subfields with no dated papers.
    """
    timeline: dict[str, dict[str, int]] = {}
    for subfield, papers in classified.items():
        year_counts: dict[str, int] = {}
        for paper in papers:
            if paper.year is not None:
                year_key = str(paper.year)
                year_counts[year_key] = year_counts.get(year_key, 0) + 1
        if year_counts:
            timeline[subfield] = year_counts
    return timeline
