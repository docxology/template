"""Generated markdown tables for sheaf track layers and binding matrix."""

from __future__ import annotations

from pathlib import Path

from manuscript.sheaf.coverage import load_sheaf_coverage_context
from manuscript.sheaf.models import CoverageMatrix, SheafManifest, TrackRegistry


def _table_text(value: object) -> str:
    """Return compact table-safe prose without introducing Markdown cells."""
    text = "" if value is None else str(value)
    return " ".join(text.replace("|", "∣").split()) or "—"


def _humanize_identifier(value: object) -> str:
    """Turn a machine identifier into short, breakable publication prose."""
    text = _table_text(value)
    if text == "—":
        return text
    return " ".join(text.replace("_", " ").replace("-", " ").replace(".", " ").split())


def _humanized_list(values: object) -> str:
    """Render a JSON string list as breakable prose while preserving order."""
    if not isinstance(values, list):
        return "—"
    items = [_humanize_identifier(value) for value in values]
    return ", ".join(item for item in items if item != "—") or "—"


def _path_basename(value: object) -> str:
    """Render a source or artifact pointer as a short, breakable basename."""
    path = _table_text(value)
    if path == "—":
        return path
    return " ".join(Path(path).name.replace("_", " ").split())


def _path_basename_list(values: object) -> str:
    """Render ordered source pointers without long unbreakable repository paths."""
    if not isinstance(values, list):
        return "—"
    items = [_path_basename(value) for value in values]
    return ", ".join(item for item in items if item != "—") or "—"


def render_track_registry_table(registry: TrackRegistry) -> str:
    """Render track registry table."""
    lines = [
        "<!-- sheaf-layers:registry -->",
        "## Sheaf fragment track registry",
        "",
        "Compose order and renderer bindings from `manuscript/sheaf/tracks.yaml`.",
        "",
        "| Order | Track id | Label | Renderer | Paper role | Paper use | Optional |",
        "| ---: | --- | --- | --- | --- | --- | --- |",
    ]
    for track_id, spec in sorted(registry.tracks.items(), key=lambda item: item[1].order):
        optional = "Yes" if spec.optional else "No"
        lines.append(
            f"| {spec.order} | `{track_id}` | {spec.label} | `{spec.renderer}` | "
            f"{spec.paper_role} | {spec.paper_use} | {optional} |"
        )
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
    """Render a compact, publication-readable binding matrix summary.

    The canonical cell-level matrix remains in the JSON/heatmap artifacts.  A
    track omitted from both summary lists is absent (not bound) for that row.
    """
    lines = [
        "<!-- sheaf-layers:binding-matrix -->",
        "## IMRAD binding matrix",
        "",
        "Compact section summary: **P** = present (bound and file exists); "
        "**M** = missing (bound, file absent). Every track not listed for a row is absent (not bound).",
        "",
        "The complete cell-level matrix is stored in `output/data/sheaf_coverage_matrix.json` "
        "and visualized in [@fig:sheaf_coverage_heatmap].",
        "",
        "| Section | Present tracks (P) | Missing tracks (M) |",
        "| --- | --- | --- |",
    ]
    for row in matrix.sections:
        prefix = "↳ " * row.depth
        title = f"{prefix}{row.title}"
        if row.kind == "group":
            title = f"**{title} (group)**"
        cells_by_track = {cell.track_id: cell for cell in row.cells}
        present = [track_id for track_id in matrix.track_ids if cells_by_track[track_id].status == "present"]
        missing = [track_id for track_id in matrix.track_ids if cells_by_track[track_id].status == "missing"]
        present_text = ", ".join(f"`{track_id}`" for track_id in present) or "—"
        missing_text = ", ".join(f"`{track_id}`" for track_id in missing) or "—"
        lines.append(f"| {title} | {present_text} | {missing_text} |")
    lines.extend(
        [
            "",
            "**Totals:** {{coverage_present}} present / {{coverage_bound}} bound / {{coverage_missing}} missing.",
            "",
        ]
    )
    return "\n".join(lines)


def render_coverage_legend() -> str:
    """Render coverage legend."""
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
    """Render evidence crosswalk table."""
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
    """Render artifact producer table."""
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
    """Render semantic restrictions table."""
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
    """Render every improvement row as a compact publication summary."""
    import json

    path = project_root / "output" / "data" / "track_improvement_scope.json"
    payload = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    roadmap = payload.get("improvement_roadmap") or []
    promotions = {
        row.get("track_id"): row
        for row in (payload.get("promotion_matrix") or [])
        if isinstance(row, dict) and row.get("track_id")
    }
    lines = [
        "<!-- sheaf-layers:track-improvement-scope -->",
        "## Track improvement scope",
        "",
        "Every roadmap row is shown below in canonical order. The source-owned full matrix in "
        "output/data/track_improvement_scope.json remains the authority for exact priorities, scope text, "
        "gate or predicate IDs, negative-control IDs, and promotion fields.",
        "",
        "| Track | Evidence progression | Status, gate, and negative control |",
        "| --- | --- | --- |",
    ]
    for row in roadmap:
        track_id = row.get("track_id")
        promotion = promotions.get(track_id) or {}
        producer = promotion.get("producer")
        producer_text = f"Producer: {_path_basename(producer)}. " if producer else "Producer: none while blocked. "
        current = row.get("current_proof")
        next_artifact = row.get("next_proving_artifact")
        if current == next_artifact:
            evidence = f"{producer_text}Current and next evidence: {_path_basename(current)}."
        else:
            evidence = (
                f"{producer_text}Current proof: {_path_basename(current)}. "
                f"Next proving artifact: {_path_basename(next_artifact)}."
            )
        status = _humanize_identifier(row.get("status"))
        priority = _humanize_identifier(row.get("priority"))
        gate = _humanize_identifier(row.get("gate_or_predicate"))
        control = _humanize_identifier(row.get("negative_control"))
        scope = _table_text(row.get("scope_boundary"))
        lines.append(
            f"| **{_humanize_identifier(track_id)}** | {evidence} | "
            f"Status: {status}; priority: {priority}. Gate or predicate: {gate}. "
            f"Negative control: {control}. Scope: {scope}. |"
        )
    live_count = sum(row.get("status") == "live" for row in roadmap)
    optional_count = sum(row.get("status") == "optional" for row in roadmap)
    blocked_count = sum(row.get("status") == "blocked" for row in roadmap)
    lines.extend(
        [
            "",
            f"**Improvement rows:** {payload.get('improvement_row_count', len(roadmap))} total; "
            f"{live_count} live / {optional_count} optional / {blocked_count} blocked; every row shown.",
            "",
        ]
    )
    return "\n".join(lines)


def render_track_lane_matrix_table(project_root: Path) -> str:
    """Render every pipeline lane as a compact publication summary."""
    import json

    path = project_root / "output" / "data" / "track_lane_matrix.json"
    payload = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    rows = payload.get("rows") or []
    lines = [
        "<!-- sheaf-layers:track-lane-matrix -->",
        "## Track-lane matrix",
        "",
        "Every pipeline row is shown below in canonical order. The source-owned full matrix in "
        "output/data/track_lane_matrix.json remains the authority for exact source paths, claim IDs, "
        "semantic-restriction IDs, gate IDs, negative-control IDs, and promotion cells.",
        "",
        "| Pipeline track | Source, producer, and primary artifact | Coverage, gates, and negative control |",
        "| --- | --- | --- |",
    ]
    for row in rows:
        source_state = "present" if row.get("source_paths_present") else "missing"
        producer_state = "configured" if row.get("producer_configured") else "not configured"
        artifact_state = "present" if row.get("primary_artifact_exists") else "missing"
        route = (
            f"Sources ({source_state}): {_path_basename_list(row.get('source_paths'))}. "
            f"Producer ({producer_state}): {_path_basename(row.get('producer'))}. "
            f"Primary artifact ({artifact_state}): {_path_basename(row.get('primary_artifact'))}."
        )
        requirement = "required" if row.get("required") else "optional"
        completeness = "matrix complete" if row.get("matrix_complete") else "matrix incomplete"
        registration = "registered" if row.get("sheaf_tracks_registered") else "unregistered"
        semantic_count = len(row.get("semantic_restrictions") or [])
        lines.append(
            f"| **{_humanize_identifier(row.get('track_id'))}** | {route} | "
            f"Role: {_table_text(row.get('label'))}. {requirement.capitalize()}; {completeness}. "
            f"Fragments ({registration}): {_humanized_list(row.get('sheaf_tracks'))}; "
            f"{row.get('manuscript_consumer_count', 0)} manuscript consumers; "
            f"{row.get('claim_id_count', 0)} claims; {semantic_count} semantic restrictions. "
            f"Gates: {_humanized_list(row.get('validation_gates'))}. "
            f"Negative control: {_humanize_identifier(row.get('negative_control'))}. |"
        )
    lines.extend(
        [
            "",
            f"**Pipeline rows:** {payload.get('row_count', len(rows))} total; "
            f"{payload.get('required_track_count', 0)} required; every row shown.",
            "",
        ]
    )
    return "\n".join(lines)


def render_section_status_table(project_root: Path) -> str:
    """Render section status table."""
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
    """Render track status table."""
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
    """Render sheaf render log table."""
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
    """Render sheaf layers markdown."""
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
        render_track_lane_matrix_table(project_root),
        render_track_improvement_scope_table(project_root),
    ]
    return "\n".join(parts)


# Backward-compatible alias for callers predating the rename.
render_methods_sheaf_layers_markdown = render_sheaf_layers_markdown
