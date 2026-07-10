#!/usr/bin/env python3
"""Thin orchestrator: render descriptor figures into ``manuscript/figures/``.

Computation lives in tested ``src/data_descriptor`` preparers; this script only
plots (all rendering in ``generate_figures``) and prints output paths. Run from
the monorepo root with ``uv run python .../scripts/generate_figures.py``.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import matplotlib.pyplot as plt  # noqa: E402

import data_descriptor as dd  # noqa: E402

INK, TEAL, BLUE, AMBER, RED, GREEN = "#0f172a", "#0f766e", "#1e3a8a", "#b45309", "#b91c1c", "#15803d"


def generate_figures(project_root: Path | None = None) -> list[Path]:
    """Render every descriptor figure and return the written PNG paths."""
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

    def head(table, columns) -> None:
        for col in range(len(columns)):
            table[0, col].set_facecolor(BLUE)
            table[0, col].set_text_props(color="white", fontweight="bold")

    schema = dd.schema_table_rows(descriptor)
    fig, ax = plt.subplots(figsize=(9.0, 0.55 * len(schema) + 1.2))
    ax.axis("off")
    cols = ["field", "type", "nullable", "unit", "constraint"]
    cells = [[r.name, r.field_type, r.nullable, r.unit or "—", r.constraint or "—"] for r in schema]
    table = ax.table(cellText=cells, colLabels=cols, cellLoc="left", loc="center")
    table.auto_set_font_size(False), table.set_fontsize(9), table.scale(1.0, 1.45)
    head(table, cols)
    ax.set_title("Field schema / data dictionary", fontsize=12, color=INK, pad=12)
    save(fig, "schema_overview.png")

    inventory = dd.file_inventory_rows(descriptor)
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    ax.bar_label(ax.barh([r.path for r in inventory], [r.rows for r in inventory], color=TEAL), padding=3, color=INK)
    ax.set_xlabel("declared rows"), ax.set_title("File inventory (declared row counts)", color=INK)
    ax.margins(x=0.15), ax.invert_yaxis()
    save(fig, "file_inventory.png")

    steps = dd.provenance_steps(descriptor)
    fig, ax = plt.subplots(figsize=(2.6 * len(steps) + 0.5, 2.2))
    ax.axis("off"), ax.set_xlim(0, len(steps)), ax.set_ylim(0, 1)
    for step in steps:
        ax.add_patch(plt.Rectangle((step.index + 0.1, 0.3), 0.8, 0.4, color=TEAL, alpha=0.9))
        ax.text(step.index + 0.5, 0.5, step.step, ha="center", va="center", color="white", fontweight="bold")
        ax.text(step.index + 0.5, 0.18, step.agent, ha="center", va="center", color=INK, fontsize=7)
        if step.index < len(steps) - 1:
            ax.annotate("", (step.index + 1.1, 0.5), (step.index + 0.9, 0.5), arrowprops={"arrowstyle": "->"})
    ax.set_title("Provenance chain", color=INK)
    save(fig, "provenance_flow.png")

    cats = ["error", "warning"]
    clean, broken = dd.severity_counts(descriptor), dd.severity_counts(dd.demo_broken_descriptor(descriptor))
    fig, ax = plt.subplots(figsize=(6.2, 3.8))
    ax.bar([i - 0.19 for i in range(2)], [clean[c] for c in cats], 0.38, label="fixture descriptor", color=GREEN)
    ax.bar([i + 0.19 for i in range(2)], [broken[c] for c in cats], 0.38, label="perturbed (demo)", color=RED)
    ax.set_xticks(range(2), cats), ax.set_ylabel("finding count"), ax.legend()
    ax.set_title("Quality gate: clean fixture vs. deliberately-broken demo", color=INK)
    save(fig, "quality_gate.png")

    def vrow(check):
        actual = "—" if check.actual_rows < 0 else str(check.actual_rows)
        mark = "match" if check.checksum_ok else ("absent" if check.status == "absent" else "MISMATCH")
        return [check.path, str(check.declared_rows), actual, mark, check.status]

    checks = dd.verify_descriptor_files(descriptor, root / "data")
    fig, ax = plt.subplots(figsize=(8.5, 0.6 * len(checks) + 1.4))
    ax.axis("off")
    cols = ["file", "declared rows", "actual rows", "checksum", "status"]
    table = ax.table(cellText=[vrow(c) for c in checks], colLabels=cols, cellLoc="center", loc="center")
    table.auto_set_font_size(False), table.set_fontsize(9), table.scale(1.0, 1.5)
    head(table, cols)
    for i, c in enumerate(checks, start=1):
        table[i, 4].set_text_props(color=GREEN if c.status == "verified" else (AMBER if c.status == "absent" else RED))
    ax.set_title(f"Descriptor↔file verification (readiness {report.readiness_score})", fontsize=12, color=INK, pad=12)
    save(fig, "checksum_verification.png")
    return written


def main() -> None:
    """CLI entry point."""
    import shutil

    written = generate_figures()
    # manuscript/figures/ is the git-tracked canonical location; the Beamer
    # slide renderer resolves ../figures/ against output/, so mirror a
    # disposable copy to output/figures/ (sibling convention, e.g.
    # template_pools_rules_tools scripts/05_generate_figures.py).
    output_figures = Path(__file__).resolve().parents[1] / "output" / "figures"
    output_figures.mkdir(parents=True, exist_ok=True)
    for figure_path in written:
        mirrored = output_figures / figure_path.name
        shutil.copy2(figure_path, mirrored)
        print(figure_path)
        print(mirrored)


if __name__ == "__main__":
    main()
