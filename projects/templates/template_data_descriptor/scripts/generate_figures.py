#!/usr/bin/env python3
"""Render descriptor figures, mirror them to output, and register provenance."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(PROJECT_ROOT / "src"), str(PROJECT_ROOT.parents[2])]

import matplotlib.pyplot as plt  # noqa: E402

import data_descriptor as dd  # noqa: E402
from infrastructure.documentation.generated_figure_registry import publish_generated_figures  # noqa: E402

INK, TEAL, BLUE, AMBER, RED, GREEN = "#0f172a", "#0f766e", "#1e3a8a", "#b45309", "#b91c1c", "#15803d"


def generate_figures(project_root: Path | None = None) -> list[Path]:
    root = project_root or PROJECT_ROOT
    descriptor = json.loads((root / "data" / "example_descriptor.json").read_text(encoding="utf-8"))
    figures_dir = root / "manuscript" / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    report = dd.build_descriptor_report(descriptor)
    written: list[Path] = []

    def save(figure, name: str) -> None:
        figure.savefig(figures_dir / name, dpi=120, bbox_inches="tight")
        plt.close(figure)
        written.append(figures_dir / name)

    def style_table(table, columns, scale: float) -> None:
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1.0, scale)
        for col in range(len(columns)):
            table[0, col].set_facecolor(BLUE)
            table[0, col].set_text_props(color="white", fontweight="bold")

    schema = dd.schema_table_rows(descriptor)
    fig, ax = plt.subplots(figsize=(9.0, 0.55 * len(schema) + 1.2))
    ax.axis("off")
    cols = ["field", "type", "nullable", "unit", "constraint"]
    cells = [[r.name, r.field_type, r.nullable, r.unit or "—", r.constraint or "—"] for r in schema]
    table = ax.table(cellText=cells, colLabels=cols, cellLoc="left", loc="center")
    style_table(table, cols, 1.45)
    ax.set_title("Field schema / data dictionary", fontsize=12, color=INK, pad=12)
    save(fig, dd.descriptor_figure_spec("fig:schema_overview").filename)

    inventory = dd.file_inventory_rows(descriptor)
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    ax.bar_label(ax.barh([r.path for r in inventory], [r.rows for r in inventory], color=TEAL), padding=3, color=INK)
    ax.set_xlabel("declared rows")
    ax.set_title("File inventory (declared row counts)", color=INK)
    ax.margins(x=0.15)
    ax.invert_yaxis()
    save(fig, dd.descriptor_figure_spec("fig:file_inventory").filename)

    steps = dd.provenance_steps(descriptor)
    fig, ax = plt.subplots(figsize=(2.6 * len(steps) + 0.5, 2.2))
    ax.axis("off")
    ax.set_xlim(0, len(steps))
    ax.set_ylim(0, 1)
    for step in steps:
        ax.add_patch(plt.Rectangle((step.index + 0.1, 0.3), 0.8, 0.4, color=TEAL, alpha=0.9))
        ax.text(step.index + 0.5, 0.5, step.step, ha="center", va="center", color="white", fontweight="bold")
        ax.text(step.index + 0.5, 0.18, step.agent, ha="center", va="center", color=INK, fontsize=7)
        if step.index < len(steps) - 1:
            ax.annotate("", (step.index + 1.1, 0.5), (step.index + 0.9, 0.5), arrowprops={"arrowstyle": "->"})
    ax.set_title("Provenance chain", color=INK)
    save(fig, dd.descriptor_figure_spec("fig:provenance_flow").filename)

    cats = ["error", "warning"]
    clean, broken = dd.severity_counts(descriptor), dd.severity_counts(dd.demo_broken_descriptor(descriptor))
    fig, ax = plt.subplots(figsize=(6.2, 3.8))
    ax.bar([i - 0.19 for i in range(2)], [clean[c] for c in cats], 0.38, label="fixture descriptor", color=GREEN)
    ax.bar([i + 0.19 for i in range(2)], [broken[c] for c in cats], 0.38, label="perturbed (demo)", color=RED)
    ax.set_xticks(range(2), cats)
    ax.set_ylabel("finding count")
    ax.legend()
    ax.set_title("Quality gate: clean fixture vs. deliberately-broken demo", color=INK)
    save(fig, dd.descriptor_figure_spec("fig:quality_gate").filename)

    checks = dd.verify_descriptor_files(descriptor, root / "data")
    fig, ax = plt.subplots(figsize=(8.5, 0.6 * len(checks) + 1.4))
    ax.axis("off")
    cols = ["file", "declared rows", "actual rows", "checksum", "status"]
    table = ax.table(cellText=dd.verification_table_rows(checks), colLabels=cols, cellLoc="center", loc="center")
    style_table(table, cols, 1.5)
    for i, c in enumerate(checks, start=1):
        table[i, 4].set_text_props(color=GREEN if c.status == "verified" else (AMBER if c.status == "absent" else RED))
    ax.set_title(f"Descriptor↔file verification (readiness {report.readiness_score})", fontsize=12, color=INK, pad=12)
    save(fig, dd.descriptor_figure_spec("fig:checksum_verification").filename)
    return written


def main(project_root: Path | None = None) -> list[Path]:
    root = project_root or PROJECT_ROOT
    rendered = generate_figures(project_root=root)
    published = publish_generated_figures(
        root / "output" / "figures",
        dd.DESCRIPTOR_FIGURE_SPECS,
        rendered,
        schema_version=dd.FIGURE_REGISTRY_SCHEMA,
    )
    written = [*rendered, *published]
    for path in written:
        print(path)
    return written


if __name__ == "__main__":
    main()
