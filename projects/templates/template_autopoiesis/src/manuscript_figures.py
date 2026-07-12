"""Manuscript figure writers for the autopoiesis exemplar."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .grammar import KNOWN_DOMAINS, load_grammar


@dataclass(frozen=True)
class ManuscriptFigureSpec:
    """Registry metadata owned by a manuscript figure writer."""

    label: str
    filename: str
    caption: str
    generated_by: str


FIGURE_REGISTRY_SCHEMA = "template-autopoiesis-figure-registry-v1"
MANUSCRIPT_FIGURE_SPECS: tuple[ManuscriptFigureSpec, ...] = (
    ManuscriptFigureSpec(
        label="fig:stacked_product",
        filename="fig_stacked_product.png",
        caption="Options per effective grammar slot, shown as a stacked bar.",
        generated_by="src.manuscript_figures.fig_stacked_product",
    ),
    ManuscriptFigureSpec(
        label="fig:product_space",
        filename="fig_product_space.png",
        caption="Total, effective, and reserved-only grammar product sizes.",
        generated_by="src.manuscript_figures.fig_product_space_annotation",
    ),
    ManuscriptFigureSpec(
        label="fig:domain_coverage",
        filename="fig_domain_coverage.png",
        caption="The five primitive domains, shown with distinct type colors.",
        generated_by="src.manuscript_figures.fig_domain_coverage",
    ),
    ManuscriptFigureSpec(
        label="fig:coverage_by_module",
        filename="fig_coverage_by_module.png",
        caption="Measured branch coverage by source module with the 90 percent floor marked.",
        generated_by="src.manuscript_figures.fig_coverage_by_module",
    ),
)
_SPEC_BY_LABEL = {spec.label: spec for spec in MANUSCRIPT_FIGURE_SPECS}


def _teal_slate_palette(n: int) -> list[str]:
    """Return n teal/slate brand colors."""
    base = [
        "#0d9488",
        "#1e293b",
        "#0f766e",
        "#334155",
        "#14b8a6",
        "#475569",
        "#0f172a",
        "#94a3b8",
    ]
    return [base[i % len(base)] for i in range(n)]


def fig_stacked_product(project_root: Path, out_dir: Path) -> Path:
    """Stacked bar: product size per slot."""
    grammar = load_grammar(project_root)
    slots = grammar.effective_slots
    sizes = [len(s.options) for s in slots]
    names = [s.name for s in slots]
    colors = _teal_slate_palette(len(names))

    fig, ax = plt.subplots(figsize=(8, 4))
    bottom = 0
    for i, (name, size) in enumerate(zip(names, sizes)):
        ax.bar(0, size, bottom=bottom, color=colors[i], label=name, width=0.5)
        ax.text(
            0.32,
            bottom + size / 2,
            f"{name}\n({size})",
            va="center",
            ha="left",
            fontsize=9,
            color=colors[i],
        )
        bottom += size

    ax.set_xticks([])
    ax.set_ylabel("Options per slot")
    ax.set_title("Effective grammar slots (stacked)")
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    out = out_dir / _SPEC_BY_LABEL["fig:stacked_product"].filename
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"  ✓ {out.name}")
    return out


def fig_domain_coverage(out_dir: Path) -> Path:
    """Type-colored domain coverage bar chart."""
    domains = list(KNOWN_DOMAINS)
    colors = {
        "optimization": "#0d9488",
        "dynamics": "#1d4ed8",
        "statistics": "#7c3aed",
        "signal": "#db2777",
        "graph": "#d97706",
    }
    heights = [1] * len(domains)
    bar_colors = [colors[d] for d in domains]

    fig, ax = plt.subplots(figsize=(8, 3))
    bars = ax.bar(domains, heights, color=bar_colors)
    for bar, d in zip(bars, domains):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.02,
            d,
            ha="center",
            va="bottom",
            fontsize=9,
            color=colors[d],
            fontweight="bold",
        )
    ax.set_yticks([])
    ax.set_title("Primitive domains (type-colored)")
    ax.set_ylim(0, 1.4)
    fig.tight_layout()
    out = out_dir / _SPEC_BY_LABEL["fig:domain_coverage"].filename
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"  ✓ {out.name}")
    return out


def fig_product_space_annotation(project_root: Path, out_dir: Path) -> Path:
    """Product space with TOTAL annotation and zero-bar arrow."""
    grammar = load_grammar(project_root)
    fig, ax = plt.subplots(figsize=(7, 4))

    total = grammar.product_size
    effective = grammar.effective_product_size
    reserved = total - effective

    bars = ax.bar(
        ["Total", "Effective", "Reserved-only"],
        [total, effective, reserved],
        color=["#0d9488", "#1d4ed8", "#94a3b8"],
    )

    for bar in bars:
        h = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            h + 1,
            str(h),
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold",
        )

    if reserved == 0:
        ax.annotate(
            "0 (all reserved slots\nare excluded)",
            xy=(2, 0),
            xytext=(1.5, effective * 0.3),
            arrowprops=dict(arrowstyle="->", color="#334155"),
            fontsize=8,
            color="#334155",
        )

    ax.set_ylabel("Count")
    ax.set_title(f"Grammar product space (seed={grammar.seed})")
    fig.tight_layout()
    out = out_dir / _SPEC_BY_LABEL["fig:product_space"].filename
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"  ✓ {out.name}")
    return out


def fig_coverage_by_module(coverage_full_json: Path, out_dir: Path) -> Path:
    """Horizontal bar chart of real per-module branch coverage.

    Reads the persisted ``coverage.json`` written by
    ``measure_test_summary(..., full_report_out=...)`` — never invents
    per-module numbers. Modules below the repo's 90% floor are drawn in a
    distinct warning color so the figure is honest about known gaps rather
    than only showing the passing aggregate.
    """
    data = json.loads(Path(coverage_full_json).read_text())
    rows = [(path, entry["summary"]["percent_covered"]) for path, entry in data["files"].items()]
    # Shorten paths to "module" or "primitives/module" relative to src/.
    short_rows = []
    for path, pct in rows:
        parts = Path(path).parts
        idx = parts.index("src") if "src" in parts else 0
        short = "/".join(parts[idx + 1 :])
        short_rows.append((short, pct))
    short_rows.sort(key=lambda r: r[1])

    names = [r[0] for r in short_rows]
    pcts = [r[1] for r in short_rows]
    colors = ["#dc2626" if p < 90 else "#0d9488" for p in pcts]

    fig, ax = plt.subplots(figsize=(8, max(3, 0.28 * len(names))))
    ax.barh(names, pcts, color=colors)
    ax.axvline(90, color="#334155", linestyle="--", linewidth=1)
    ax.text(90.5, len(names) - 0.5, "90% floor", fontsize=8, color="#334155", va="top")
    ax.set_xlim(0, 105)
    ax.set_xlabel("Branch coverage (%)")
    ax.set_title("Per-module test coverage (real, measured this build)")
    fig.tight_layout()
    out = out_dir / _SPEC_BY_LABEL["fig:coverage_by_module"].filename
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"  ✓ {out.name}")
    return out


def generate_manuscript_figures(project_root: Path, out_dir: Path) -> list[Path]:
    """Write all autopoiesis manuscript figures to *out_dir*."""
    return [
        fig_stacked_product(project_root, out_dir),
        fig_domain_coverage(out_dir),
        fig_product_space_annotation(project_root, out_dir),
    ]
