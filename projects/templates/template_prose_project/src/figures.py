"""Matplotlib figures for the prose-review project.

All plotting is colour-blind-safe (Wong 2011 palette), 300 dpi, PNG
output. Figures are pure functions over a :class:`ManuscriptReport`.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # noqa: E402
import matplotlib.pyplot as plt
import numpy as np

from infrastructure.prose import ManuscriptReport

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


def plot_section_word_counts(report: ManuscriptReport, output_dir: Path | str) -> Path:
    """Bar chart of word counts per file."""
    out_dir = _ensure_outdir(output_dir)
    names = [f.name for f in report.files]
    counts = [f.metrics.word_count for f in report.files]

    fig, ax = plt.subplots(figsize=(8, max(2.5, 0.4 * len(names) + 1)), dpi=300)
    if names:
        ax.barh(range(len(names)), counts, color=_PALETTE[0])
        ax.set_yticks(range(len(names)))
        ax.set_yticklabels(names, fontsize=9)
        ax.invert_yaxis()
        for i, c in enumerate(counts):
            ax.text(c, i, f" {c}", va="center", fontsize=8)
    else:
        ax.text(0.5, 0.5, "(no files)", ha="center", va="center", transform=ax.transAxes)
    ax.set_title("Words per manuscript file")
    ax.set_xlabel("Word count")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()

    out_path = out_dir / "section_word_counts.png"
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


def plot_readability_radar(report: ManuscriptReport, output_dir: Path | str) -> Path:
    """Bar chart comparing the three readability scores per file.

    A radar chart sounds appealing here, but with mixed value ranges
    (FRE ∈ [0, 100], FKGL ∈ [0, 25], Fog ∈ [0, 25]) a normalised bar
    chart is clearer.
    """
    out_dir = _ensure_outdir(output_dir)
    names = [f.name for f in report.files]
    fre = np.array([f.metrics.flesch_reading_ease for f in report.files], dtype=float)
    fkgl = np.array([f.metrics.flesch_kincaid_grade for f in report.files], dtype=float)
    fog = np.array([f.metrics.gunning_fog for f in report.files], dtype=float)

    fig, ax = plt.subplots(figsize=(8, max(3.0, 0.4 * len(names) + 1)), dpi=300)
    if names:
        x = np.arange(len(names))
        width = 0.27
        ax.bar(x - width, fre / 100.0 * 25.0, width, color=_PALETTE[0], label="FRE / 100 × 25")
        ax.bar(x, fkgl, width, color=_PALETTE[1], label="FKGL")
        ax.bar(x + width, fog, width, color=_PALETTE[2], label="Gunning Fog")
        ax.set_xticks(x)
        ax.set_xticklabels(names, rotation=30, ha="right", fontsize=8)
        ax.legend(fontsize=8, loc="upper left")
    else:
        ax.text(0.5, 0.5, "(no files)", ha="center", va="center", transform=ax.transAxes)
    ax.set_title("Readability metrics per file")
    ax.set_ylabel("Score (FRE rescaled)")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()

    out_path = out_dir / "readability_metrics.png"
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


def plot_citation_density(report: ManuscriptReport, output_dir: Path | str) -> Path:
    """Bar chart of citation density per file (citations per 1000 words)."""
    out_dir = _ensure_outdir(output_dir)
    names = [f.name for f in report.files]
    densities = [f.quality.citation_density_per_1000 for f in report.files]

    fig, ax = plt.subplots(figsize=(8, max(2.5, 0.4 * len(names) + 1)), dpi=300)
    if names:
        ax.barh(range(len(names)), densities, color=_PALETTE[3])
        ax.set_yticks(range(len(names)))
        ax.set_yticklabels(names, fontsize=9)
        ax.invert_yaxis()
        for i, d in enumerate(densities):
            ax.text(d, i, f" {d}", va="center", fontsize=8)
    else:
        ax.text(0.5, 0.5, "(no files)", ha="center", va="center", transform=ax.transAxes)
    ax.set_title("Citation density per file")
    ax.set_xlabel("Citations per 1000 words")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()

    out_path = out_dir / "citation_density.png"
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


def generate_all_figures(report: ManuscriptReport, output_dir: Path | str) -> list[Path]:
    """Render every figure in stable order."""
    return [
        plot_section_word_counts(report, output_dir),
        plot_readability_radar(report, output_dir),
        plot_citation_density(report, output_dir),
    ]
