"""Manuscript figure writers for the autopoiesis exemplar."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .grammar import KNOWN_DOMAINS, load_grammar


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
    out = out_dir / "fig_stacked_product.png"
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
    out = out_dir / "fig_domain_coverage.png"
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
    out = out_dir / "fig_product_space.png"
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
