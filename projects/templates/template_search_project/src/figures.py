"""Figure generators for the search project.

Pure-Python plotting helpers — they take a :class:`SearchResult` (or a
JSON file containing one) and write PNG figures to a target directory.
The figures are intentionally simple and accessibility-aware: a
colour-blind-safe palette, descriptive titles, and 300 dpi exports.

Like the rest of ``src/``, no script logic lives here. The
``scripts/generate_search_figures.py`` orchestrator imports these
functions and prints the resulting paths.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

import matplotlib

matplotlib.use("Agg")  # noqa: E402 — must precede pyplot import for headless CI
import matplotlib.pyplot as plt

from infrastructure.search.literature import Paper, SearchResult, SearchQuery

# Colour-blind-safe categorical palette (Wong, 2011).
_PALETTE = [
    "#0072B2",
    "#E69F00",
    "#009E73",
    "#CC79A7",
    "#56B4E9",
    "#D55E00",
    "#F0E442",
    "#999999",
]


def _ensure_outdir(path: Path | str) -> Path:
    out = Path(path)
    out.mkdir(parents=True, exist_ok=True)
    return out


def plot_papers_per_source(result: SearchResult, output_dir: Path | str) -> Path:
    """Bar chart of paper count per backend.

    Uses ``result.per_source_counts`` directly (the value the aggregator
    recorded *before* deduplication, which is the accurate per-backend
    contribution).
    """
    out_dir = _ensure_outdir(output_dir)
    counts: Mapping[str, int] = result.per_source_counts or {}

    fig, ax = plt.subplots(figsize=(6, 3.5), dpi=300)
    if counts:
        names = list(counts.keys())
        values = [counts[n] for n in names]
        bars = ax.bar(names, values, color=_PALETTE[: len(names)])
        for bar, value in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                str(value),
                ha="center",
                va="bottom",
                fontsize=9,
            )
    else:
        ax.text(0.5, 0.5, "(no results)", ha="center", va="center", transform=ax.transAxes)

    ax.set_title("Papers per source")
    ax.set_xlabel("Backend")
    ax.set_ylabel("Papers contributed")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()

    out_path = out_dir / "papers_per_source.png"
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


def plot_year_histogram(result: SearchResult, output_dir: Path | str) -> Path:
    """Histogram of publication years for the deduplicated paper list."""
    out_dir = _ensure_outdir(output_dir)
    years = [p.year for p in result.papers if p.year is not None]

    fig, ax = plt.subplots(figsize=(6, 3.5), dpi=300)
    if years:
        lo = min(years)
        hi = max(years)
        # Use one bin per year so the histogram is faithful for small N.
        bins = list(range(lo, hi + 2))
        ax.hist(years, bins=bins, color=_PALETTE[0], edgecolor="white")
    else:
        ax.text(0.5, 0.5, "(no years)", ha="center", va="center", transform=ax.transAxes)

    ax.set_title("Publication year distribution")
    ax.set_xlabel("Year")
    ax.set_ylabel("Papers")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()

    out_path = out_dir / "year_histogram.png"
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


def plot_score_distribution(result: SearchResult, output_dir: Path | str) -> Path:
    """Per-paper relevance score (kde-free; just dots ranked by score)."""
    out_dir = _ensure_outdir(output_dir)
    scored = sorted(
        ((p.title or p.id, p.score) for p in result.papers),
        key=lambda item: item[1],
        reverse=True,
    )

    fig, ax = plt.subplots(figsize=(6, max(2.5, 0.3 * len(scored) + 1)), dpi=300)
    if scored:
        labels = [t[:60] + ("…" if len(t) > 60 else "") for t, _ in scored]
        scores = [s for _, s in scored]
        ax.barh(range(len(scores)), scores, color=_PALETTE[2])
        ax.set_yticks(range(len(scores)))
        ax.set_yticklabels(labels, fontsize=8)
        ax.invert_yaxis()
    else:
        ax.text(0.5, 0.5, "(no papers)", ha="center", va="center", transform=ax.transAxes)

    ax.set_title("Relevance score by paper")
    ax.set_xlabel("Score (backend-reported)")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()

    out_path = out_dir / "score_distribution.png"
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


def generate_all_figures(result: SearchResult, output_dir: Path | str) -> list[Path]:
    """Run every figure generator. Order is stable across runs."""
    return [
        plot_papers_per_source(result, output_dir),
        plot_year_histogram(result, output_dir),
        plot_score_distribution(result, output_dir),
    ]


def load_search_result(path: Path | str) -> SearchResult:
    """Reconstruct a :class:`SearchResult` from a JSON file."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    query_data = payload.get("query") or {}
    query = SearchQuery(
        text=query_data.get("text", ""),
        max_results=int(query_data.get("max_results", 10)),
        year_min=query_data.get("year_min"),
        year_max=query_data.get("year_max"),
        sources=list(query_data.get("sources") or []),
        fields=list(query_data.get("fields") or []),
    )
    papers = [Paper.from_dict(p) for p in payload.get("papers") or []]
    return SearchResult(
        query=query,
        papers=papers,
        per_source_counts=dict(payload.get("per_source_counts") or {}),
        errors=dict(payload.get("errors") or {}),
    )
