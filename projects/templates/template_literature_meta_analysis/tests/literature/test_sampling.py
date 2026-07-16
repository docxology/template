"""Tests for literature.sampling module."""

from __future__ import annotations

import pytest

from literature.models import Paper
from literature.sampling import load_sampling_config, sample_papers


def test_load_sampling_config_defaults() -> None:
    """Test loading sampling config with defaults."""
    config: dict[str, object] = {}
    fraction, seed = load_sampling_config(config)
    assert fraction == 1.0  # No subsampling by default
    assert seed == 42


def test_load_sampling_config_custom() -> None:
    """Test loading sampling config with custom values."""
    config = {
        "sampling": {
            "fraction": 0.1,
            "seed": 123,
        }
    }
    fraction, seed = load_sampling_config(config)
    assert fraction == 0.1
    assert seed == 123


@pytest.mark.parametrize(
    "sampling, message",
    [
        ({"fraction": 0}, "greater than 0"),
        ({"fraction": -0.1}, "greater than 0"),
        ({"fraction": 1.5}, "at most 1"),
        ({"fraction": True}, "numeric"),
        ({"fraction": "0.5"}, "numeric"),
        ({"seed": -1}, "non-negative integer"),
        ({"seed": True}, "non-negative integer"),
    ],
)
def test_load_sampling_config_rejects_invalid_values(sampling: dict[str, object], message: str) -> None:
    """Invalid sampling config fails closed instead of being silently clamped."""
    with pytest.raises(ValueError, match=message):
        load_sampling_config({"sampling": sampling})


def test_sample_papers_empty() -> None:
    """Test sampling from an empty list."""
    papers: list[Paper] = []
    result = sample_papers(papers, fraction=0.5, seed=42)
    assert result == []


def test_sample_papers_full() -> None:
    """Test no sampling when fraction >= 1.0."""
    papers = [
        Paper(title="A", doi="10.1000/a"),
        Paper(title="B", doi="10.1000/b"),
    ]
    result = sample_papers(papers, fraction=1.0, seed=42)
    assert len(result) == 2
    assert result == papers

    # > 1.0 also returns all
    result = sample_papers(papers, fraction=1.5, seed=42)
    assert len(result) == 2


def test_sample_papers_deterministic() -> None:
    """Test that sampling is deterministic with same seed."""
    papers = [Paper(title=f"Paper {i}", doi=f"10.1000/{i}") for i in range(100)]

    result1 = sample_papers(papers, fraction=0.1, seed=42)
    result2 = sample_papers(papers, fraction=0.1, seed=42)

    # Same seed produces same result
    assert result1 == result2
    assert len(result1) == 10  # 10% of 100


def test_sample_papers_different_seeds() -> None:
    """Test that different seeds produce different results."""
    papers = [Paper(title=f"Paper {i}", doi=f"10.1000/{i}") for i in range(100)]

    result1 = sample_papers(papers, fraction=0.1, seed=42)
    result2 = sample_papers(papers, fraction=0.1, seed=123)

    # Different seeds should produce different selections
    assert len(result1) == len(result2) == 10
    # With 90% probability this will fail if sampling is random
    assert result1 != result2


def test_sample_papers_stable_order() -> None:
    """Test that sampling is stable regardless of input order."""
    papers = [
        Paper(title="C", doi="10.1000/c"),
        Paper(title="A", doi="10.1000/a"),
        Paper(title="B", doi="10.1000/b"),
    ]

    # Same papers, different input order
    papers_shuffled = [papers[1], papers[2], papers[0]]  # a, b, c

    result1 = sample_papers(papers, fraction=0.67, seed=42)  # Should get 2 papers
    result2 = sample_papers(papers_shuffled, fraction=0.67, seed=42)

    # Results should be identical (sorted by canonical_id internally)
    assert result1 == result2


def test_sample_papers_uses_exact_ceiling_target() -> None:
    """The selected count is exactly ceil(n * fraction)."""
    papers = [Paper(title=f"Paper {i}", doi=f"10.1000/{i}") for i in range(10)]

    result = sample_papers(papers, fraction=0.15, seed=42)
    assert len(result) == 2

    result = sample_papers(papers[:5], fraction=0.5, seed=42)
    assert len(result) == 3

    result = sample_papers(papers, fraction=0.01, seed=42)
    assert len(result) == 1


def test_sample_papers_has_stable_per_paper_ranking_when_corpus_grows() -> None:
    """Adding a paper does not reshuffle the relative rank of existing papers."""
    papers = [Paper(title=f"Paper {i}", doi=f"10.1000/{i}") for i in range(100)]
    before = sample_papers(papers, fraction=0.1, seed=42)
    after = sample_papers(
        [*papers, Paper(title="New Paper", doi="10.1000/new")],
        fraction=0.1,
        seed=42,
    )

    before_ids = [paper.canonical_id for paper in before]
    before_id_set = set(before_ids)
    common_after_ids = [paper.canonical_id for paper in after if paper.canonical_id in before_id_set]
    assert common_after_ids == [paper_id for paper_id in before_ids if paper_id in common_after_ids]
    assert len(common_after_ids) >= len(before) - 1
