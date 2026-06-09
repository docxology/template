"""Deterministic visualization-quality audit for generated figure artifacts."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml

VISUALIZATION_AUDIT_SCHEMA = "template_active_inference.visualization_quality_audit.v1"
STATISTICAL_VISUALIZATION_BRIDGE_SCHEMA = "template_active_inference.statistical_visualization_bridge.v1"
MIN_RENDER_WIDTH = 400
MIN_RENDER_HEIGHT = 200
MIN_RENDER_BYTES = 5_000
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


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)?", text))


def _image_metrics(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"exists": False, "width_px": 0, "height_px": 0, "mode": "", "size_bytes": 0}
    try:
        from PIL import Image

        with Image.open(path) as image:
            width, height = image.size
            mode = image.mode
    except (ImportError, OSError, ValueError, EOFError):
        width, height, mode = 0, 0, ""
    return {
        "exists": path.is_file(),
        "width_px": int(width),
        "height_px": int(height),
        "mode": mode,
        "size_bytes": path.stat().st_size if path.is_file() else 0,
    }


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


def _figure_reference_sections(root: Path, figure_id: str) -> list[str]:
    paths = sorted((root / "manuscript" / "sections" / "imrad").glob("**/*.md")) + sorted(
        path
        for path in (root / "manuscript").glob("*.md")
        if path.name not in {"AGENTS.md", "README.md", "SYNTAX.md", "preamble.md"}
    )
    needles = (f"@fig:{figure_id}", f"#fig:{figure_id}")
    sections = {
        _section_id_from_path(root, path)
        for path in paths
        if path.is_file() and any(needle in path.read_text(encoding="utf-8") for needle in needles)
    }
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


def build_visualization_quality_audit(project_root: Path) -> dict[str, Any]:
    """Build figure accessibility, source, hash, and render-readiness rows."""
    root = project_root.resolve()
    from visualizations.figure_registry import load_figure_registry

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
            and metrics["width_px"] >= MIN_RENDER_WIDTH
            and metrics["height_px"] >= MIN_RENDER_HEIGHT
            and metrics["size_bytes"] >= MIN_RENDER_BYTES
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
        )
        rows.append(row)
    return {
        "schema": VISUALIZATION_AUDIT_SCHEMA,
        "rows": rows,
        "figure_count": len(rows),
        "source_mapped_count": sum(1 for row in rows if row["source_mapped"]),
        "rendered_count": sum(1 for row in rows if row["rendered"]),
        "accessibility_text_count": sum(1 for row in rows if row["accessibility_text_ok"]),
        "hashed_count": sum(1 for row in rows if row["hash_present"]),
        "source_backed_count": sum(1 for row in rows if row["source_backed"]),
        "section_bound_count": sum(1 for row in rows if row["section_bound"]),
        "statistically_backed_count": sum(1 for row in rows if row["statistically_backed"]),
        "statistical_source_count": sum(int(row["statistical_source_count"]) for row in rows),
        "statistical_figure_ids": [row["figure_id"] for row in rows if row["statistically_backed"]],
        "all_sources_mapped": bool(rows) and all(row["source_mapped"] for row in rows),
        "all_sources_backed": bool(rows) and all(row["source_backed"] for row in rows),
        "all_rendered": bool(rows) and all(row["rendered"] for row in rows),
        "all_accessibility_text_ok": bool(rows) and all(row["accessibility_text_ok"] for row in rows),
        "all_hashes_present": bool(rows) and all(row["hash_present"] for row in rows),
        "all_visual_roles_present": bool(rows) and all(row["visual_role_ok"] for row in rows),
        "all_evidence_roles_present": bool(rows) and all(row["evidence_role_ok"] for row in rows),
        "all_paper_claims_present": bool(rows) and all(row["paper_claim_ok"] for row in rows),
        "all_figures_section_bound": bool(rows) and all(row["section_bound"] for row in rows),
        "all_statistical_sources_present": any(row["statistically_backed"] for row in rows)
        and all(row["statistical_sources_present"] for row in rows if row["statistical_sources"]),
        "all_quality_ok": bool(rows) and all(row["quality_ok"] for row in rows),
    }


def write_visualization_quality_audit(project_root: Path) -> Path:
    """Write the deterministic visualization-quality audit report."""
    root = project_root.resolve()
    return _write_json(
        root / "output" / "reports" / "visualization_quality_audit.json",
        build_visualization_quality_audit(root),
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
    rows: list[dict[str, Any]] = []
    for row in visualization.get("rows") or []:
        if not row.get("statistically_backed"):
            continue
        figure_reference_sections = _figure_reference_sections(root, str(row.get("figure_id", "")))
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
    return _write_json(
        root / "output" / "data" / "statistical_visualization_bridge.json",
        build_statistical_visualization_bridge(root),
    )


def validate_visualization_quality_audit(project_root: Path) -> list[str]:
    """Validate the saved visualization-quality audit against its row evidence."""
    root = project_root.resolve()
    path = root / "output" / "reports" / "visualization_quality_audit.json"
    payload = _load_json(path)
    if not payload:
        return ["visualization_quality_audit.json missing"]
    issues: list[str] = []
    rows = payload.get("rows") or []
    visual_roles_present = bool(rows) and all(row.get("visual_role_ok") for row in rows)
    evidence_roles_present = bool(rows) and all(row.get("evidence_role_ok") for row in rows)
    paper_claims_present = bool(rows) and all(row.get("paper_claim_ok") for row in rows)
    figures_section_bound = bool(rows) and all(row.get("section_bound") for row in rows)
    if payload.get("schema") != VISUALIZATION_AUDIT_SCHEMA:
        issues.append("visualization_quality_audit.json schema mismatch")
    if payload.get("all_quality_ok") is not True or not (bool(rows) and all(row.get("quality_ok") for row in rows)):
        issues.append("visualization_quality_audit.json records low-quality figure rows")
    if payload.get("all_sources_mapped") is not True:
        issues.append("visualization_quality_audit.json has unmapped figure sources")
    if payload.get("all_rendered") is not True:
        issues.append("visualization_quality_audit.json has unrendered figures")
    if payload.get("all_accessibility_text_ok") is not True:
        issues.append("visualization_quality_audit.json has insufficient alt text or captions")
    if payload.get("all_hashes_present") is not True:
        issues.append("visualization_quality_audit.json lacks figure hashes")
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
    statistically_backed = [row for row in rows if row.get("statistically_backed")]
    statistical_sources_present = bool(statistically_backed) and all(
        row.get("statistical_sources_present") for row in statistically_backed
    )
    if (
        payload.get("statistically_backed_count") != len(statistically_backed)
        or payload.get("all_statistical_sources_present") is not True
        or payload.get("all_statistical_sources_present") != statistical_sources_present
    ):
        issues.append("visualization_quality_audit.json has unsupported statistical figure sources")
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
