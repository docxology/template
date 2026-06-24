"""Tests for analysis.descriptive_stats module.

Validates descriptive bibliometric statistics, the citation distribution and
Gini coefficient, author-productivity ranking, and the consolidated meta-report
artifact using a small hand-constructed corpus whose every statistic is
computed independently by hand (never green-by-construction).
"""

import json

import pytest

from analysis.descriptive_stats import (
    author_productivity,
    build_meta_report,
    citation_distribution,
    descriptive_stats,
    save_meta_report,
)
from literature.models import Author, Paper


# ── Hand-constructed corpus with fully known values ──────────────────────
#
# P1: 2020, "Neural Computation", [Friston, Parr],      cites=0,   abstract="A", doi set,    OA=True
# P2: 2020, "Neural Computation", [Friston, Da Costa],  cites=5,   abstract="B", doi=None,   OA=False
# P3: 2021, "Entropy",            [Friston],            cites=12,  abstract="",  doi set,    OA=None
# P4: 2021, None (no venue),      [Parr, Da Costa],     cites=80,  abstract="D", doi set,    OA=True
# P5: 2022, "Entropy",            [Friston, Parr],      cites=600, abstract="E", doi set,    OA=None
#
# Derived by hand (used as the reference values asserted below):
#   total = 5
#   years -> {2020: 2, 2021: 2, 2022: 1}; min 2020, max 2022
#   venues -> Entropy: 2, Neural Computation: 2 (None skipped)
#   author paper-counts -> Friston: 4, Parr: 3, Da Costa: 2  (unique authors = 3)
#       sorted multiset [2, 3, 4] -> mean 3.0, median 3.0
#   citations [0, 5, 12, 80, 600] -> mean 139.4, median 12, max 600, total 697
#   OA flags present: [True, False, True] -> 2/3 -> 66.666...%
#   abstracts non-empty: 4/5 -> 80.0%
#   dois present: 4/5 -> 80.0%


def _corpus() -> list[Paper]:
    """Return the hand-constructed reference corpus."""
    friston = Author(name="Friston")
    parr = Author(name="Parr")
    da_costa = Author(name="Da Costa")
    return [
        Paper(
            title="P1",
            abstract="A",
            authors=[friston, parr],
            year=2020,
            venue="Neural Computation",
            doi="10.1/a",
            citation_count=0,
            is_open_access=True,
        ),
        Paper(
            title="P2",
            abstract="B",
            authors=[friston, da_costa],
            year=2020,
            venue="Neural Computation",
            doi=None,
            citation_count=5,
            is_open_access=False,
        ),
        Paper(
            title="P3",
            abstract="",
            authors=[friston],
            year=2021,
            venue="Entropy",
            doi="10.3/c",
            citation_count=12,
            is_open_access=None,
        ),
        Paper(
            title="P4",
            abstract="D",
            authors=[parr, da_costa],
            year=2021,
            venue=None,
            doi="10.4/d",
            citation_count=80,
            is_open_access=True,
        ),
        Paper(
            title="P5",
            abstract="E",
            authors=[friston, parr],
            year=2022,
            venue="Entropy",
            doi="10.5/e",
            citation_count=600,
            is_open_access=None,
        ),
    ]


def _brute_force_gini(values: list[int]) -> float:
    """Independent reference Gini via an explicit pairwise double loop.

    This deliberately re-derives the Gini coefficient with a different,
    slower implementation than the module's vectorized version so the
    assertion binds to an external reference rather than the function output.
    """
    if not values:
        return 0.0
    n = len(values)
    mean = sum(values) / n
    if mean == 0.0:
        return 0.0
    total_diff = 0.0
    for x_i in values:
        for x_j in values:
            total_diff += abs(x_i - x_j)
    return total_diff / (2 * (n**2) * mean)


# ── descriptive_stats ────────────────────────────────────────────────────


class TestDescriptiveStats:
    """Tests for descriptive_stats against hand-computed references."""

    def test_total_and_year_bounds(self):
        """Total count and year min/max match the corpus."""
        stats = descriptive_stats(_corpus())
        assert stats["total"] == 5
        assert stats["year_min"] == 2020
        assert stats["year_max"] == 2022

    def test_counts_by_year(self):
        """Year histogram matches the hand-computed distribution."""
        stats = descriptive_stats(_corpus())
        assert stats["counts_by_year"] == {2020: 2, 2021: 2, 2022: 1}
        # Sorted ascending in insertion order.
        assert list(stats["counts_by_year"].keys()) == [2020, 2021, 2022]

    def test_counts_by_venue_sorted_and_skips_none(self):
        """Venue counts skip None venues and tie-break by name ascending."""
        stats = descriptive_stats(_corpus())
        assert stats["counts_by_venue"] == {"Entropy": 2, "Neural Computation": 2}
        # Equal counts -> alphabetical: Entropy before Neural Computation.
        assert list(stats["counts_by_venue"].keys()) == [
            "Entropy",
            "Neural Computation",
        ]

    def test_counts_by_venue_top_limit(self):
        """top_venues truncates to the requested number of venues."""
        stats = descriptive_stats(_corpus(), top_venues=1)
        assert stats["counts_by_venue"] == {"Entropy": 2}

    def test_author_summaries(self):
        """Unique-author count and per-author mean/median match by hand."""
        stats = descriptive_stats(_corpus())
        assert stats["unique_authors"] == 3
        # Multiset of per-author paper counts is [2, 3, 4].
        assert stats["papers_per_author_mean"] == 3.0
        assert stats["papers_per_author_median"] == 3.0

    def test_citation_summaries(self):
        """Citation mean/median/max/total match hand-computed references."""
        stats = descriptive_stats(_corpus())
        # [0, 5, 12, 80, 600]: sum 697, mean 139.4, median 12.
        assert stats["citation_count_total"] == 697
        assert stats["citation_count_mean"] == pytest.approx(139.4)
        assert stats["citation_count_median"] == 12
        assert stats["citation_count_max"] == 600

    def test_percentages(self):
        """Open-access/abstract/doi percentages use the right denominators."""
        stats = descriptive_stats(_corpus())
        # OA denominator excludes None flags: [True, False, True] -> 2/3.
        assert stats["pct_open_access"] == pytest.approx(200.0 / 3.0)
        # Abstracts: 4 of 5 non-empty; DOIs: 4 of 5 present.
        assert stats["pct_with_abstract"] == pytest.approx(80.0)
        assert stats["pct_with_doi"] == pytest.approx(80.0)

    def test_empty_corpus(self):
        """Empty corpus yields zeros/None with no division errors."""
        stats = descriptive_stats([])
        assert stats["total"] == 0
        assert stats["year_min"] is None
        assert stats["year_max"] is None
        assert stats["counts_by_year"] == {}
        assert stats["counts_by_venue"] == {}
        assert stats["unique_authors"] == 0
        assert stats["papers_per_author_mean"] == 0.0
        assert stats["papers_per_author_median"] == 0.0
        assert stats["citation_count_mean"] == 0.0
        assert stats["citation_count_median"] == 0.0
        assert stats["citation_count_max"] == 0
        assert stats["citation_count_total"] == 0
        assert stats["pct_open_access"] == 0.0
        assert stats["pct_with_abstract"] == 0.0
        assert stats["pct_with_doi"] == 0.0

    def test_all_open_access_none_yields_zero_pct(self):
        """When no paper has an OA flag set, pct_open_access is 0.0."""
        papers = [
            Paper(title="X", citation_count=1, is_open_access=None),
            Paper(title="Y", citation_count=2, is_open_access=None),
        ]
        stats = descriptive_stats(papers)
        assert stats["pct_open_access"] == 0.0

    def test_duplicate_author_within_paper_counted_once(self):
        """An author repeated within one paper contributes a single count."""
        dup = Author(name="Solo")
        papers = [Paper(title="Z", authors=[dup, dup])]
        stats = descriptive_stats(papers)
        assert stats["unique_authors"] == 1
        assert stats["papers_per_author_mean"] == 1.0


# ── citation_distribution ────────────────────────────────────────────────


class TestCitationDistribution:
    """Tests for citation_distribution histogram and Gini coefficient."""

    def test_default_histogram_buckets(self):
        """Each default bucket count matches hand placement of the values."""
        dist = citation_distribution(_corpus())
        # 0->"0", 5->"1-9", 12->"10-49", 80->"50-99", 600->"500+".
        assert dist["histogram"] == {
            "0": 1,
            "1-9": 1,
            "10-49": 1,
            "50-99": 1,
            "100-499": 0,
            "500+": 1,
        }
        assert dist["n"] == 5
        assert dist["total_citations"] == 697

    def test_gini_matches_independent_reference(self):
        """Gini equals an independently brute-forced pairwise computation."""
        values = [0, 5, 12, 80, 600]
        dist = citation_distribution(_corpus())
        reference = _brute_force_gini(values)
        # Sanity-check the reference itself is a non-trivial inequality value.
        assert 0.0 < reference < 1.0
        assert dist["gini"] == pytest.approx(reference, abs=1e-9)

    def test_gini_all_equal_is_zero(self):
        """A perfectly equal corpus has zero Gini inequality."""
        papers = [Paper(title=f"E{i}", citation_count=7) for i in range(4)]
        dist = citation_distribution(papers)
        assert dist["gini"] == 0.0

    def test_gini_all_zero_is_zero(self):
        """An all-zero corpus (mean 0) has zero Gini, guarded division."""
        papers = [Paper(title=f"Z{i}", citation_count=0) for i in range(3)]
        dist = citation_distribution(papers)
        assert dist["gini"] == 0.0

    def test_empty_distribution(self):
        """Empty corpus yields zero Gini, zero counts, empty histogram."""
        dist = citation_distribution([])
        assert dist["gini"] == 0.0
        assert dist["n"] == 0
        assert dist["total_citations"] == 0
        assert all(count == 0 for count in dist["histogram"].values())

    def test_custom_buckets(self):
        """Custom monotonic bucket edges relabel and re-place values."""
        papers = [
            Paper(title="a", citation_count=0),
            Paper(title="b", citation_count=3),
            Paper(title="c", citation_count=15),
        ]
        dist = citation_distribution(papers, buckets=[0, 10])
        # Edges [0, 10] -> labels "0-9", "10+".
        assert dist["histogram"] == {"0-9": 2, "10+": 1}

    def test_buckets_must_be_increasing(self):
        """Non-increasing bucket edges raise ValueError."""
        with pytest.raises(ValueError):
            citation_distribution(_corpus(), buckets=[0, 0, 5])

    def test_buckets_must_be_nonempty(self):
        """An empty bucket edge list raises ValueError."""
        with pytest.raises(ValueError):
            citation_distribution(_corpus(), buckets=[])

    def test_single_edge_buckets(self):
        """A single-edge bucket list produces one catch-all '+' bucket."""
        papers = [Paper(title="s", citation_count=42)]
        dist = citation_distribution(papers, buckets=[0])
        assert dist["histogram"] == {"0+": 1}


# ── author_productivity ──────────────────────────────────────────────────


class TestAuthorProductivity:
    """Tests for author_productivity ranking and truncation."""

    def test_ranking_order(self):
        """Authors rank by count desc, then name ascending."""
        ranking = author_productivity(_corpus())
        assert ranking == [("Friston", 4), ("Parr", 3), ("Da Costa", 2)]

    def test_top_k_truncation(self):
        """top_k truncates to the highest-ranked authors."""
        ranking = author_productivity(_corpus(), top_k=2)
        assert ranking == [("Friston", 4), ("Parr", 3)]

    def test_name_tiebreak_ascending(self):
        """Equal counts break ties by name ascending."""
        papers = [
            Paper(title="t1", authors=[Author(name="Zed")]),
            Paper(title="t2", authors=[Author(name="Amy")]),
        ]
        ranking = author_productivity(papers)
        assert ranking == [("Amy", 1), ("Zed", 1)]

    def test_empty(self):
        """No papers yields an empty ranking."""
        assert author_productivity([]) == []

    def test_duplicate_author_within_paper_counted_once(self):
        """An author listed twice on one paper is counted once."""
        dup = Author(name="Solo")
        papers = [Paper(title="dup", authors=[dup, dup])]
        assert author_productivity(papers) == [("Solo", 1)]

    def test_top_k_zero_returns_empty(self):
        """top_k=0 truncates to an empty ranking."""
        assert author_productivity(_corpus(), top_k=0) == []


# ── build_meta_report ────────────────────────────────────────────────────


class TestBuildMetaReport:
    """Tests for the consolidated meta-report artifact."""

    def test_nests_all_sections(self):
        """Report nests provenance + all three analysis sections."""
        report = build_meta_report(_corpus())
        assert set(report.keys()) >= {
            "generated",
            "descriptive_stats",
            "citation_distribution",
            "author_productivity",
        }
        assert report["generated"]["total_papers"] == 5
        assert report["generated"]["schema_version"] == "1.0"
        assert report["generated"]["generator"] == "descriptive_stats.build_meta_report"
        # Nested sections equal the standalone function outputs.
        assert report["descriptive_stats"]["total"] == 5
        assert report["citation_distribution"]["total_citations"] == 697
        # author_productivity stored JSON-friendly as 2-element lists.
        assert report["author_productivity"] == [
            ["Friston", 4],
            ["Parr", 3],
            ["Da Costa", 2],
        ]

    def test_extras_merged_without_mutation(self):
        """Extras add top-level keys and the caller's dict is not mutated."""
        extras = {"topic_summary": {"k": 3}, "entity_summary": [1, 2]}
        snapshot = json.loads(json.dumps(extras))
        report = build_meta_report(_corpus(), extras=extras)
        assert report["topic_summary"] == {"k": 3}
        assert report["entity_summary"] == [1, 2]
        # Core sections still present alongside extras.
        assert "descriptive_stats" in report
        # Caller's extras dict is untouched.
        assert extras == snapshot

    def test_extras_can_override_generated_block(self):
        """An explicit 'generated' key in extras overrides the default block."""
        report = build_meta_report(_corpus(), extras={"generated": "custom"})
        assert report["generated"] == "custom"

    def test_extras_none_is_noop(self):
        """extras=None leaves only the core report keys."""
        report = build_meta_report(_corpus(), extras=None)
        assert set(report.keys()) == {
            "generated",
            "descriptive_stats",
            "citation_distribution",
            "author_productivity",
        }


# ── save_meta_report ─────────────────────────────────────────────────────


class TestSaveMetaReport:
    """Tests for JSON persistence and round-trip fidelity."""

    def test_round_trip(self, tmp_path):
        """Saved JSON reloads to an equal structure and returns the path."""
        report = build_meta_report(_corpus(), extras={"topic_summary": {"n": 1}})
        path = tmp_path / "nested" / "meta_report.json"
        returned = save_meta_report(report, path)
        assert returned == path
        assert path.exists()
        loaded = json.loads(path.read_text(encoding="utf-8"))
        # JSON object keys are always strings, so integer year keys round-trip
        # to their string form; compare both sides through one JSON pass so the
        # assertion checks serialization fidelity, not Python key identity.
        assert loaded == json.loads(json.dumps(report))
        # Spot-check a representative nested value survives the round-trip.
        assert loaded["descriptive_stats"]["citation_count_total"] == 697
        assert loaded["author_productivity"] == [
            ["Friston", 4],
            ["Parr", 3],
            ["Da Costa", 2],
        ]

    def test_creates_parent_dirs(self, tmp_path):
        """Missing parent directories are created on save."""
        report = build_meta_report([])
        path = tmp_path / "a" / "b" / "c" / "report.json"
        save_meta_report(report, path)
        assert path.exists()
