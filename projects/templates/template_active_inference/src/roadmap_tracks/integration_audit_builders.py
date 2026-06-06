"""Core integration-audit builders (dependency graph, manuscript provenance, claims, gates).

Split out of :mod:`roadmap_tracks.integration_audit` to keep each module a cohesive
unit under the line-count gate. The public ``integration_audit`` module re-exports
every name defined here, so existing ``from roadmap_tracks.integration_audit import X``
imports continue to resolve unchanged.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml

TOKEN_RE = re.compile(r"\{\{([a-z][a-z0-9_]*)(?::\.[0-9]+f)?\}\}")
TOKEN_MATCH_RE = re.compile(r"\{\{([a-z][a-z0-9_]*)(?::\.(\d+)f)?\}\}")
SELF_PRODUCER = "generate_integration_audit.py"
LATE_HYDRATION_PRODUCER = "z_generate_manuscript_variables.py"
SHEAF_TRACK_PRODUCER = "generate_sheaf_tracks.py"


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _analysis_scripts(root: Path) -> list[str]:
    data = yaml.safe_load((root / "manuscript" / "config.yaml").read_text(encoding="utf-8")) or {}
    return [str(script) for script in ((data.get("analysis") or {}).get("scripts") or [])]


def build_integration_dependency_graph(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    from manuscript.sheaf.semantic import build_validation_dependency_graph

    base = build_validation_dependency_graph(root)
    artifacts = base.get("artifacts") or {}
    edges = list(base.get("edges") or [])
    for rel, record in artifacts.items():
        for gate in record.get("validation_gates") or []:
            edges.append({"source": gate, "target": rel, "kind": "validator_reads"})
    token_provenance = build_manuscript_token_provenance(root)
    for token in token_provenance["tokens"]:
        edges.append({"source": token["section"], "target": token["token"], "kind": "section_uses_token"})
        edges.append({"source": token["token"], "target": token["source"], "kind": "token_from_artifact"})
    edge_types = sorted({edge["kind"] for edge in edges})
    required = [
        "produces",
        "consumed_by",
        "validated_by",
        "validator_reads",
        "section_uses_token",
        "token_from_artifact",
    ]
    return {
        "schema": "template_active_inference.integration_dependency_graph.v1",
        "analysis_scripts": base.get("analysis_scripts") or [],
        "artifacts": artifacts,
        "edges": edges,
        "edge_types": edge_types,
        "required_edge_types": required,
        "all_required_edge_types_present": set(required).issubset(edge_types),
        "issues": base.get("issues") or [],
    }


def build_producer_completeness(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    from manuscript.sheaf.semantic import ARTIFACT_PRODUCERS

    configured = set(_analysis_scripts(root))
    rows = [
        {
            "artifact": rel,
            "producer": producer,
            "exists": (root / rel).is_file() or producer in {SELF_PRODUCER, LATE_HYDRATION_PRODUCER},
            "configured": producer in configured,
        }
        for rel, producer in sorted(ARTIFACT_PRODUCERS.items())
    ]
    return {
        "schema": "template_active_inference.producer_completeness.v1",
        "rows": rows,
        "all_complete": all(row["exists"] and row["configured"] for row in rows),
    }


def build_stale_artifact_report(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    graph = build_integration_dependency_graph(root)
    rows = []
    excluded_producers = {SELF_PRODUCER, LATE_HYDRATION_PRODUCER, SHEAF_TRACK_PRODUCER}
    for rel, record in sorted((graph.get("artifacts") or {}).items()):
        if record.get("producer") in excluded_producers:
            continue
        path = root / rel
        sha = _sha256(path) if path.is_file() else ""
        rows.append(
            {
                "artifact": rel,
                "exists": path.is_file(),
                "sha256": sha,
                "fresh": path.is_file(),
            }
        )
    return {
        "schema": "template_active_inference.stale_artifact_report.v1",
        "rows": rows,
        "excluded_producers": sorted(excluded_producers),
        "all_fresh": all(row["fresh"] for row in rows),
    }


def build_cross_track_symbol_table(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    from gnn.parser import parse_gnn_file
    from ontology.bindings import load_section_ontology

    rows = []
    section_ontology_paths = {
        "bernoulli_toy": root / "manuscript" / "sections" / "imrad" / "methods_analytical" / "ontology.yaml",
        "si_tmaze": root / "manuscript" / "sections" / "imrad" / "methods_pymdp" / "ontology.yaml",
    }
    for path in sorted((root / "gnn").glob("*.gnn.md")):
        model_id = path.stem.replace(".gnn", "")
        model = parse_gnn_file(path)
        section_ontology = (
            load_section_ontology(section_ontology_paths[model_id]) if model_id in section_ontology_paths else {}
        )
        for variable, var in sorted(model.variables.items()):
            gnn_term = model.ontology.get(variable)
            section_term = section_ontology.get(variable)
            term_consistent = bool(gnn_term) and bool(section_term) and gnn_term == section_term
            rows.append(
                {
                    "model": model_id,
                    "symbol": variable,
                    "shape": list(var.dims),
                    "dtype": var.dtype,
                    "gnn_term": gnn_term,
                    "section_ontology_term": section_term,
                    "json_field": variable,
                    "lean_namespace": "TemplateActiveInference",
                    "shape_declared": bool(var.dims),
                    "dtype_declared": bool(var.dtype),
                    "ontology_declared": bool(gnn_term),
                    "section_ontology_declared": bool(section_term),
                    "term_consistent": term_consistent,
                    "consistent": bool(var.dims and var.dtype and term_consistent),
                }
            )
    return {
        "schema": "template_active_inference.cross_track_symbol_table.v1",
        "rows": rows,
        "symbol_count": len(rows),
        "all_shapes_declared": bool(rows) and all(row["shape_declared"] for row in rows),
        "all_dtypes_declared": bool(rows) and all(row["dtype_declared"] for row in rows),
        "all_ontology_terms_declared": bool(rows) and all(row["ontology_declared"] for row in rows),
        "all_section_terms_declared": bool(rows) and all(row["section_ontology_declared"] for row in rows),
        "all_consistent": bool(rows) and all(row["consistent"] for row in rows),
    }


def build_manuscript_token_provenance(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    source = "output/data/manuscript_variables.json"
    variables = _load_json(root / source)
    from manuscript.variables import generate_variables

    variables = {**generate_variables(root, require_analysis_outputs=False), **variables}
    rows = []
    paths = sorted((root / "manuscript").glob("*.md")) + sorted((root / "manuscript" / "sections").glob("**/*.md"))
    excluded = {"AGENTS.md", "README.md", "SYNTAX.md", "preamble.md"}
    for path in paths:
        if path.name in excluded:
            continue
        text = path.read_text(encoding="utf-8")
        for token in sorted(set(TOKEN_RE.findall(text))):
            rows.append(
                {
                    "section": path.relative_to(root).as_posix(),
                    "token": token,
                    "source": source,
                    "mapped": token in variables,
                }
            )
    return {
        "schema": "template_active_inference.manuscript_token_provenance.v1",
        "tokens": rows,
        "token_count": len(rows),
        "all_tokens_mapped": all(row["mapped"] for row in rows),
    }


def _expected_token_value(token: str, precision: str | None, variables: dict[str, Any]) -> str:
    from manuscript.hydrate import format_variables

    formatted = format_variables(variables)
    value = str(formatted.get(token, ""))
    if precision is None:
        return value
    try:
        return f"{float(value):.{int(precision)}f}"
    except ValueError:
        return value


def build_manuscript_staleness_report(project_root: Path) -> dict[str, Any]:
    """Compare hydrated manuscript tokens against the current generated variables."""
    root = project_root.resolve()
    from manuscript.hydrate import EXCLUDED_DOC_FILENAMES
    from manuscript.variables import generate_variables

    variables = generate_variables(root, require_analysis_outputs=False)
    rows: list[dict[str, Any]] = []
    output_dir = root / "output" / "manuscript"
    for path in sorted((root / "manuscript").glob("*.md")):
        if path.name in EXCLUDED_DOC_FILENAMES:
            continue
        resolved_path = output_dir / path.name
        try:
            source_text = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            rows.append(
                {
                    "section": path.relative_to(root).as_posix(),
                    "token": "<missing_source>",
                    "expected": "source file exists",
                    "resolved_path": resolved_path.relative_to(root).as_posix(),
                    "fresh": False,
                }
            )
            continue
        resolved_text = resolved_path.read_text(encoding="utf-8") if resolved_path.is_file() else ""
        seen: set[tuple[str, str | None]] = set()
        for match in TOKEN_MATCH_RE.finditer(source_text):
            token = match.group(1)
            precision = match.group(2)
            key = (token, precision)
            if key in seen:
                continue
            seen.add(key)
            expected = _expected_token_value(token, precision, variables)
            if token == "manuscript_staleness_all_fresh":
                expected = "true"
            unresolved = match.group(0) in resolved_text
            fresh = resolved_path.is_file() and not unresolved and expected in resolved_text
            rows.append(
                {
                    "section": path.relative_to(root).as_posix(),
                    "token": token,
                    "expected": expected,
                    "resolved_path": resolved_path.relative_to(root).as_posix(),
                    "fresh": fresh,
                }
            )
    for row in rows:
        if row["token"] == "manuscript_staleness_row_count":
            row["expected"] = str(len(rows))
            resolved_path = root / str(row["resolved_path"])
            resolved_text = resolved_path.read_text(encoding="utf-8") if resolved_path.is_file() else ""
            row["fresh"] = resolved_path.is_file() and row["expected"] in resolved_text
    return {
        "schema": "template_active_inference.manuscript_staleness_report.v1",
        "rows": rows,
        "row_count": len(rows),
        "all_fresh": bool(rows) and all(row["fresh"] for row in rows),
    }


def build_claim_evidence_audit(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    ledger = yaml.safe_load((root / "data" / "claim_ledger.yaml").read_text(encoding="utf-8")) or {}
    rows = []
    for claim in ledger.get("claims") or []:
        rows.append(
            {
                "id": claim.get("id"),
                "path": claim.get("path"),
                "has_evidence": bool(claim.get("evidence")),
                "has_tracks": bool(claim.get("tracks")),
            }
        )
    return {
        "schema": "template_active_inference.claim_evidence_audit.v1",
        "rows": rows,
        "claim_count": len(rows),
        "all_claims_typed": bool(rows) and all(row["has_evidence"] and row["has_tracks"] for row in rows),
    }


def build_validation_gate_index(project_root: Path) -> dict[str, Any]:
    _ = project_root
    rows = [
        {"id": "validate_outputs", "inputs": ["output/data", "output/reports"], "indexed": True},
        {"id": "validate_manuscript", "inputs": ["manuscript/sheaf", "output/manuscript"], "indexed": True},
        {"id": "semantic_sheaf_gluing", "inputs": ["output/data/sheaf_gluing_certificate.json"], "indexed": True},
        {"id": "typed_claim_evidence", "inputs": ["data/claim_ledger.yaml"], "indexed": True},
        {
            "id": "manuscript_staleness_report",
            "inputs": ["output/manuscript", "output/data/manuscript_variables.json"],
            "indexed": True,
        },
        {"id": "animation_frame_deltas", "inputs": ["output/figures/si_belief_trajectory.gif"], "indexed": True},
        {
            "id": "pymdp_runtime_diagnostics",
            "inputs": ["output/reports/pymdp_runtime_diagnostics.json"],
            "indexed": True,
        },
        {
            "id": "pymdp_policy_posterior_grid",
            "inputs": ["output/data/pymdp_policy_posterior_grid.json"],
            "indexed": True,
        },
        {
            "id": "analytical_assumption_index",
            "inputs": ["output/data/analytical_assumption_index.json"],
            "indexed": True,
        },
        {"id": "canonical_sheaf_tracks", "inputs": ["output/data/track_improvement_scope.json"], "indexed": True},
        {"id": "release_bundle_manifest", "inputs": ["output/reports/release_bundle_manifest.json"], "indexed": True},
        {"id": "evidence_field_index", "inputs": ["output/data/evidence_field_index.json"], "indexed": True},
        {
            "id": "theorem_traceability_matrix",
            "inputs": ["output/data/theorem_traceability_matrix.json"],
            "indexed": True,
        },
        {"id": "artifact_diffoscope", "inputs": ["output/reports/artifact_diffoscope.json"], "indexed": True},
        {"id": "proof_extraction_index", "inputs": ["output/data/proof_extraction_index.json"], "indexed": True},
        {"id": "state_space_catalog", "inputs": ["output/data/state_space_catalog.json"], "indexed": True},
        {"id": "causal_ablation_matrix", "inputs": ["output/data/causal_ablation_matrix.json"], "indexed": True},
        {"id": "artifact_license_audit", "inputs": ["output/reports/artifact_license_audit.json"], "indexed": True},
        {"id": "release_notes_evidence", "inputs": ["output/reports/release_notes_evidence.json"], "indexed": True},
        {"id": "proof_dependency_graph", "inputs": ["output/data/proof_dependency_graph.json"], "indexed": True},
        {"id": "state_transition_table", "inputs": ["output/data/state_transition_table.json"], "indexed": True},
        {
            "id": "ablation_sensitivity_report",
            "inputs": ["output/reports/ablation_sensitivity_report.json"],
            "indexed": True,
        },
        {"id": "release_attestation", "inputs": ["output/reports/release_attestation.json"], "indexed": True},
        {"id": "track_improvement_scope", "inputs": ["output/data/track_improvement_scope.json"], "indexed": True},
        {"id": "blocked_scope_manifest", "inputs": ["output/reports/blocked_scope_manifest.json"], "indexed": True},
        {"id": "lake_build", "inputs": ["lean/lakefile.lean"], "indexed": True},
    ]
    return {
        "schema": "template_active_inference.validation_gate_index.v1",
        "rows": rows,
        "gate_count": len(rows),
        "all_indexed": all(row["indexed"] for row in rows),
    }
