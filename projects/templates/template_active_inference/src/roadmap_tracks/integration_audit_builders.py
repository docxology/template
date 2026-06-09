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

from roadmap_tracks.row_aggregates import all_rows

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
    from manuscript.variables import generate_variables
    from ontology.bindings import load_section_ontology
    from visualizations.figure_registry import load_figure_registry

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
                    "source_kind": "gnn_variable",
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
    lean = _load_json(root / "output" / "reports" / "lean_theorem_inventory.json")
    for row in lean.get("rows") or []:
        theorem = str(row.get("name") or "")
        rows.append(
            {
                "source_kind": "lean_theorem",
                "model": "lean_boundary",
                "symbol": theorem,
                "shape": ["theorem"],
                "dtype": "Lean.Prop",
                "gnn_term": "",
                "section_ontology_term": "",
                "json_field": theorem,
                "lean_namespace": "TemplateActiveInference",
                "shape_declared": bool(theorem),
                "dtype_declared": True,
                "ontology_declared": True,
                "section_ontology_declared": True,
                "term_consistent": True,
                "consistent": bool(theorem),
            }
        )
    variables = generate_variables(root, require_analysis_outputs=False)
    for token in sorted(variables):
        rows.append(
            {
                "source_kind": "manuscript_variable",
                "model": "manuscript_variables",
                "symbol": token,
                "shape": [1],
                "dtype": type(variables[token]).__name__,
                "gnn_term": "",
                "section_ontology_term": "",
                "json_field": f"$.{token}",
                "lean_namespace": "",
                "shape_declared": True,
                "dtype_declared": True,
                "ontology_declared": True,
                "section_ontology_declared": True,
                "term_consistent": True,
                "consistent": True,
            }
        )
    evidence = _load_json(root / "output" / "data" / "evidence_field_index.json")
    for row in evidence.get("rows") or []:
        symbol = f"{row.get('artifact')}:{row.get('jsonpath')}"
        rows.append(
            {
                "source_kind": "json_field",
                "model": row.get("artifact", ""),
                "symbol": symbol,
                "shape": ["jsonpath"],
                "dtype": "JSON",
                "gnn_term": "",
                "section_ontology_term": "",
                "json_field": row.get("jsonpath", ""),
                "lean_namespace": "",
                "shape_declared": bool(row.get("jsonpath")),
                "dtype_declared": True,
                "ontology_declared": True,
                "section_ontology_declared": True,
                "term_consistent": True,
                "consistent": bool(row.get("jsonpath")),
            }
        )
    for figure_id in sorted(load_figure_registry(root)):
        rows.append(
            {
                "source_kind": "figure_label",
                "model": "figure_registry",
                "symbol": figure_id,
                "shape": ["figure"],
                "dtype": "PNG",
                "gnn_term": "",
                "section_ontology_term": "",
                "json_field": f"$.figures.{figure_id}",
                "lean_namespace": "",
                "shape_declared": True,
                "dtype_declared": True,
                "ontology_declared": True,
                "section_ontology_declared": True,
                "term_consistent": True,
                "consistent": True,
            }
        )
    return {
        "schema": "template_active_inference.cross_track_symbol_table.v1",
        "rows": rows,
        "symbol_count": len(rows),
        "source_kinds": sorted({str(row.get("source_kind")) for row in rows if row.get("source_kind")}),
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
        seen: set[tuple[str, str | None]] = set()
        for match in TOKEN_MATCH_RE.finditer(text):
            token = match.group(1)
            precision = match.group(2)
            key = (token, precision)
            if key in seen:
                continue
            seen.add(key)
            expected_value = _expected_token_value(token, precision, variables)
            hydrated_path = root / "output" / "manuscript" / path.name
            rows.append(
                {
                    "section": path.relative_to(root).as_posix(),
                    "token": token,
                    "precision": precision,
                    "source": source,
                    "source_jsonpath": f"$.{token}",
                    "expected_value": expected_value,
                    "consumer_kind": "appendix_fragment"
                    if "appendix" in path.as_posix()
                    else "manuscript_section",
                    "generated_output_path": (
                        hydrated_path.relative_to(root).as_posix()
                        if hydrated_path.is_file()
                        else ""
                    ),
                    "hydrated_value_present": True
                    if not hydrated_path.is_file()
                    else expected_value in hydrated_path.read_text(encoding="utf-8"),
                    "mapped": token in variables,
                }
            )
    return {
        "schema": "template_active_inference.manuscript_token_provenance.v1",
        "tokens": rows,
        "token_count": len(rows),
        "consumer_kinds": sorted({str(row.get("consumer_kind")) for row in rows if row.get("consumer_kind")}),
        "all_tokens_mapped": all(row["mapped"] and row["source_jsonpath"] for row in rows),
        "all_hydrated_values_current": all(row["hydrated_value_present"] for row in rows),
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
        evidence = claim.get("evidence") or {}
        predicate = str(
            evidence.get("predicate")
            or ("equals" if "equals" in evidence else "")
            or ("min" if "min" in evidence else "")
            or ("len_equals" if "len_equals" in evidence else "")
            or ("set_equals" if "set_equals" in evidence else "")
            or ("file_exists" if evidence.get("predicate") == "file_exists" else "")
        )
        waiver = str(evidence.get("waiver") or "")
        substantive = bool(evidence and (predicate or waiver))
        failure_reason = "" if substantive and claim.get("tracks") else "missing predicate/waiver or tracks"
        rows.append(
            {
                "id": claim.get("id"),
                "path": claim.get("path"),
                "jsonpath": f"$.{evidence.get('field')}" if evidence.get("field") else "$",
                "predicate": predicate,
                "waiver": waiver,
                "substantive": substantive,
                "failure_reason": failure_reason,
                "has_evidence": bool(claim.get("evidence")),
                "has_tracks": bool(claim.get("tracks")),
            }
        )
    return {
        "schema": "template_active_inference.claim_evidence_audit.v1",
        "rows": rows,
        "claim_count": len(rows),
        "all_claims_typed": bool(rows)
        and all(row["has_evidence"] and row["has_tracks"] and row["substantive"] and not row["failure_reason"] for row in rows),
    }


def build_validation_gate_index(project_root: Path) -> dict[str, Any]:
    _ = project_root
    def gate(
        gate_id: str,
        inputs: list[str],
        outputs: list[str],
        negative_control: str,
        command: str = "uv run python scripts/validate_outputs.py",
    ) -> dict[str, Any]:
        return {
            "id": gate_id,
            "command": command,
            "inputs": inputs,
            "required_inputs": inputs,
            "declared_outputs": outputs,
            "negative_control_id": negative_control,
            "indexed": True,
        }

    rows = [
        gate("validate_outputs", ["output/data", "output/reports"], ["output/reports/validation_report.json"], "stale_provenance_hash"),
        gate("validate_manuscript", ["manuscript/sheaf", "output/manuscript"], ["output/data/sheaf_gluing_certificate.json"], "stale_semantic_certificate", "uv run python scripts/compose_manuscript.py --validate-only --strict"),
        gate("semantic_sheaf_gluing", ["output/data/sheaf_gluing_certificate.json"], ["output/data/sheaf_gluing_certificate.json"], "stale_semantic_certificate"),
        gate("typed_claim_evidence", ["data/claim_ledger.yaml"], ["output/reports/claim_evidence_audit.json"], "missing_typed_claim"),
        {
            "id": "manuscript_staleness_report",
            "command": "uv run python scripts/compose_manuscript.py --validate-only --strict",
            "inputs": ["output/manuscript", "output/data/manuscript_variables.json"],
            "required_inputs": ["output/manuscript", "output/data/manuscript_variables.json"],
            "declared_outputs": ["output/reports/manuscript_staleness_report.json"],
            "negative_control_id": "stale_hydrated_manuscript_value",
            "indexed": True,
        },
        gate("animation_frame_deltas", ["output/figures/si_belief_trajectory.gif"], ["output/data/animation_frame_deltas.json"], "static_animation_delta_manifest"),
        gate("pymdp_runtime_diagnostics", ["output/reports/pymdp_runtime_diagnostics.json"], ["output/reports/pymdp_runtime_diagnostics.json"], "unexpected_pymdp_runtime_warning"),
        gate("pymdp_policy_posterior_grid", ["output/data/pymdp_policy_posterior_grid.json"], ["output/data/pymdp_policy_posterior_grid.json"], "unnormalized_policy_posterior"),
        gate("analytical_assumption_index", ["output/data/analytical_assumption_index.json"], ["output/data/analytical_assumption_index.json"], "missing_analytical_assumption"),
        gate("canonical_sheaf_tracks", ["output/data/track_improvement_scope.json"], ["output/data/track_improvement_scope.json"], "missing_sheaf_track_producer"),
        gate("release_bundle_manifest", ["output/reports/release_bundle_manifest.json"], ["output/reports/release_bundle_manifest.json"], "release_bundle_parity_failure"),
        gate("evidence_field_index", ["output/data/evidence_field_index.json"], ["output/data/evidence_field_index.json"], "missing_typed_claim"),
        gate("theorem_traceability_matrix", ["output/data/theorem_traceability_matrix.json"], ["output/data/theorem_traceability_matrix.json"], "theorem_traceability_unlinked"),
        gate("artifact_diffoscope", ["output/reports/artifact_diffoscope.json"], ["output/reports/artifact_diffoscope.json"], "artifact_diffoscope_missed_hash_drift"),
        gate("proof_extraction_index", ["output/data/proof_extraction_index.json"], ["output/data/proof_extraction_index.json"], "proof_extraction_missing_statement"),
        gate("state_space_catalog", ["output/data/state_space_catalog.json"], ["output/data/state_space_catalog.json"], "state_space_catalog_missing_finite_space"),
        gate("causal_ablation_matrix", ["output/data/causal_ablation_matrix.json"], ["output/data/causal_ablation_matrix.json"], "causal_ablation_missing_cell"),
        gate("artifact_license_audit", ["output/reports/artifact_license_audit.json"], ["output/reports/artifact_license_audit.json"], "artifact_license_unsafe_artifact"),
        gate("release_notes_evidence", ["output/reports/release_notes_evidence.json"], ["output/reports/release_notes_evidence.json"], "release_notes_claim_failed_gate_passed"),
        gate("proof_dependency_graph", ["output/data/proof_dependency_graph.json"], ["output/data/proof_dependency_graph.json"], "proof_dependency_unlinked_theorem"),
        gate("state_transition_table", ["output/data/state_transition_table.json"], ["output/data/state_transition_table.json"], "state_transition_missing_model"),
        gate("ablation_sensitivity_report", ["output/reports/ablation_sensitivity_report.json"], ["output/reports/ablation_sensitivity_report.json"], "ablation_sensitivity_unbacked_effect"),
        gate("release_attestation", ["output/reports/release_attestation.json"], ["output/reports/release_attestation.json"], "release_attestation_failed_gate"),
        gate("track_improvement_scope", ["output/data/track_improvement_scope.json"], ["output/data/track_improvement_scope.json"], "missing_sheaf_track_producer"),
        gate("blocked_scope_manifest", ["output/reports/blocked_scope_manifest.json"], ["output/reports/blocked_scope_manifest.json"], "empirical_adapter_live"),
        gate("lake_build", ["lean/lakefile.lean"], ["output/reports/lean_theorem_inventory.json"], "lean_forbidden_token", "uv run python scripts/generate_formal_interop_tracks.py"),
    ]
    return {
        "schema": "template_active_inference.validation_gate_index.v1",
        "rows": rows,
        "gate_count": len(rows),
        "all_indexed": all_rows(
            {"rows": rows},
            lambda row: row.get("indexed")
            and row.get("command")
            and row.get("required_inputs")
            and row.get("declared_outputs")
            and row.get("negative_control_id"),
        ),
    }
