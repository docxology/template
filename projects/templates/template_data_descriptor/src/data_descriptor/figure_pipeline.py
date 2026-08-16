"""Typed rendering and publication pipeline for descriptor figures.

The executable under ``scripts/`` is intentionally only an entry point.  This
module owns the reusable producer: it loads one descriptor snapshot, derives
the same verification evidence used by the plots and alternate text, renders
the complete figure set, and publishes that exact run fail-closed.

Matplotlib is imported lazily after selecting the non-interactive backend so
descriptor validation remains cheap and display-independent for callers that
do not render figures.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, cast

from data_descriptor.descriptor import build_descriptor_report
from data_descriptor.figures import (
    FIGURE_REGISTRY_SCHEMA,
    DescriptorFigureSpec,
    demo_broken_descriptor,
    descriptor_figure_spec,
    descriptor_figure_specs_for_data,
    file_inventory_rows,
    provenance_steps,
    schema_table_rows,
    severity_counts,
    verification_table_rows,
)
from data_descriptor.registry import FigureSpecLike, publish_generated_figures
from data_descriptor.verification import FileVerification, verify_descriptor_files

if TYPE_CHECKING:
    from matplotlib.figure import Figure
    from matplotlib.table import Table


INK = "#0f172a"
TEAL = "#0f766e"
BLUE = "#1e3a8a"
AMBER = "#b45309"
RED = "#b91c1c"
GREEN = "#15803d"


class FigurePublisher(Protocol):
    """Callable contract shared by the monorepo and standalone publishers."""

    def __call__(
        self,
        output_dir: Path,
        specs: Iterable[FigureSpecLike],
        generated_paths: Iterable[Path],
        *,
        schema_version: str,
    ) -> list[Path]:
        """Mirror a complete figure set and write its registry."""
        ...


@dataclass(frozen=True)
class DescriptorFigureInputs:
    """One source-bound snapshot used for plots and registry descriptions."""

    descriptor: dict[str, Any]
    checks: tuple[FileVerification, ...]
    readiness_score: float


@dataclass(frozen=True)
class DescriptorFigureRun:
    """Rendered files bound to the exact inputs from which they were built."""

    inputs: DescriptorFigureInputs
    specs: tuple[DescriptorFigureSpec, ...]
    rendered_paths: tuple[Path, ...]


def load_descriptor_figure_inputs(project_root: Path) -> DescriptorFigureInputs:
    """Load and verify the descriptor snapshot used by every figure."""
    root = Path(project_root)
    descriptor = cast(
        "dict[str, Any]",
        json.loads((root / "data" / "example_descriptor.json").read_text(encoding="utf-8")),
    )
    report = build_descriptor_report(descriptor)
    checks = verify_descriptor_files(descriptor, root / "data")
    return DescriptorFigureInputs(
        descriptor=descriptor,
        checks=checks,
        readiness_score=report.readiness_score,
    )


def render_descriptor_figures(
    project_root: Path,
    *,
    inputs: DescriptorFigureInputs | None = None,
) -> DescriptorFigureRun:
    """Render the canonical five-figure set from one prepared input snapshot."""
    os.environ.setdefault("MPLBACKEND", "Agg")
    import matplotlib.pyplot as plt

    root = Path(project_root)
    prepared = inputs or load_descriptor_figure_inputs(root)
    descriptor = prepared.descriptor
    bound_specs = descriptor_figure_specs_for_data(
        descriptor,
        prepared.checks,
        readiness_score=prepared.readiness_score,
    )
    figures_dir = root / "manuscript" / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    def save(figure: Figure, spec: DescriptorFigureSpec) -> None:
        path = figures_dir / spec.filename
        figure.savefig(path, dpi=120, bbox_inches="tight")
        plt.close(figure)
        written.append(path)

    schema = schema_table_rows(descriptor)
    figure, axis = plt.subplots(figsize=(9.0, 0.55 * len(schema) + 1.2))
    axis.axis("off")
    schema_columns = ["field", "type", "nullable", "unit", "constraint"]
    schema_cells = [
        [row.name, row.field_type, row.nullable, row.unit or "—", row.constraint or "—"] for row in schema
    ] or [["No declared fields", "—", "—", "—", "—"]]
    table = axis.table(cellText=schema_cells, colLabels=schema_columns, cellLoc="left", loc="center")
    _style_table(table, len(schema_columns), scale=1.45)
    axis.set_title("Field schema / data dictionary", fontsize=12, color=INK, pad=12)
    save(figure, descriptor_figure_spec("fig:schema_overview"))

    inventory = file_inventory_rows(descriptor)
    figure, axis = plt.subplots(figsize=(7.5, 3.6))
    bars = axis.barh([row.path for row in inventory], [row.rows for row in inventory], color=TEAL)
    axis.bar_label(bars, padding=3, color=INK)
    axis.set_xlabel("declared rows")
    axis.set_title("File inventory (declared row counts)", color=INK)
    axis.margins(x=0.15)
    axis.invert_yaxis()
    save(figure, descriptor_figure_spec("fig:file_inventory"))

    steps = provenance_steps(descriptor)
    figure, axis = plt.subplots(figsize=(2.6 * len(steps) + 0.5, 2.2))
    axis.axis("off")
    axis.set_xlim(0, max(1, len(steps)))
    axis.set_ylim(0, 1)
    for step in steps:
        axis.add_patch(plt.Rectangle((step.index + 0.1, 0.3), 0.8, 0.4, color=TEAL, alpha=0.9))
        axis.text(step.index + 0.5, 0.5, step.step, ha="center", va="center", color="white", fontweight="bold")
        axis.text(step.index + 0.5, 0.18, step.agent, ha="center", va="center", color=INK, fontsize=7)
        if step.index < len(steps) - 1:
            axis.annotate("", (step.index + 1.1, 0.5), (step.index + 0.9, 0.5), arrowprops={"arrowstyle": "->"})
    axis.set_title("Provenance chain", color=INK)
    save(figure, descriptor_figure_spec("fig:provenance_flow"))

    categories = ["error", "warning"]
    clean = severity_counts(descriptor)
    broken = severity_counts(demo_broken_descriptor(descriptor))
    figure, axis = plt.subplots(figsize=(6.2, 3.8))
    axis.bar(
        [index - 0.19 for index in range(2)],
        [clean[key] for key in categories],
        0.38,
        label="fixture descriptor",
        color=GREEN,
    )
    axis.bar(
        [index + 0.19 for index in range(2)],
        [broken[key] for key in categories],
        0.38,
        label="perturbed (demo)",
        color=RED,
    )
    axis.set_xticks(range(2), categories)
    axis.set_ylabel("finding count")
    axis.legend()
    axis.set_title("Quality gate: clean fixture vs. deliberately-broken demo", color=INK)
    save(figure, descriptor_figure_spec("fig:quality_gate"))

    figure, axis = plt.subplots(figsize=(8.5, 0.6 * len(prepared.checks) + 1.4))
    axis.axis("off")
    verification_columns = ["file", "declared rows", "actual rows", "checksum", "status"]
    verification_rows = verification_table_rows(prepared.checks) or (
        ("No declared files", "—", "—", "—", "unavailable"),
    )
    table = axis.table(
        cellText=verification_rows,
        colLabels=verification_columns,
        cellLoc="center",
        loc="center",
    )
    _style_table(table, len(verification_columns), scale=1.5)
    for index, check in enumerate(prepared.checks, start=1):
        color = GREEN if check.status == "verified" else (AMBER if check.status == "absent" else RED)
        table[index, 4].set_text_props(color=color)
    axis.set_title(
        f"Descriptor↔file verification (readiness {prepared.readiness_score})",
        fontsize=12,
        color=INK,
        pad=12,
    )
    save(figure, descriptor_figure_spec("fig:checksum_verification"))
    return DescriptorFigureRun(
        inputs=prepared,
        specs=bound_specs,
        rendered_paths=tuple(written),
    )


def publish_descriptor_figure_run(
    project_root: Path,
    run: DescriptorFigureRun,
    *,
    publisher: FigurePublisher = publish_generated_figures,
) -> tuple[Path, ...]:
    """Publish exactly the rendered run, with descriptions from its inputs."""
    return tuple(
        publisher(
            Path(project_root) / "output" / "figures",
            run.specs,
            run.rendered_paths,
            schema_version=FIGURE_REGISTRY_SCHEMA,
        )
    )


def generate_descriptor_figure_assets(project_root: Path) -> tuple[Path, ...]:
    """Render, mirror, and register the complete canonical figure run."""
    run = render_descriptor_figures(project_root)
    published = publish_descriptor_figure_run(project_root, run)
    return (*run.rendered_paths, *published)


def _style_table(table: Table, column_count: int, *, scale: float) -> None:
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.0, scale)
    for column in range(column_count):
        table[0, column].set_facecolor(BLUE)
        table[0, column].set_text_props(color="white", fontweight="bold")


__all__ = [
    "DescriptorFigureInputs",
    "DescriptorFigureRun",
    "FigurePublisher",
    "generate_descriptor_figure_assets",
    "load_descriptor_figure_inputs",
    "publish_descriptor_figure_run",
    "render_descriptor_figures",
]
