"""Source-backed scholarship matrix for the active-inference exemplar."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml

SCHOLARSHIP_SCHEMA = "template_active_inference.scholarship_source_matrix.v1"

EXPECTED_SCHOLARSHIP_KEYS: tuple[str, ...] = (
    "friston2010fep",
    "buckley2017mathreview",
    "dacosta2020discrete",
    "parr2022active",
    "smith2022tutorial",
    "pymdp2024",
    "gnn2023",
    "curry2014sheaves",
    "robinson2014topological",
)

SCHOLARSHIP_SOURCES: tuple[dict[str, Any], ...] = (
    {
        "citation_key": "friston2010fep",
        "source_kind": "primary_article",
        "source_family": "free_energy_principle",
        "method_role": "scope_background",
        "tracks": ["prose", "formalism", "scholarship"],
        "artifact": "output/data/scholarship_source_matrix.json",
        "manuscript_sections": ["intro_motivation", "methods_sheaf"],
        "claim_boundary": "background only; no empirical biological claim is inferred",
    },
    {
        "citation_key": "buckley2017mathreview",
        "source_kind": "mathematical_review",
        "source_family": "free_energy_principle",
        "method_role": "mathematical_review",
        "tracks": ["formalism", "scholarship"],
        "artifact": "output/data/analytical_assumption_index.json",
        "manuscript_sections": ["methods_analytical", "appendix_full_sheaf"],
        "claim_boundary": "supports finite variational-free-energy notation only",
    },
    {
        "citation_key": "buckley2017mathreview",
        "source_kind": "mathematical_review",
        "source_family": "free_energy_principle",
        "method_role": "statistics_boundary",
        "tracks": ["simulation", "uncertainty", "scholarship"],
        "artifact": "output/data/analysis_statistics.json",
        "manuscript_sections": ["results_si_tmaze", "results_invariants"],
        "claim_boundary": "supports reporting deterministic toy statistics, not inferential population statistics",
    },
    {
        "citation_key": "dacosta2020discrete",
        "source_kind": "primary_article",
        "source_family": "discrete_state_space_active_inference",
        "method_role": "discrete_planning_formalism",
        "tracks": ["pymdp", "model_checking", "scholarship"],
        "artifact": "output/reports/model_checking_witnesses.json",
        "manuscript_sections": ["methods_pymdp", "methods_lean"],
        "claim_boundary": "finite toy state spaces only",
    },
    {
        "citation_key": "parr2022active",
        "source_kind": "monograph",
        "source_family": "active_inference",
        "method_role": "conceptual_reference",
        "tracks": ["prose", "uncertainty", "scholarship"],
        "artifact": "output/data/uncertainty_summary.json",
        "manuscript_sections": ["intro_motivation", "results_invariants"],
        "claim_boundary": "conceptual context, not evidence for toy metrics",
    },
    {
        "citation_key": "smith2022tutorial",
        "source_kind": "tutorial_article",
        "source_family": "active_inference_practice",
        "method_role": "model_building_tutorial",
        "tracks": ["pymdp", "scholarship"],
        "artifact": "output/data/si_policy_grid.json",
        "manuscript_sections": ["methods_pymdp", "results_si_tmaze"],
        "claim_boundary": "empirical fitting is out of scope until an adapter is promoted",
    },
    {
        "citation_key": "smith2022tutorial",
        "source_kind": "tutorial_article",
        "source_family": "active_inference_practice",
        "method_role": "empirical_scope_boundary",
        "tracks": ["adversarial_audit", "scholarship"],
        "artifact": "output/reports/blocked_scope_manifest.json",
        "manuscript_sections": ["discussion_outlook", "appendix_full_sheaf"],
        "claim_boundary": "keeps empirical-data tutorial relevance separate from this public toy-only exemplar",
    },
    {
        "citation_key": "pymdp2024",
        "source_kind": "primary_repository",
        "source_family": "pymdp_implementation",
        "method_role": "implementation_anchor",
        "tracks": ["pymdp", "interop", "scholarship"],
        "artifact": "output/reports/pymdp_runtime_diagnostics.json",
        "manuscript_sections": ["methods_pymdp", "appendix_full_sheaf"],
        "claim_boundary": "runtime construction and diagnostics only",
    },
    {
        "citation_key": "gnn2023",
        "source_kind": "primary_preprint",
        "source_family": "generalized_notation_notation",
        "method_role": "notation_anchor",
        "tracks": ["gnn", "ontology", "interop", "scholarship"],
        "artifact": "output/data/interop_roundtrip_report.json",
        "manuscript_sections": ["methods_analytical", "methods_pymdp", "appendix_full_sheaf"],
        "claim_boundary": "notation and round-trip contract only",
    },
    {
        "citation_key": "curry2014sheaves",
        "source_kind": "dissertation",
        "source_family": "cellular_sheaves",
        "method_role": "sheaf_gluing_background",
        "tracks": ["prose", "formalism", "scholarship"],
        "artifact": "output/data/sheaf_gluing_certificate.json",
        "manuscript_sections": ["methods_sheaf", "appendix_full_sheaf"],
        "claim_boundary": "finite manuscript-stalk analogy, not full sheaf cohomology",
    },
    {
        "citation_key": "curry2014sheaves",
        "source_kind": "dissertation",
        "source_family": "cellular_sheaves",
        "method_role": "finite_sheaf_law_boundary",
        "tracks": ["formalism", "scholarship"],
        "artifact": "output/data/sheaf_section_status_matrix.json",
        "manuscript_sections": ["methods_sheaf", "appendix_full_sheaf"],
        "claim_boundary": "supports finite sheaf-law phrasing over the manuscript base poset only",
    },
    {
        "citation_key": "robinson2014topological",
        "source_kind": "monograph",
        "source_family": "applied_sheaf_signal_processing",
        "method_role": "local_to_global_consistency",
        "tracks": ["visualization", "prose", "scholarship"],
        "artifact": "output/data/sheaf_coverage_matrix.json",
        "manuscript_sections": ["methods_sheaf", "appendix_full_sheaf"],
        "claim_boundary": "applied local/global consistency analogy only",
    },
    {
        "citation_key": "robinson2014topological",
        "source_kind": "monograph",
        "source_family": "applied_sheaf_signal_processing",
        "method_role": "visualization_quality_audit",
        "tracks": ["visualization", "scholarship"],
        "artifact": "output/reports/visualization_quality_audit.json",
        "manuscript_sections": ["methods_sheaf", "appendix_full_sheaf"],
        "claim_boundary": "supports visual local-to-global diagnostics, not empirical truth of the toy figures",
    },
    {
        "citation_key": "buckley2017mathreview",
        "source_kind": "mathematical_review",
        "source_family": "free_energy_principle",
        "method_role": "statistical_visualization_bridge",
        "tracks": ["simulation", "visualization", "scholarship"],
        "artifact": "output/reports/visualization_quality_audit.json",
        "manuscript_sections": ["methods_sheaf", "results_si_tmaze", "appendix_full_sheaf"],
        "claim_boundary": "connects deterministic toy statistics to figure provenance without claiming population inference",
    },
)


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _bib_entries(root: Path) -> dict[str, str]:
    path = root / "manuscript" / "references.bib"
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(r"@\w+\s*\{\s*([^,\s]+)\s*,(.*?)(?=\n@\w+\s*\{|\Z)", re.S)
    return {match.group(1).strip(): match.group(2) for match in pattern.finditer(text)}


def _citation_present(root: Path, key: str) -> bool:
    paths = sorted((root / "manuscript" / "sections").glob("**/*.md")) + sorted(
        path
        for path in (root / "manuscript").glob("*.md")
        if path.name not in {"99_references.md", "SYNTAX.md", "README.md", "AGENTS.md"}
    )
    needle = f"@{key}"
    return any(needle in path.read_text(encoding="utf-8") for path in paths if path.is_file())


def _registry_tracks(root: Path) -> set[str]:
    tracks = (_load_yaml(root / "manuscript" / "sheaf" / "tracks.yaml").get("tracks") or {}).keys()
    return {str(track) for track in tracks}


def _manifest_sections(root: Path) -> set[str]:
    sections = _load_yaml(root / "manuscript" / "sheaf" / "manifest.yaml").get("sections") or []
    return {str(section.get("id")) for section in sections if isinstance(section, dict) and section.get("id")}


def _has_locator(entry: str) -> bool:
    lower = entry.lower()
    return "doi" in lower or "url" in lower or "https://" in lower or "http://" in lower


def build_scholarship_source_matrix(project_root: Path) -> dict[str, Any]:
    """Build the literature-to-method traceability matrix."""
    root = project_root.resolve()
    bib_entries = _bib_entries(root)
    registry = _registry_tracks(root)
    sections = _manifest_sections(root)
    rows: list[dict[str, Any]] = []
    for source in SCHOLARSHIP_SOURCES:
        key = str(source["citation_key"])
        entry = bib_entries.get(key, "")
        artifact = str(source["artifact"])
        track_ids = [str(track) for track in source["tracks"]]
        section_ids = [str(section) for section in source["manuscript_sections"]]
        row = {
            **source,
            "bib_has_entry": bool(entry),
            "bib_has_locator": bool(entry and _has_locator(entry)),
            "cited_in_manuscript": _citation_present(root, key),
            "artifact_exists": artifact == "output/data/scholarship_source_matrix.json" or (root / artifact).is_file(),
            "tracks_registered": set(track_ids).issubset(registry),
            "sections_bound": set(section_ids).issubset(sections),
        }
        row["connected"] = all(
            bool(row[field])
            for field in (
                "bib_has_entry",
                "bib_has_locator",
                "cited_in_manuscript",
                "artifact_exists",
                "tracks_registered",
                "sections_bound",
            )
        ) and bool(row["claim_boundary"])
        rows.append(row)
    expected = set(EXPECTED_SCHOLARSHIP_KEYS)
    observed = {str(row["citation_key"]) for row in rows}
    return {
        "schema": SCHOLARSHIP_SCHEMA,
        "rows": rows,
        "source_count": len(rows),
        "expected_sources": sorted(expected),
        "observed_sources": sorted(observed),
        "method_role_count": len({str(row["method_role"]) for row in rows}),
        "source_family_count": len({str(row["source_family"]) for row in rows}),
        "primary_source_count": sum(
            1 for row in rows if row["source_kind"] in {"primary_article", "primary_repository", "primary_preprint"}
        ),
        "quantitative_method_role_count": sum(
            1
            for row in rows
            if str(row["method_role"]) in {"statistics_boundary", "visualization_quality_audit"}
            or str(row["method_role"]) == "statistical_visualization_bridge"
        ),
        "all_expected_sources_present": observed == expected,
        "all_sources_connected": bool(rows) and all(row["connected"] for row in rows),
    }


def write_scholarship_source_matrix(project_root: Path) -> Path:
    """Write the source-backed scholarship matrix."""
    root = project_root.resolve()
    return _write_json(
        root / "output" / "data" / "scholarship_source_matrix.json", build_scholarship_source_matrix(root)
    )


def validate_scholarship_source_matrix(project_root: Path) -> list[str]:
    """Validate the saved scholarship-source matrix against its row evidence."""
    root = project_root.resolve()
    payload_path = root / "output" / "data" / "scholarship_source_matrix.json"
    issues: list[str] = []
    if not payload_path.is_file():
        return ["scholarship_source_matrix.json missing"]
    try:
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return ["scholarship_source_matrix.json is not valid JSON"]
    rows = payload.get("rows") or []
    observed = {str(row.get("citation_key")) for row in rows}
    expected = set(EXPECTED_SCHOLARSHIP_KEYS)
    if payload.get("schema") != SCHOLARSHIP_SCHEMA:
        issues.append("scholarship_source_matrix.json schema mismatch")
    if observed != expected or payload.get("all_expected_sources_present") is not True:
        issues.append("scholarship_source_matrix.json source set is incomplete")
    connected = bool(rows) and all(
        row.get("bib_has_entry")
        and row.get("bib_has_locator")
        and row.get("cited_in_manuscript")
        and row.get("artifact_exists")
        and row.get("tracks_registered")
        and row.get("sections_bound")
        and row.get("claim_boundary")
        and row.get("connected")
        for row in rows
    )
    if payload.get("all_sources_connected") is not True or payload.get("all_sources_connected") != connected:
        issues.append("scholarship_source_matrix.json has disconnected source rows")
    if int(payload.get("method_role_count", 0) or 0) < 6:
        issues.append("scholarship_source_matrix.json has too few method roles")
    if int(payload.get("quantitative_method_role_count", 0) or 0) < 3:
        issues.append("scholarship_source_matrix.json lacks quantitative or visualization method roles")
    return issues
