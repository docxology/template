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


def render_evidence_crosswalk_table(project_root: Path) -> str:
    from manuscript.sheaf.semantic import build_evidence_crosswalk

    crosswalk = build_evidence_crosswalk(project_root)
    lines = [
        "<!-- sheaf-layers:evidence-crosswalk -->",
        "## Evidence crosswalk",
        "",
        "| Claim | Artifact | Producer | Gates |",
        "| --- | --- | --- | --- |",
    ]
    for claim in (crosswalk.get("claims") or [])[:8]:
        gates = ", ".join(claim.get("validation_gates") or [])
        lines.append(f"| `{claim.get('id')}` | `{claim.get('path')}` | `{claim.get('producer')}` | {gates} |")
    lines.extend(["", f"**Claim rows:** {crosswalk.get('claim_count', 0)} typed evidence claims.", ""])
    return "\n".join(lines)


def render_artifact_producer_table(project_root: Path) -> str:
    from manuscript.sheaf.semantic import build_validation_dependency_graph

    graph = build_validation_dependency_graph(project_root)
    lines = [
        "<!-- sheaf-layers:artifact-producers -->",
        "## Artifact producer graph",
        "",
        "| Artifact | Producer | Configured | Consumers |",
        "| --- | --- | --- | --- |",
    ]
    for rel, record in sorted((graph.get("artifacts") or {}).items()):
        if (
            rel.startswith("output/data/")
            or rel.startswith("output/reports/")
            or rel == "output/figures/si_belief_trajectory.gif"
        ):
            configured = "Yes" if record.get("produced_by_configured_analysis") else "No"
            consumers = ", ".join(record.get("consumers") or record.get("validation_gates") or [])
            lines.append(f"| `{rel}` | `{record.get('producer')}` | {configured} | {consumers} |")
    lines.extend(["", f"**Producer issues:** {len(graph.get('issues') or [])}.", ""])
    return "\n".join(lines)


def render_semantic_restrictions_table(project_root: Path) -> str:
    from manuscript.sheaf.semantic import build_semantic_gluing_certificate

    restrictions = build_semantic_gluing_certificate(project_root).get("restrictions") or {}
    rows = [
        ("Coverage missing", restrictions.get("coverage_missing")),
        ("Policy comparison rows", restrictions.get("policy_comparison_run_count")),
        ("Policy grid complete", restrictions.get("policy_comparison_complete_grid")),
        ("Policy posterior rows", restrictions.get("policy_posterior_row_count")),
        ("Policy posterior normalized", restrictions.get("policy_posterior_normalized")),
        ("Runtime unexpected warnings", restrictions.get("pymdp_runtime_unexpected_warning_count")),
        ("Graph-world trace agrees", restrictions.get("graph_world_steps_match")),
        ("Animation frames", restrictions.get("animation_frame_count")),
        ("Lean all proved", restrictions.get("lean_all_proved")),
        ("GNN ontology ok", restrictions.get("gnn_ontology_ok")),
        ("Configured producers ok", restrictions.get("configured_artifact_producers_ok")),
        ("Semantic certificate ok", restrictions.get("semantic_ok")),
        ("Dependency edges ok", restrictions.get("dependency_edge_types_ok")),
        ("Track scope complete", restrictions.get("track_improvement_scope_complete")),
        ("Empirical adapter blocked", restrictions.get("blocked_empirical_adapter")),
        ("Provenance bundles complete", restrictions.get("provenance_bundle_complete")),
        ("Replay rows matched", restrictions.get("replay_matrix_all_matched")),
        ("Sensitivity complete", restrictions.get("sensitivity_complete_grid")),
        ("Uncertainty normalized", restrictions.get("uncertainty_all_normalized")),
        ("Evidence fields mapped", restrictions.get("evidence_fields_mapped")),
        ("Release bundle sources present", restrictions.get("release_bundle_sources_present")),
        ("Theorem traceability linked", restrictions.get("theorem_traceability_linked")),
        ("Gate ergonomics indexed", restrictions.get("gate_ergonomics_indexed")),
        ("Interop lossless", restrictions.get("interop_all_lossless")),
        ("Scope toy-only", restrictions.get("scope_boundary_toy_only")),
    ]
    lines = [
        "<!-- sheaf-layers:semantic-restrictions -->",
        "## Semantic gluing restrictions",
        "",
        "| Restriction | Value |",
        "| --- | --- |",
    ]
    lines.extend(f"| {name} | `{value}` |" for name, value in rows)
    lines.append("")
    return "\n".join(lines)


def render_track_improvement_scope_table(project_root: Path) -> str:
    import json

    path = project_root / "output" / "data" / "track_improvement_scope.json"
    payload = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    lines = [
        "<!-- sheaf-layers:track-improvement-scope -->",
        "## Track improvement scope",
        "",
        "| Track | Status | Current proof | Next artifact | Gate | Negative control |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in (payload.get("improvement_roadmap") or [])[:12]:
        lines.append(
            "| "
            f"`{row.get('track_id')}` | {row.get('status')} | `{row.get('current_proof')}` | "
            f"`{row.get('next_proving_artifact')}` | `{row.get('gate_or_predicate')}` | "
            f"{row.get('negative_control')} |"
        )
    lines.extend(["", f"**Improvement rows:** {payload.get('improvement_row_count', 0)}.", ""])
    return "\n".join(lines)


def render_section_status_table(project_root: Path) -> str:
    from manuscript.sheaf.status import build_sheaf_section_status_matrix

    payload = build_sheaf_section_status_matrix(project_root)
    lines = [
        "<!-- sheaf-layers:section-status -->",
        "## Section-track status",
        "",
        "Generated status for the current manuscript sheaf, summarized per composable section.",
        "",
        "| Section | IMRAD | Bound | Present | Missing | Status |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in payload.get("sections") or []:
        if not row.get("compose"):
            continue
        lines.append(
            "| "
            f"{row.get('title')} | {row.get('imrad')} | {row.get('bound_count')} | "
            f"{row.get('present_count')} | {row.get('missing_count')} | `{row.get('status')}` |"
        )
    lines.extend(
        [
            "",
            f"**Section status:** {payload.get('fully_sheafed_section_count', 0)} / "
            f"{payload.get('composable_section_count', 0)} composable sections fully sheafed; "
            f"{payload.get('missing_required_count', 0)} required bound fragments missing.",
            "",
        ]
    )
    return "\n".join(lines)


def render_track_status_table(project_root: Path) -> str:
    from manuscript.sheaf.status import build_sheaf_section_status_matrix

    payload = build_sheaf_section_status_matrix(project_root)
    lines = [
        "<!-- sheaf-layers:track-status -->",
        "## Track status",
        "",
        "| Track | Renderer | Bound sections | Present | Missing | Claims | Status |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in payload.get("tracks") or []:
        lines.append(
            "| "
            f"`{row.get('track_id')}` | `{row.get('renderer')}` | {row.get('bound_section_count')} | "
            f"{row.get('present_section_count')} | {row.get('missing_section_count')} | "
            f"{row.get('claim_count')} | `{row.get('status')}` |"
        )
    lines.extend(["", f"**Status cells:** {payload.get('cell_count', 0)} section-track cells.", ""])
    return "\n".join(lines)


def render_sheaf_render_log_table(project_root: Path) -> str:
    from manuscript.sheaf.status import build_sheaf_render_log

    payload = build_sheaf_render_log(project_root)
    lines = [
        "<!-- sheaf-layers:render-log -->",
        "## Render and logging summary",
        "",
        "| Event | Component | Output | Status | Detail |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in payload.get("events") or []:
        lines.append(
            "| "
            f"`{row.get('event_id')}` | `{row.get('component')}` | `{row.get('output')}` | "
            f"`{row.get('status')}` | {row.get('detail')} |"
        )
    lines.extend(["", f"**Render events:** {payload.get('event_count', 0)}.", ""])
    return "\n".join(lines)


def render_sheaf_layers_markdown(project_root: Path) -> str:
    ctx = load_sheaf_coverage_context(project_root)
    parts = [
        render_track_registry_table(ctx.registry),
        render_binding_matrix_table(ctx.matrix, ctx.manifest, project_root=project_root),
        render_coverage_legend(),
        render_section_status_table(project_root),
        render_track_status_table(project_root),
        render_sheaf_render_log_table(project_root),
        render_evidence_crosswalk_table(project_root),
        render_artifact_producer_table(project_root),
        render_semantic_restrictions_table(project_root),
        render_track_improvement_scope_table(project_root),
    ]
    return "\n".join(parts)


# Backward-compatible alias for callers predating the rename.
render_methods_sheaf_layers_markdown = render_sheaf_layers_markdown
