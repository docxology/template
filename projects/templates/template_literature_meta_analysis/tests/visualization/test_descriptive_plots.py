"""Tests for descriptive statistics visualizations."""

from __future__ import annotations

from pathlib import Path

from visualization.descriptive_plots import (
    plot_author_productivity,
    plot_citation_distribution,
    plot_entity_bar_chart,
    plot_similarity_heatmap,
    plot_top_venues,
)


def test_plot_citation_distribution_with_data(tmp_path: Path) -> None:
    """Citation distribution chart renders with histogram and Gini annotation."""
    data = {
        "histogram": {"0": 500, "1-9": 300, "10-49": 150, "50-99": 30, "100-499": 15, "500+": 5},
        "gini": 0.812,
        "n": 1000,
        "total_citations": 45000,
    }
    out = tmp_path / "citation_distribution.png"
    result = plot_citation_distribution(data, out)
    assert result == out
    assert out.exists()
    assert out.stat().st_size > 0


def test_plot_citation_distribution_empty(tmp_path: Path) -> None:
    """Empty citation data produces a blank figure, not a crash."""
    out = tmp_path / "empty.png"
    result = plot_citation_distribution({}, out)
    assert result == out
    assert out.exists()


def test_plot_top_venues_with_data(tmp_path: Path) -> None:
    """Top venues chart renders with venue names and counts."""
    stats = {
        "counts_by_venue": {
            "Sleep": 120,
            "J Clin Psychopharmacol": 80,
            "Neuroscience": 60,
            "Nature": 40,
            "JAMA": 30,
        }
    }
    out = tmp_path / "top_venues.png"
    result = plot_top_venues(stats, out)
    assert result == out
    assert out.exists()
    assert out.stat().st_size > 0


def test_plot_top_venues_empty(tmp_path: Path) -> None:
    """Empty venue data produces a blank figure."""
    out = tmp_path / "empty.png"
    result = plot_top_venues({}, out)
    assert result == out
    assert out.exists()


def test_plot_author_productivity_with_data(tmp_path: Path) -> None:
    """Author productivity chart renders with names and counts."""
    authors = [
        ["Smith J", 15],
        ["Doe A", 12],
        ["Garcia M", 10],
        ["Lee K", 8],
        ["Brown R", 7],
    ]
    out = tmp_path / "author_productivity.png"
    result = plot_author_productivity(authors, out)
    assert result == out
    assert out.exists()
    assert out.stat().st_size > 0


def test_plot_author_productivity_empty(tmp_path: Path) -> None:
    """Empty author data produces a blank figure."""
    out = tmp_path / "empty.png"
    result = plot_author_productivity([], out)
    assert result == out
    assert out.exists()


def test_plot_top_venues_truncates_long_names(tmp_path: Path) -> None:
    """Long venue names are truncated without crashing."""
    stats = {
        "counts_by_venue": {
            "A Very Long Venue Name That Should Be Truncated": 50,
            "Short": 30,
        }
    }
    out = tmp_path / "trunc.png"
    result = plot_top_venues(stats, out, top_n=2)
    assert result == out
    assert out.exists()


def test_plot_similarity_heatmap_with_data(tmp_path: Path) -> None:
    """Similarity heatmap renders with document pairs."""
    pairs = [
        {"paper_a": "doi:10.1/a", "paper_b": "doi:10.1/b", "similarity": 0.95},
        {"paper_a": "doi:10.1/c", "paper_b": "doi:10.1/d", "similarity": 0.87},
        {"paper_a": "doi:10.1/e", "paper_b": "doi:10.1/f", "similarity": 0.72},
    ]
    out = tmp_path / "similarity.png"
    result = plot_similarity_heatmap(pairs, out)
    assert result == out
    assert out.exists()
    assert out.stat().st_size > 0


def test_plot_similarity_heatmap_empty(tmp_path: Path) -> None:
    """Empty similarity data produces a blank figure."""
    out = tmp_path / "empty.png"
    result = plot_similarity_heatmap([], out)
    assert result == out
    assert out.exists()


def test_plot_entity_bar_chart_with_data(tmp_path: Path) -> None:
    """Entity bar chart renders with entity names and counts."""
    entities = {"modafinil": 500, "narcolepsy": 300, "placebo": 250, "dopamine": 180}
    out = tmp_path / "entities.png"
    result = plot_entity_bar_chart(entities, out)
    assert result == out
    assert out.exists()
    assert out.stat().st_size > 0


def test_plot_entity_bar_chart_empty(tmp_path: Path) -> None:
    """Empty entity data produces a blank figure."""
    out = tmp_path / "empty.png"
    result = plot_entity_bar_chart({}, out)
    assert result == out
    assert out.exists()
