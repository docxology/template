"""Deterministic visualization-quality audit for generated figure artifacts."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from json_io import load_json as _load_json
from json_io import write_json as _write_json

from .integration_audit_artifacts import ALLOWED_CLAIM_LANES
from .visualization_contract import build_auxiliary_visualization_inventory, build_style_contract

VISUALIZATION_AUDIT_SCHEMA = "template_active_inference.visualization_quality_audit.v1"
STATISTICAL_VISUALIZATION_BRIDGE_SCHEMA = "template_active_inference.statistical_visualization_bridge.v1"
MIN_RENDER_WIDTH = 400
MIN_RENDER_HEIGHT = 200
MIN_RENDER_BYTES = 5_000
MIN_ASPECT_RATIO = 0.45
MAX_ASPECT_RATIO = 4.2
MIN_ALT_WORDS = 12
MIN_CAPTION_WORDS = 8
MIN_PAPER_CLAIM_WORDS = 6
ALLOWED_VISUAL_ROLES = {"trend", "comparison", "trace", "matrix", "diagram", "table", "flow", "dashboard"}
ALLOWED_EVIDENCE_ROLES = {"statistical", "source_mapped", "formal", "schematic", "scholarship", "sheaf"}
STATISTICAL_SOURCE_ARTIFACTS = {
    "output/data/analysis_statistics.json",
    "output/data/parameter_sweep.csv",
    "output/data/si_tmaze_summary.json",
    "output/data/si_tmaze_trace.json",
    "output/data/sensitivity_sweep.json",
    "output/data/uncertainty_summary.json",
    "output/data/si_policy_comparison.json",
    "output/data/pymdp_policy_posterior_grid.json",
    "output/data/causal_ablation_matrix.json",
    "output/reports/ablation_sensitivity_report.json",
    "output/reports/invariants.json",
    "output/reports/si_invariants.json",
    "output/reports/pymdp_runtime_diagnostics.json",
}


def _word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)?", text))


def _image_metrics(path: Path) -> dict[str, Any]:
    from visualizations.figure_io import image_render_metrics

    metrics = dict(image_render_metrics(path))
    aspect_ratio = float(metrics["aspect_ratio"])
    render_size_ok = (
        int(metrics["width_px"]) >= MIN_RENDER_WIDTH
        and int(metrics["height_px"]) >= MIN_RENDER_HEIGHT
        and int(metrics["size_bytes"]) >= MIN_RENDER_BYTES
    )
    metrics["render_size_ok"] = render_size_ok
    metrics["aspect_ratio_ok"] = MIN_ASPECT_RATIO <= aspect_ratio <= MAX_ASPECT_RATIO
    return metrics


def _statistical_sources(root: Path, sources: list[str]) -> tuple[list[str], bool]:
    statistical = [source for source in sources if source in STATISTICAL_SOURCE_ARTIFACTS]
    return statistical, bool(statistical) and all((root / source).exists() for source in statistical)


def _all_sources_present(root: Path, sources: list[str]) -> bool:
    return bool(sources) and all((root / source).exists() for source in sources)


def _figure_section_bindings(root: Path) -> dict[str, list[str]]:
    path = root / "figures.yaml"
    if not path.is_file():
        return {}
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return {}
    bindings: dict[str, set[str]] = {}
    for section_id, entries in (payload.get("section_figures") or {}).items():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            figure_id = entry if isinstance(entry, str) else entry.get("id") if isinstance(entry, dict) else None
            if figure_id:
                bindings.setdefault(str(figure_id), set()).add(str(section_id))
    return {figure_id: sorted(sections) for figure_id, sections in bindings.items()}


def _section_id_from_path(root: Path, path: Path) -> str:
    rel_parts = path.relative_to(root).parts
    if "imrad" in rel_parts:
        index = rel_parts.index("imrad")
        if len(rel_parts) > index + 1:
            return rel_parts[index + 1]
    stem = path.stem
    return re.sub(r"^\d+_(?:\d+_)?", "", stem)


def _imrad_section_files(root: Path) -> list[tuple[str, str]]:
    """Read every IMRaD manuscript markdown file once: ``(section_id, text)`` pairs.

    ``_figure_reference_sections`` used to re-glob and re-read this same file
    set from scratch for every figure row, turning a per-row lookup into that
    many full directory scans (~7 statistically-backed rows x ~116 imrad files
    = hundreds of redundant reads, compounding the ``scholarship.py`` version
    of the same bug as the dominant cost behind
    ``test_aggregate_forgery_controls.py`` timing out). Callers that need
    multiple figure ids should read the files once via this helper and pass
    the result to ``_figure_reference_sections`` via ``files=``.
    """

    paths = sorted((root / "manuscript" / "sections" / "imrad").glob("**/*.md")) + sorted(
        path
        for path in (root / "manuscript").glob("*.md")
        if path.name not in {"AGENTS.md", "README.md", "SYNTAX.md", "preamble.md"}
    )
    return [(_section_id_from_path(root, path), path.read_text(encoding="utf-8")) for path in paths if path.is_file()]


def _figure_reference_sections(root: Path, figure_id: str, *, files: list[tuple[str, str]] | None = None) -> list[str]:
    section_files = files if files is not None else _imrad_section_files(root)
    needles = (f"@fig:{figure_id}", f"#fig:{figure_id}")
    sections = {section_id for section_id, text in section_files if any(needle in text for needle in needles)}
    return sorted(sections)


def _manifest_section_tracks(root: Path) -> dict[str, list[str]]:
    path = root / "manuscript" / "sheaf" / "manifest.yaml"
    if not path.is_file():
        return {}
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return {}
    section_tracks: dict[str, list[str]] = {}
    for section in payload.get("sections") or []:
        section_id = section.get("id")
        if not section_id:
            continue
        tracks = section.get("tracks") or {}
        section_tracks[str(section_id)] = sorted(str(track_id) for track_id in tracks)
    return section_tracks


def _reference_section_status(row: dict[str, Any]) -> tuple[bool, bool]:
    sections = [str(section) for section in row.get("figure_reference_sections") or []]
    bindings = row.get("reference_track_bindings") or {}
    sheaf_bound = bool(sections) and all(bool(bindings.get(section)) for section in sections)
    visualization_bound = sheaf_bound and all(
        "visualization" in set(bindings.get(section) or []) for section in sections
    )
    return sheaf_bound, visualization_bound


def _figure_evidence_rows(root: Path) -> list[dict[str, Any]]:
    """Derive live figure evidence rows from registry, source maps, hashes, and renders."""
    from visualizations.figure_registry import load_figure_registry

    style_contract = build_style_contract(root)
    source_map = _load_json(root / "output" / "data" / "figure_source_map.json")
    hash_manifest = _load_json(root / "output" / "reports" / "figure_hash_manifest.json")
    sources_by_id = {str(row.get("figure_id")): row for row in source_map.get("rows") or []}
    hashes_by_path = {str(row.get("path")): row for row in hash_manifest.get("rows") or []}
    section_bindings_by_id = _figure_section_bindings(root)
    rows: list[dict[str, Any]] = []
    for figure_id, spec in sorted(load_figure_registry(root).items()):
        rel_path = f"output/figures/{spec.filename}"
        metrics = _image_metrics(root / rel_path)
        source_row = sources_by_id.get(figure_id, {})
        hash_row = hashes_by_path.get(rel_path, {})
        sources = source_row.get("source_artifacts") or source_row.get("sources") or []
        claim_lanes = [str(lane) for lane in source_row.get("claim_lanes") or []]
        statistical_sources, statistical_sources_present = _statistical_sources(
            root, [str(source) for source in sources]
        )
        section_bindings = section_bindings_by_id.get(figure_id, [])
        source_backed = source_row.get("mapped") is True and _all_sources_present(
            root, [str(source) for source in sources]
        )
        alt_word_count = _word_count(spec.alt)
        caption_word_count = _word_count(spec.caption)
        paper_claim_word_count = _word_count(spec.paper_claim)
        visual_role_ok = spec.visual_role in ALLOWED_VISUAL_ROLES
        evidence_role_ok = spec.evidence_role in ALLOWED_EVIDENCE_ROLES
        paper_claim_ok = paper_claim_word_count >= MIN_PAPER_CLAIM_WORDS
        section_bound = bool(section_bindings)
        rendered = (
            metrics["exists"]
            and metrics["render_size_ok"]
            and metrics["aspect_ratio_ok"]
            and metrics["nonblank"]
            and metrics["mode"] == "RGB"
        )
        accessibility_ok = alt_word_count >= MIN_ALT_WORDS and caption_word_count >= MIN_CAPTION_WORDS
        row = {
            "figure_id": figure_id,
            "path": rel_path,
            "sources": sources,
            "source_mapped": source_row.get("mapped") is True,
            "source_backed": source_backed,
            "statistical_sources": statistical_sources,
            "statistical_source_count": len(statistical_sources),
            "statistical_sources_present": statistical_sources_present,
            "statistically_backed": bool(statistical_sources) and statistical_sources_present,
            "claim_lanes": claim_lanes,
            "claim_lane_count": len(claim_lanes),
            "claim_lanes_valid": bool(claim_lanes) and set(claim_lanes).issubset(ALLOWED_CLAIM_LANES),
            "section_bindings": section_bindings,
            "section_bound": section_bound,
            "visual_role": spec.visual_role,
            "visual_role_ok": visual_role_ok,
            "evidence_role": spec.evidence_role,
            "evidence_role_ok": evidence_role_ok,
            "paper_claim": spec.paper_claim,
            "paper_claim_word_count": paper_claim_word_count,
            "paper_claim_ok": paper_claim_ok,
            "hash_present": bool(hash_row.get("sha256")),
            "style_contract_ok": style_contract["ok"],
            "accessibility_text_ok": accessibility_ok,
            "alt_word_count": alt_word_count,
            "caption_word_count": caption_word_count,
            "width_fraction": spec.width,
            "rendered": rendered,
            **metrics,
        }
        row["quality_ok"] = (
            row["source_mapped"]
            and row["hash_present"]
            and row["accessibility_text_ok"]
            and row["rendered"]
            and row["visual_role_ok"]
            and row["evidence_role_ok"]
            and row["paper_claim_ok"]
            and row["section_bound"]
            and row["claim_lanes_valid"]
            and row["style_contract_ok"]
        )
        row["complete"] = row["quality_ok"]
        rows.append(row)
    return rows


def build_visualization_quality_audit(project_root: Path) -> dict[str, Any]:
    """Build figure accessibility, source, hash, and render-readiness rows."""
    root = project_root.resolve()
    rows = _figure_evidence_rows(root)
    style_contract = build_style_contract(root)
    auxiliary_inventory = build_auxiliary_visualization_inventory(root)
    return {
        "schema": VISUALIZATION_AUDIT_SCHEMA,
        "rows": rows,
        "style_contract": style_contract,
        "auxiliary_visualizations": auxiliary_inventory["rows"],
        "figure_count": len(rows),
        "auxiliary_visualization_count": auxiliary_inventory["auxiliary_visualization_count"],
        "source_mapped_count": sum(1 for row in rows if row["source_mapped"]),
        "rendered_count": sum(1 for row in rows if row["rendered"]),
        "accessibility_text_count": sum(1 for row in rows if row["accessibility_text_ok"]),
        "hashed_count": sum(1 for row in rows if row["hash_present"]),
        "source_backed_count": sum(1 for row in rows if row["source_backed"]),
        "section_bound_count": sum(1 for row in rows if row["section_bound"]),
        "statistically_backed_count": sum(1 for row in rows if row["statistically_backed"]),
        "statistical_source_count": sum(int(row["statistical_source_count"]) for row in rows),
        "statistical_figure_ids": [row["figure_id"] for row in rows if row["statistically_backed"]],
        "claim_lane_coverage": {
            lane: sum(1 for row in rows if lane in set(row.get("claim_lanes") or [])) for lane in ALLOWED_CLAIM_LANES
        },
        "all_sources_mapped": bool(rows) and all(row["source_mapped"] for row in rows),
        "all_sources_backed": bool(rows) and all(row["source_backed"] for row in rows),
        "all_rendered": bool(rows) and all(row["rendered"] for row in rows),
        "all_accessibility_text_ok": bool(rows) and all(row["accessibility_text_ok"] for row in rows),
        "all_hashes_present": bool(rows) and all(row["hash_present"] for row in rows),
        "all_visual_roles_present": bool(rows) and all(row["visual_role_ok"] for row in rows),
        "all_evidence_roles_present": bool(rows) and all(row["evidence_role_ok"] for row in rows),
        "all_paper_claims_present": bool(rows) and all(row["paper_claim_ok"] for row in rows),
        "all_figures_section_bound": bool(rows) and all(row["section_bound"] for row in rows),
        "all_figures_have_claim_lanes": bool(rows) and all(row["claim_lanes"] for row in rows),
        "all_claim_lanes_valid": bool(rows) and all(row["claim_lanes_valid"] for row in rows),
        "all_style_tokens_ok": style_contract["ok"],
        "all_auxiliary_outputs_classified": auxiliary_inventory["all_auxiliary_outputs_classified"],
        "all_auxiliary_outputs_rendered": auxiliary_inventory["all_auxiliary_outputs_rendered"],
        "all_statistical_sources_present": any(row["statistically_backed"] for row in rows)
        and all(row["statistical_sources_present"] for row in rows if row["statistical_sources"]),
        "all_figures_complete": bool(rows) and all(row["complete"] for row in rows),
        "all_quality_ok": bool(rows) and all(row["quality_ok"] for row in rows),
    }


def write_visualization_quality_audit(project_root: Path) -> Path:
    """Write the deterministic visualization-quality audit report."""
    root = project_root.resolve()
    return Path(
        _write_json(
            root / "output" / "reports" / "visualization_quality_audit.json",
            build_visualization_quality_audit(root),
        )
    )


def build_statistical_visualization_bridge(project_root: Path) -> dict[str, Any]:
    """Build the crosswalk from statistical figure rows to scholarship and sheaf bindings."""
    root = project_root.resolve()
    visualization = _load_json(root / "output" / "reports" / "visualization_quality_audit.json")
    if not visualization:
        visualization = build_visualization_quality_audit(root)

    from manuscript.sheaf.registry import load_track_registry
    from roadmap_tracks.scholarship import build_scholarship_source_matrix

    registered_tracks = set(load_track_registry(root / "manuscript" / "sheaf" / "tracks.yaml").tracks)
    scholarship = build_scholarship_source_matrix(root)
    scholarship_rows = [
        row
        for row in scholarship.get("rows") or []
        if row.get("artifact") == "output/reports/visualization_quality_audit.json"
        and row.get("method_role") in {"statistical_visualization_bridge", "visualization_quality_audit"}
    ]
    scholarship_tracks = sorted({track for row in scholarship_rows for track in row.get("tracks") or []})
    scholarship_method_roles = sorted(
        {str(row.get("method_role")) for row in scholarship_rows if row.get("method_role")}
    )
    manuscript_sections = sorted(
        {section for row in scholarship_rows for section in row.get("manuscript_sections") or []}
    )
    scholarship_connected = bool(scholarship_rows) and all(row.get("connected") for row in scholarship_rows)
    tracks_registered = bool(scholarship_tracks) and set(scholarship_tracks).issubset(registered_tracks)
    section_tracks = _manifest_section_tracks(root)
    imrad_files = _imrad_section_files(root)
    rows: list[dict[str, Any]] = []
    for row in visualization.get("rows") or []:
        if not row.get("statistically_backed"):
            continue
        figure_reference_sections = _figure_reference_sections(root, str(row.get("figure_id", "")), files=imrad_files)
        referenced_in_manuscript = bool(figure_reference_sections)
        reference_track_bindings = {section: section_tracks.get(section, []) for section in figure_reference_sections}
        reference_sections_sheaf_bound = bool(figure_reference_sections) and all(
            reference_track_bindings.get(section) for section in figure_reference_sections
        )
        reference_sections_visualization_bound = reference_sections_sheaf_bound and all(
            "visualization" in set(reference_track_bindings.get(section, [])) for section in figure_reference_sections
        )
        statistical_sources = [str(source) for source in row.get("statistical_sources") or []]
        statistical_sources_present = bool(statistical_sources) and all(
            (root / source).exists() for source in statistical_sources
        )
        connected = (
            row.get("quality_ok") is True
            and row.get("statistically_backed") is True
            and statistical_sources_present
            and scholarship_connected
            and tracks_registered
            and referenced_in_manuscript
            and reference_sections_sheaf_bound
            and reference_sections_visualization_bound
            and bool(manuscript_sections)
        )
        rows.append(
            {
                "figure_id": row.get("figure_id", ""),
                "figure_path": row.get("path", ""),
                "visualization_audit": "output/reports/visualization_quality_audit.json",
                "statistical_sources": statistical_sources,
                "statistical_source_count": len(statistical_sources),
                "statistical_sources_present": statistical_sources_present,
                "scholarship_method_roles": scholarship_method_roles,
                "scholarship_rows_connected": scholarship_connected,
                "sheaf_tracks": scholarship_tracks,
                "sheaf_tracks_registered": tracks_registered,
                "manuscript_sections": manuscript_sections,
                "figure_reference_sections": figure_reference_sections,
                "reference_track_bindings": reference_track_bindings,
                "reference_sections_sheaf_bound": reference_sections_sheaf_bound,
                "reference_sections_visualization_bound": reference_sections_visualization_bound,
                "referenced_in_manuscript": referenced_in_manuscript,
                "connected": connected,
                "complete": connected,
            }
        )
    return {
        "schema": STATISTICAL_VISUALIZATION_BRIDGE_SCHEMA,
        "rows": rows,
        "row_count": len(rows),
        "statistical_source_count": sum(int(row["statistical_source_count"]) for row in rows),
        "scholarship_method_roles": scholarship_method_roles,
        "sheaf_tracks": scholarship_tracks,
        "manuscript_sections": manuscript_sections,
        "all_rows_connected": bool(rows) and all(row["connected"] for row in rows),
        "all_rows_complete": bool(rows) and all(row["complete"] for row in rows),
        "all_complete": bool(rows) and all(row["complete"] for row in rows),
        "all_figures_referenced": bool(rows) and all(row["referenced_in_manuscript"] for row in rows),
        "all_reference_sections_sheaf_bound": bool(rows) and all(row["reference_sections_sheaf_bound"] for row in rows),
        "all_reference_sections_visualization_bound": bool(rows)
        and all(row["reference_sections_visualization_bound"] for row in rows),
        "all_statistical_sources_present": bool(rows) and all(row["statistical_sources_present"] for row in rows),
        "all_scholarship_rows_connected": scholarship_connected,
        "all_sheaf_tracks_registered": tracks_registered,
    }


def write_statistical_visualization_bridge(project_root: Path) -> Path:
    """Write the statistical-visualization scholarship/sheaf crosswalk."""
    root = project_root.resolve()
    return Path(
        _write_json(
            root / "output" / "data" / "statistical_visualization_bridge.json",
            build_statistical_visualization_bridge(root),
        )
    )


def validate_visualization_quality_audit(project_root: Path) -> list[str]:
    """Validate the saved visualization-quality audit against its row evidence."""
    root = project_root.resolve()
    path = root / "output" / "reports" / "visualization_quality_audit.json"
    payload = _load_json(path)
    if not payload:
        return ["visualization_quality_audit.json missing"]
    from visualizations.figure_registry import load_figure_registry

    issues: list[str] = []
    rows = payload.get("rows") or []
    rows_by_id = {str(row.get("figure_id")): row for row in rows}
    registry = load_figure_registry(root)
    expected_rows_by_id = {str(row["figure_id"]): row for row in _figure_evidence_rows(root)}
    expected_style_contract = build_style_contract(root)
    expected_auxiliary_inventory = build_auxiliary_visualization_inventory(root)
    source_map = _load_json(root / "output" / "data" / "figure_source_map.json")
    source_rows = {str(row.get("figure_id")): row for row in source_map.get("rows") or []}
    hash_manifest = _load_json(root / "output" / "reports" / "figure_hash_manifest.json")
    hash_rows = {str(row.get("path")): row for row in hash_manifest.get("rows") or []}
    section_bindings = _figure_section_bindings(root)
    visual_roles_present = bool(rows) and all(row.get("visual_role_ok") for row in rows)
    evidence_roles_present = bool(rows) and all(row.get("evidence_role_ok") for row in rows)
    paper_claims_present = bool(rows) and all(row.get("paper_claim_ok") for row in rows)
    figures_section_bound = bool(rows) and all(row.get("section_bound") for row in rows)
    live_rendered: list[bool] = []
    live_sources_mapped: list[bool] = []
    live_sources_backed: list[bool] = []
    live_section_bound: list[bool] = []
    live_hashes_present: list[bool] = []
    live_statistically_backed: list[dict[str, Any]] = []
    for figure_id, spec in sorted(registry.items()):
        row = rows_by_id.get(figure_id)
        if row is None:
            issues.append(f"visualization_quality_audit.json missing row for {figure_id}")
            continue
        expected_row = expected_rows_by_id.get(figure_id, {})
        rel_path = f"output/figures/{spec.filename}"
        metrics = _image_metrics(root / rel_path)
        rendered = (
            metrics["exists"]
            and metrics["render_size_ok"]
            and metrics["aspect_ratio_ok"]
            and metrics["nonblank"]
            and metrics["mode"] == "RGB"
        )
        live_rendered.append(rendered)
        if not rendered:
            issues.append(f"visualization_quality_audit.json live render failed or blank for {figure_id}")
        if any(row.get(key) != metrics[key] for key in ("width_px", "height_px", "mode", "nonblank")):
            issues.append(f"visualization_quality_audit.json stale live render metrics for {figure_id}")
        for key in (
            "visual_role",
            "visual_role_ok",
            "evidence_role",
            "evidence_role_ok",
            "paper_claim",
            "paper_claim_ok",
            "accessibility_text_ok",
            "quality_ok",
            "complete",
            "style_contract_ok",
            "claim_lanes",
            "claim_lane_count",
            "claim_lanes_valid",
        ):
            if expected_row and row.get(key) != expected_row.get(key):
                issues.append(f"visualization_quality_audit.json stale figure evidence for {figure_id}")
                break
        expected_source_row = source_rows.get(figure_id, {})
        expected_sources = [str(source) for source in expected_source_row.get("source_artifacts") or []]
        row_sources = [str(source) for source in row.get("sources") or []]
        source_mapped = expected_source_row.get("mapped") is True and row_sources == expected_sources
        source_backed = source_mapped and _all_sources_present(root, expected_sources)
        live_sources_mapped.append(source_mapped)
        live_sources_backed.append(source_backed)
        if row.get("source_mapped") is not source_mapped or row.get("source_backed") is not source_backed:
            issues.append(f"visualization_quality_audit.json stale source metadata for {figure_id}")
        expected_sections = section_bindings.get(figure_id, [])
        row_sections = [str(section) for section in row.get("section_bindings") or []]
        section_bound = bool(expected_sections) and row_sections == expected_sections
        live_section_bound.append(section_bound)
        if row.get("section_bound") is not section_bound:
            issues.append(f"visualization_quality_audit.json stale section binding for {figure_id}")
        hash_present = bool(hash_rows.get(rel_path, {}).get("sha256"))
        live_hashes_present.append(hash_present)
        if row.get("hash_present") is not hash_present:
            issues.append(f"visualization_quality_audit.json stale hash metadata for {figure_id}")
        statistical_sources, statistical_sources_present = _statistical_sources(root, expected_sources)
        if statistical_sources and statistical_sources_present:
            live_statistically_backed.append({"figure_id": figure_id, "statistical_sources_present": True})
    if payload.get("schema") != VISUALIZATION_AUDIT_SCHEMA:
        issues.append("visualization_quality_audit.json schema mismatch")
    figures_complete = bool(rows) and all(row.get("complete") is True and row.get("quality_ok") is True for row in rows)
    if payload.get("all_figures_complete") is not True or payload.get("all_figures_complete") != figures_complete:
        issues.append("visualization_quality_audit.json has incomplete figure rows")
    if payload.get("all_quality_ok") is not True or payload.get("all_quality_ok") != (
        bool(rows) and all(row.get("quality_ok") for row in rows)
    ):
        issues.append("visualization_quality_audit.json records low-quality figure rows")
    if payload.get("all_sources_mapped") is not True:
        issues.append("visualization_quality_audit.json has unmapped figure sources")
    if payload.get("all_rendered") is not True:
        issues.append("visualization_quality_audit.json has unrendered figures")
    if live_rendered and (payload.get("all_rendered") != all(live_rendered) or not all(live_rendered)):
        issues.append("visualization_quality_audit.json live render evidence disagrees with summary")
    if payload.get("all_accessibility_text_ok") is not True:
        issues.append("visualization_quality_audit.json has insufficient alt text or captions")
    if payload.get("all_hashes_present") is not True:
        issues.append("visualization_quality_audit.json lacks figure hashes")
    if live_hashes_present and payload.get("all_hashes_present") != all(live_hashes_present):
        issues.append("visualization_quality_audit.json live hash evidence disagrees with summary")
    if live_sources_mapped and payload.get("all_sources_mapped") != all(live_sources_mapped):
        issues.append("visualization_quality_audit.json source metadata disagrees with source map")
    if live_sources_backed and payload.get("all_sources_backed") != all(live_sources_backed):
        issues.append("visualization_quality_audit.json source backing disagrees with source map")
    if live_section_bound and payload.get("all_figures_section_bound") != all(live_section_bound):
        issues.append("visualization_quality_audit.json section binding evidence disagrees with registry")
    if (
        payload.get("all_visual_roles_present") is not True
        or payload.get("all_visual_roles_present") != visual_roles_present
        or payload.get("all_evidence_roles_present") is not True
        or payload.get("all_evidence_roles_present") != evidence_roles_present
        or payload.get("all_paper_claims_present") is not True
        or payload.get("all_paper_claims_present") != paper_claims_present
        or payload.get("all_figures_section_bound") is not True
        or payload.get("all_figures_section_bound") != figures_section_bound
    ):
        issues.append("visualization_quality_audit.json has incomplete figure intent metadata")
    claim_lanes_valid = bool(rows) and all(
        row.get("claim_lanes_valid") is True
        and bool(row.get("claim_lanes"))
        and set(str(lane) for lane in row.get("claim_lanes") or []).issubset(ALLOWED_CLAIM_LANES)
        for row in rows
    )
    if (
        payload.get("all_figures_have_claim_lanes") is not True
        or payload.get("all_claim_lanes_valid") is not True
        or payload.get("all_claim_lanes_valid") != claim_lanes_valid
    ):
        issues.append("visualization_quality_audit.json has incomplete claim-lane coverage")
    statistically_backed = [row for row in rows if row.get("statistically_backed")]
    statistical_sources_present = bool(statistically_backed) and all(
        row.get("statistical_sources_present") for row in statistically_backed
    )
    if (
        payload.get("statistically_backed_count") != len(statistically_backed)
        or payload.get("statistically_backed_count") != len(live_statistically_backed)
        or payload.get("all_statistical_sources_present") is not True
        or payload.get("all_statistical_sources_present") != statistical_sources_present
    ):
        issues.append("visualization_quality_audit.json has unsupported statistical figure sources")
    if (
        payload.get("style_contract") != expected_style_contract
        or payload.get("all_style_tokens_ok") is not True
        or payload.get("all_style_tokens_ok") != expected_style_contract["ok"]
    ):
        issues.append("visualization_quality_audit.json has stale or weak style-token evidence")
    auxiliary_rows = payload.get("auxiliary_visualizations") or []
    if (
        auxiliary_rows != expected_auxiliary_inventory["rows"]
        or payload.get("auxiliary_visualization_count") != expected_auxiliary_inventory["auxiliary_visualization_count"]
        or payload.get("all_auxiliary_outputs_classified")
        != expected_auxiliary_inventory["all_auxiliary_outputs_classified"]
        or payload.get("all_auxiliary_outputs_rendered")
        != expected_auxiliary_inventory["all_auxiliary_outputs_rendered"]
        or payload.get("all_auxiliary_outputs_classified") is not True
        or payload.get("all_auxiliary_outputs_rendered") is not True
    ):
        issues.append("visualization_quality_audit.json has stale or unclassified auxiliary visualizations")
    return issues


def validate_statistical_visualization_bridge(project_root: Path) -> list[str]:
    """Validate the saved statistical visualization crosswalk against row evidence."""
    root = project_root.resolve()
    path = root / "output" / "data" / "statistical_visualization_bridge.json"
    payload = _load_json(path)
    if not payload:
        return ["statistical_visualization_bridge.json missing"]
    issues: list[str] = []
    rows = payload.get("rows") or []
    rows_connected = bool(rows) and all(row.get("connected") for row in rows)
    rows_complete = bool(rows) and all(row.get("complete") is True and row.get("connected") is True for row in rows)
    sources_present = bool(rows) and all(row.get("statistical_sources_present") for row in rows)
    figures_referenced = bool(rows) and all(row.get("referenced_in_manuscript") for row in rows)
    reference_section_status = [_reference_section_status(row) for row in rows]
    reference_sections_sheaf_bound = bool(rows) and all(
        row.get("reference_sections_sheaf_bound") is True and status[0]
        for row, status in zip(rows, reference_section_status, strict=True)
    )
    reference_sections_visualization_bound = bool(rows) and all(
        row.get("reference_sections_visualization_bound") is True and status[1]
        for row, status in zip(rows, reference_section_status, strict=True)
    )
    tracks_registered = bool(rows) and all(row.get("sheaf_tracks_registered") for row in rows)
    if payload.get("schema") != STATISTICAL_VISUALIZATION_BRIDGE_SCHEMA:
        issues.append("statistical_visualization_bridge.json schema mismatch")
    if payload.get("row_count") != len(rows):
        issues.append("statistical_visualization_bridge.json row_count mismatch")
    if payload.get("all_rows_connected") is not True or payload.get("all_rows_connected") != rows_connected:
        issues.append("statistical_visualization_bridge.json has disconnected rows")
    if (
        payload.get("all_rows_complete") is not True
        or payload.get("all_complete") is not True
        or payload.get("all_rows_complete") != rows_complete
        or payload.get("all_complete") != rows_complete
    ):
        issues.append("statistical_visualization_bridge.json has incomplete rows")
    if payload.get("all_figures_referenced") is not True or payload.get("all_figures_referenced") != figures_referenced:
        issues.append("statistical_visualization_bridge.json has unreferenced figure rows")
    if (
        payload.get("all_reference_sections_sheaf_bound") is not True
        or payload.get("all_reference_sections_sheaf_bound") != reference_sections_sheaf_bound
        or payload.get("all_reference_sections_visualization_bound") is not True
        or payload.get("all_reference_sections_visualization_bound") != reference_sections_visualization_bound
    ):
        issues.append("statistical_visualization_bridge.json has unbound figure reference sections")
    if (
        payload.get("all_statistical_sources_present") is not True
        or payload.get("all_statistical_sources_present") != sources_present
    ):
        issues.append("statistical_visualization_bridge.json has missing statistical sources")
    if payload.get("all_sheaf_tracks_registered") is not True or not tracks_registered:
        issues.append("statistical_visualization_bridge.json has unregistered sheaf tracks")
    if "statistical_visualization_bridge" not in set(payload.get("scholarship_method_roles") or []):
        issues.append("statistical_visualization_bridge.json lacks scholarship bridge role")
    return issues
