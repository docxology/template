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
    "#0072B2", "#E69F00", "#009E73", "#CC79A7",
    "#56B4E9", "#D55E00", "#F0E442", "#999999",
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


def generate_all_figures(
    report: ManuscriptReport, output_dir: Path | str
) -> list[Path]:
    """Render every figure in stable order."""
    return [
        plot_section_word_counts(report, output_dir),
        plot_readability_radar(report, output_dir),
        plot_citation_density(report, output_dir),
    ]


def load_manuscript_report(path: Path | str) -> ManuscriptReport:
    """Reconstruct a :class:`ManuscriptReport` from on-disk JSON."""
    import json
    from infrastructure.prose.report import (
        FileReport,
        ManuscriptReport as _MR,
    )
    from infrastructure.prose.analysis import (
        Heading,
        ProseMetrics,
        QualityReport,
        Section,
        StructureReport,
    )

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    files: list[FileReport] = []
    for f in payload.get("files") or []:
        m = ProseMetrics(**f["metrics"])
        s_data = f["structure"]
        headings = [Heading(**h) for h in s_data.get("headings") or []]
        sections: list[Section] = []
        for sec, hd in zip(s_data.get("sections") or [], headings):
            sections.append(
                Section(heading=hd, body="", word_count=int(sec.get("word_count", 0)))
            )
        struct = StructureReport(
            headings=headings,
            sections=sections,
            total_words=int(s_data.get("total_words", 0)),
            max_depth=int(s_data.get("max_depth", 0)),
            has_h1=bool(s_data.get("has_h1", False)),
            has_skipped_level=bool(s_data.get("has_skipped_level", False)),
        )
        q_data = f["quality"]
        # QualityReport accepts everything as kwargs.
        q = QualityReport(
            passive_count=q_data.get("passive_count", 0),
            passive_sentences=list(q_data.get("passive_sentences") or []),
            hedge_count=q_data.get("hedge_count", 0),
            hedge_words=list(q_data.get("hedge_words") or []),
            citation_count=q_data.get("citation_count", 0),
            citation_keys=list(q_data.get("citation_keys") or []),
            long_sentence_count=q_data.get("long_sentence_count", 0),
            long_sentences=list(q_data.get("long_sentences") or []),
            word_count=q_data.get("word_count", 0),
            citation_density_per_1000=q_data.get("citation_density_per_1000", 0.0),
            hedge_density_per_1000=q_data.get("hedge_density_per_1000", 0.0),
            passive_density_per_1000=q_data.get("passive_density_per_1000", 0.0),
        )
        files.append(FileReport(name=f["name"], metrics=m, structure=struct, quality=q))

    return _MR(
        files=files,
        total_words=int(payload.get("total_words", 0)),
        total_sentences=int(payload.get("total_sentences", 0)),
        total_paragraphs=int(payload.get("total_paragraphs", 0)),
        avg_flesch_reading_ease=float(payload.get("avg_flesch_reading_ease", 0.0)),
        avg_flesch_kincaid_grade=float(payload.get("avg_flesch_kincaid_grade", 0.0)),
        avg_gunning_fog=float(payload.get("avg_gunning_fog", 0.0)),
        citation_keys=list(payload.get("citation_keys") or []),
    )
