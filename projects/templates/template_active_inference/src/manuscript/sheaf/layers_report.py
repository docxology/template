"""Generated markdown tables for sheaf track layers and binding matrix."""

from __future__ import annotations

from pathlib import Path

from manuscript.sheaf.coverage import load_sheaf_coverage_context
from manuscript.sheaf.models import CoverageMatrix, SheafManifest, TrackRegistry, coverage_cell_symbol


def render_track_registry_table(registry: TrackRegistry) -> str:
    lines = [
        "<!-- sheaf-layers:registry -->",
        "## Sheaf fragment track registry",
        "",
        "Compose order and renderer bindings from `manuscript/sheaf/tracks.yaml`.",
        "",
        "| Order | Track id | Label | Renderer | Optional |",
        "| ---: | --- | --- | --- | --- |",
    ]
    for track_id, spec in sorted(registry.tracks.items(), key=lambda item: item[1].order):
        optional = "Yes" if spec.optional else "No"
        lines.append(f"| {spec.order} | `{track_id}` | {spec.label} | `{spec.renderer}` | {optional} |")
    lines.append("")
    lines.append("**Track count:** {{sheaf_track_count}} registered fragment types.")
    lines.append("")
    return "\n".join(lines)


def render_binding_matrix_table(
    matrix: CoverageMatrix,
    manifest: SheafManifest,
    *,
    project_root: Path | None = None,
) -> str:
    header = "| Section | " + " | ".join(matrix.track_ids) + " |"
    sep = "| --- | " + " | ".join("---" for _ in matrix.track_ids) + " |"
    lines = [
        "<!-- sheaf-layers:binding-matrix -->",
        "## IMRAD binding matrix",
        "",
        "Section rows versus fragment track columns. "
        "**P** = present (bound and file exists); **—** = absent (not bound); **M** = missing (bound, file absent).",
        "",
        header,
        sep,
    ]
    for row in matrix.sections:
        indent = "  " * row.depth
        title = f"{indent}{row.title}"
        if row.kind == "group":
            title = f"{title} (group)"
        cells_by_track = {cell.track_id: cell for cell in row.cells}
        symbols = [coverage_cell_symbol(cells_by_track[tid].color) for tid in matrix.track_ids]
        lines.append(f"| {title} | " + " | ".join(symbols) + " |")
    lines.extend(
        [
            "",
            "**Totals:** {{coverage_present}} present / {{coverage_bound}} bound / {{coverage_missing}} missing.",
            "",
        ]
    )
    return "\n".join(lines)


def render_coverage_legend() -> str:
    return "\n".join(
        [
            "<!-- sheaf-layers:legend -->",
            "| Symbol | Coverage color | Meaning |",
            "| --- | --- | --- |",
            "| P | Black | Track **present** (bound and fragment exists) |",
            "| — | White | **Absent** (not bound for this section) |",
            "| M | Gray | **Missing** (bound but fragment file absent) |",
            "",
        ]
    )


def render_sheaf_layers_markdown(project_root: Path) -> str:
    ctx = load_sheaf_coverage_context(project_root)
    parts = [
        render_track_registry_table(ctx.registry),
        render_binding_matrix_table(ctx.matrix, ctx.manifest, project_root=project_root),
        render_coverage_legend(),
    ]
    return "\n".join(parts)


# Backward-compatible alias for callers predating the rename.
render_methods_sheaf_layers_markdown = render_sheaf_layers_markdown
