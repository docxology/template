#!/usr/bin/env python3
"""Generate handbook figures: section coverage, evidence by theme, gap status."""

from __future__ import annotations

import os
import sys
from pathlib import Path

project_root = Path(os.environ.get("PROJECT_DIR", Path(__file__).resolve().parent.parent))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

repo_root = project_root.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

import matplotlib.pyplot as plt

from infrastructure.core.logging_utils import get_logger
from infrastructure.documentation.figure_manager import FigureManager

from src.corpus_io import load_corpus
from src.corpus_stats import evidence_counts_by_theme
from src.handbook_plot_data import section_scores_with_gap_flags
from src.metrics import build_metrics_report
from src.synthesis import synthesize

logger = get_logger(__name__)
fixture_path = project_root / "data" / "fixtures" / "riverbend_area.yaml"

_CAPTION_COVERAGE = (
    "Riverbend fixture (version 2026.1): horizontal coverage score per handbook section "
    "(capped sum of matching evidence weights, range 0–1). Red dashed vertical line: "
    "current gap threshold from synthesis; sections strictly to the left would be listed "
    "in the JSON ``gaps`` array."
)
_CAPTION_BY_THEME = (
    "Riverbend fixture: count of evidence rows per theme id after corpus validation "
    "(duplicate ids and invalid weights rejected at load). Bar height shows how many "
    "statements contribute to each thematic bucket used for section routing."
)
_CAPTION_GAP_STATUS = (
    "Same scores as the coverage chart, sorted by section id, with bars colored by gap "
    "status: coral = section id in ``gap_section_ids`` (score strictly below threshold); "
    "steel blue = at or above threshold. For this fixture under the default threshold, "
    "all sections are above the line (empty gap list), illustrating a fully covered outline."
)


def _register_figures(project_root: Path) -> None:
    registry_path = project_root / "output" / "figures" / "figure_registry.json"
    fm = FigureManager(registry_file=str(registry_path))
    entries = [
        (
            "handbook_evidence_coverage.png",
            _CAPTION_COVERAGE,
            "fig:coverage",
            "Methods: synthesis",
        ),
        (
            "handbook_evidence_by_theme.png",
            _CAPTION_BY_THEME,
            "fig:bytheme",
            "Methods: synthesis",
        ),
        (
            "handbook_section_gap_status.png",
            _CAPTION_GAP_STATUS,
            "fig:gapstatus",
            "Methods: synthesis",
        ),
    ]
    for filename, caption, label, section in entries:
        fm.register_figure(
            filename=filename,
            caption=caption,
            label=label,
            section=section,
            generated_by="02_generate_handbook_figure.py",
        )
        logger.info("Registered figure %s", label)


def main() -> None:
    out_dir = project_root / "output" / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    coverage_path = out_dir / "handbook_evidence_coverage.png"
    by_theme_path = out_dir / "handbook_evidence_by_theme.png"
    gap_path = out_dir / "handbook_section_gap_status.png"

    corpus = load_corpus(fixture_path)
    synth = synthesize(corpus)
    metrics = build_metrics_report(synth)
    scores = metrics["scores_by_section"]
    thr = metrics["gap_threshold"]
    labels = list(scores.keys())
    values = [scores[k] for k in labels]
    short_labels = [k.replace("_", " ") for k in labels]

    fig, ax = plt.subplots(figsize=(8, 5), layout="constrained")
    y_pos = range(len(labels))
    ax.barh(list(y_pos), values, color="#2c5f7c", height=0.65)
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(short_labels, fontsize=9)
    ax.set_xlabel("Coverage score (capped sum of evidence weights)")
    ax.set_xlim(0, 1.05)
    ax.set_title("Handbook section coverage: Riverbend fixture corpus")
    ax.axvline(x=thr, color="#c44e52", linestyle="--", linewidth=1, label="Gap threshold")
    ax.legend(loc="lower right", fontsize=8)
    fig.savefig(coverage_path, dpi=200)
    plt.close(fig)

    counts = evidence_counts_by_theme(corpus)
    theme_ids = sorted(counts.keys())
    counts_list = [counts[k] for k in theme_ids]
    labels_t = [k.replace("_", " ") for k in theme_ids]

    fig2, ax2 = plt.subplots(figsize=(7, 4.5), layout="constrained")
    ax2.bar(range(len(theme_ids)), counts_list, color="#3d7a4a", width=0.72)
    ax2.set_xticks(range(len(theme_ids)))
    ax2.set_xticklabels(labels_t, rotation=35, ha="right", fontsize=8)
    ax2.set_ylabel("Evidence rows")
    ax2.set_title("Evidence volume by theme: Riverbend fixture")
    fig2.savefig(by_theme_path, dpi=200)
    plt.close(fig2)

    sec_labels, sec_scores, gap_flags, thr_g = section_scores_with_gap_flags(metrics)
    short_sec = [s.replace("_", " ") for s in sec_labels]
    colors = ["#dd8452" if g else "#2c5f7c" for g in gap_flags]
    fig3, ax3 = plt.subplots(figsize=(8, 5), layout="constrained")
    y3 = range(len(sec_labels))
    ax3.barh(list(y3), sec_scores, color=colors, height=0.65)
    ax3.set_yticks(list(y3))
    ax3.set_yticklabels(short_sec, fontsize=9)
    ax3.set_xlabel("Coverage score (capped sum of evidence weights)")
    ax3.set_xlim(0, 1.05)
    ax3.set_title("Section scores vs gap threshold (Riverbend fixture)")
    ax3.axvline(x=thr_g, color="#c44e52", linestyle="--", linewidth=1, label="Gap threshold")
    ax3.legend(loc="lower right", fontsize=8)
    fig3.savefig(gap_path, dpi=200)
    plt.close(fig3)

    _register_figures(project_root)

    logger.info("Wrote %s", coverage_path)
    logger.info("Wrote %s", by_theme_path)
    logger.info("Wrote %s", gap_path)
    print(str(coverage_path))
    print(str(by_theme_path))
    print(str(gap_path))


if __name__ == "__main__":
    main()
