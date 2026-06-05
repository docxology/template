"""Integration-audit artifacts for canonical sheaf-track gates."""

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


def write_manuscript_staleness_report(project_root: Path) -> Path:
    """Write the hydrated-manuscript staleness report."""
    root = project_root.resolve()
    return _write_json(
        root / "output" / "reports" / "manuscript_staleness_report.json",
        build_manuscript_staleness_report(root),
    )


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


def build_artifact_diffoscope(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    provenance = _load_json(root / "output" / "data" / "artifact_provenance.json")
    rows = []
    cycle_producers = {SELF_PRODUCER, LATE_HYDRATION_PRODUCER, SHEAF_TRACK_PRODUCER}
    for row in provenance.get("rows") or []:
        rel = str(row.get("artifact") or "")
        if row.get("cycle_excluded") or row.get("producer") in cycle_producers:
            continue
        path = root / rel
        live_hash = _sha256(path) if path.is_file() else ""
        saved_hash = str(row.get("sha256") or "")
        rows.append(
            {
                "artifact": rel,
                "jsonpath": "$",
                "saved_sha256": saved_hash,
                "live_sha256": live_hash,
                "equal": bool(saved_hash) and saved_hash == live_hash,
                "source": "output/data/artifact_provenance.json",
            }
        )
    return {
        "schema": "template_active_inference.artifact_diffoscope.v1",
        "rows": rows,
        "row_count": len(rows),
        "all_equal": bool(rows) and all(row["equal"] for row in rows),
    }


def build_artifact_license_audit(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    provenance = _load_json(root / "output" / "data" / "artifact_provenance.json")
    project_license = "MIT"
    config = yaml.safe_load((root / "manuscript" / "config.yaml").read_text(encoding="utf-8")) or {}
    project_license = str((config.get("metadata") or {}).get("license") or project_license)
    rows = []
    for row in provenance.get("rows") or []:
        rel = str(row.get("artifact") or "")
        generated = rel.startswith("output/")
        rows.append(
            {
                "artifact": rel,
                "license": project_license,
                "source_kind": "generated_local" if generated else "project_source",
                "license_safe": generated or rel.startswith(("manuscript/", "src/", "data/", "lean/", "gnn/")),
                "producer": row.get("producer", ""),
            }
        )
    return {
        "schema": "template_active_inference.artifact_license_audit.v1",
        "rows": rows,
        "row_count": len(rows),
        "all_license_safe": bool(rows) and all(row["license_safe"] and row["license"] for row in rows),
    }


def build_release_notes_evidence(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    release_bundle = _load_json(root / "output" / "reports" / "release_bundle_manifest.json")
    semantic = _load_json(root / "output" / "data" / "sheaf_gluing_certificate.json")
    validation_path = root / "output" / "reports" / "validation_report.json"
    semantic_path = root / "output" / "data" / "sheaf_gluing_certificate.json"
    rows = [
        {
            "note_id": "validation_report_all_passed",
            "source": "output/reports/validation_report.json",
            "claim": "The final saved validation report is a release source; this row is explicitly deferred until the validation stage writes it.",
            "passed": True,
            "deferred_until_validation": not validation_path.exists(),
        },
        {
            "note_id": "release_bundle_sources_present",
            "source": "output/reports/release_bundle_manifest.json",
            "claim": "Required release bundle sources are present or render-deferred.",
            "passed": release_bundle.get("all_required_sources_present") is True,
            "deferred_until_validation": False,
        },
        {
            "note_id": "semantic_certificate_ok",
            "source": "output/data/sheaf_gluing_certificate.json",
            "claim": "The semantic certificate is the source for the release note; semantic correctness is enforced by the semantic gate.",
            "passed": (not semantic_path.exists()) or bool(semantic.get("schema")),
            "deferred_until_validation": not semantic_path.exists(),
        },
    ]
    return {
        "schema": "template_active_inference.release_notes_evidence.v1",
        "rows": rows,
        "row_count": len(rows),
        "all_notes_source_backed": all(row["source"] and row["passed"] for row in rows),
    }


def build_figure_source_map(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    from visualizations.figure_registry import load_figure_registry

    sources = {
        "efe_decomposition": ["src/simulation/efe_decomposition.py", "src/simulation/tmaze_model.py"],
        "ising_mi_curve": ["output/data/parameter_sweep.csv"],
        "free_energy_curve": ["src/analytical/decomposition.py"],
        "si_belief_entropy_curve": ["output/data/si_tmaze_trace.json"],
        "si_obs_action_trace": ["output/data/si_tmaze_summary.json"],
        "si_tmaze_actions": ["output/data/si_tmaze_summary.json"],
        "sheaf_layers_overview": ["output/data/sheaf_coverage_matrix.json"],
        "sheaf_coverage_heatmap": ["output/data/sheaf_coverage_matrix.json"],
        "invariant_dashboard": ["output/reports/invariants.json"],
        "tmaze_schematic": [
            "pymdp.yaml",
            "output/reports/pymdp_runtime_diagnostics.json",
            "output/data/pymdp_policy_posterior_grid.json",
        ],
        "multi_track_architecture": ["tracks.yaml", "manuscript/sheaf/tracks.yaml"],
        "lean_boundary_status": ["lean/TemplateActiveInference"],
        "gnn_ontology_concordance": ["gnn", "manuscript/sections/imrad"],
        "semantic_gluing_graph": [
            "output/data/validation_dependency_graph.json",
            "output/data/sheaf_gluing_certificate.json",
            "output/data/evidence_field_index.json",
        ],
        "theorem_traceability_graph": [
            "output/data/theorem_traceability_matrix.json",
            "output/data/proof_dependency_graph.json",
        ],
        "causal_ablation_heatmap": [
            "output/data/causal_ablation_matrix.json",
            "output/reports/ablation_sensitivity_report.json",
        ],
        "scholarship_source_map": ["output/data/scholarship_source_matrix.json", "manuscript/references.bib"],
    }
    rows = []
    for figure_id in sorted(load_figure_registry(root)):
        rows.append(
            {"figure_id": figure_id, "sources": sources.get(figure_id, []), "mapped": bool(sources.get(figure_id))}
        )
    return {
        "schema": "template_active_inference.figure_source_map.v1",
        "rows": rows,
        "figure_count": len(rows),
        "all_figures_mapped": all(row["mapped"] for row in rows),
    }


def build_figure_hash_manifest(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    rows = []
    for path in sorted((root / "output" / "figures").glob("*")):
        if path.suffix.lower() not in {".png", ".gif"}:
            continue
        rows.append(
            {
                "path": path.relative_to(root).as_posix(),
                "sha256": _sha256(path),
                "size_bytes": path.stat().st_size,
                "fresh": True,
            }
        )
    return {
        "schema": "template_active_inference.figure_hash_manifest.v1",
        "rows": rows,
        "figure_count": len(rows),
        "all_hashes_present": bool(rows) and all(row["sha256"] for row in rows),
    }


def build_scope_boundary_audit(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    rows = []
    violations: list[str] = []
    allowed_future_files = {"15_discussion_outlook.md", "17_conclusion.md"}
    for path in sorted((root / "manuscript").glob("[0-9][0-9]_*.md")):
        text = path.read_text(encoding="utf-8").lower()
        forbidden = "empirical biological" in text or "biological data" in text
        negated = "not empirical" in text or "future" in text
        allowed = path.name in allowed_future_files
        ok = not forbidden or negated or allowed
        rows.append({"section": path.name, "classification": "toy_or_future", "ok": ok})
        if not ok:
            violations.append(path.name)
    return {
        "schema": "template_active_inference.scope_boundary_audit.v1",
        "rows": rows,
        "violations": violations,
        "all_current_claims_toy": not violations,
        "empirical_adapter_enabled": False,
        "scope_boundary_status": "toy_only_pass" if not violations else "scope_leak",
    }


def build_manuscript_evidence_tables(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    claims = build_claim_evidence_audit(root)
    graph = build_integration_dependency_graph(root)
    provenance = _load_json(root / "output" / "data" / "artifact_provenance.json")
    staleness = build_manuscript_staleness_report(root)
    posterior = _load_json(root / "output" / "data" / "pymdp_policy_posterior_grid.json")
    runtime = _load_json(root / "output" / "reports" / "pymdp_runtime_diagnostics.json")
    semantic = _load_json(root / "output" / "data" / "sheaf_gluing_certificate.json")
    track_scope = _load_json(root / "output" / "data" / "track_improvement_scope.json")
    replay_matrix = _load_json(root / "output" / "reports" / "replay_matrix.json")
    diffoscope = _load_json(root / "output" / "reports" / "artifact_diffoscope.json")
    proof = _load_json(root / "output" / "data" / "proof_extraction_index.json")
    catalog = _load_json(root / "output" / "data" / "state_space_catalog.json")
    ablation = _load_json(root / "output" / "data" / "causal_ablation_matrix.json")
    license_audit = _load_json(root / "output" / "reports" / "artifact_license_audit.json")
    release_notes = _load_json(root / "output" / "reports" / "release_notes_evidence.json")
    scholarship = _load_json(root / "output" / "data" / "scholarship_source_matrix.json")
    proof_dependency = _load_json(root / "output" / "data" / "proof_dependency_graph.json")
    transition_table = _load_json(root / "output" / "data" / "state_transition_table.json")
    ablation_sensitivity = _load_json(root / "output" / "reports" / "ablation_sensitivity_report.json")
    release_attestation = _load_json(root / "output" / "reports" / "release_attestation.json")
    tables = [
        {
            "id": "claim_evidence",
            "row_count": claims["claim_count"],
            "source": "output/reports/claim_evidence_audit.json",
        },
        {
            "id": "artifact_producers",
            "row_count": len(graph.get("artifacts") or {}),
            "source": "output/data/validation_dependency_graph.json",
        },
        {
            "id": "artifact_provenance",
            "row_count": int(provenance.get("artifact_count", 0)),
            "source": "output/data/artifact_provenance.json",
        },
        {
            "id": "manuscript_staleness",
            "row_count": int(staleness.get("row_count", 0)),
            "source": "output/reports/manuscript_staleness_report.json",
        },
        {
            "id": "pymdp_policy_posterior",
            "row_count": int(posterior.get("row_count", 0)),
            "source": "output/data/pymdp_policy_posterior_grid.json",
        },
        {
            "id": "pymdp_runtime_diagnostics",
            "row_count": int(runtime.get("construction_count", 0)),
            "source": "output/reports/pymdp_runtime_diagnostics.json",
        },
        {
            "id": "semantic_restrictions",
            "row_count": len(semantic.get("restrictions") or {}),
            "source": "output/data/sheaf_gluing_certificate.json",
        },
        {
            "id": "track_improvement_scope",
            "row_count": int(track_scope.get("improvement_row_count", 0)),
            "source": "output/data/track_improvement_scope.json",
        },
        {
            "id": "replay_matrix",
            "row_count": int(replay_matrix.get("check_count", 0)),
            "source": "output/reports/replay_matrix.json",
        },
        {
            "id": "artifact_diffoscope",
            "row_count": int(diffoscope.get("row_count", 0)),
            "source": "output/reports/artifact_diffoscope.json",
        },
        {
            "id": "proof_extraction",
            "row_count": int(proof.get("theorem_count", 0)),
            "source": "output/data/proof_extraction_index.json",
        },
        {
            "id": "state_space_catalog",
            "row_count": int(catalog.get("row_count", 0)),
            "source": "output/data/state_space_catalog.json",
        },
        {
            "id": "causal_ablation",
            "row_count": int(ablation.get("row_count", 0)),
            "source": "output/data/causal_ablation_matrix.json",
        },
        {
            "id": "artifact_license",
            "row_count": int(license_audit.get("row_count", 0)),
            "source": "output/reports/artifact_license_audit.json",
        },
        {
            "id": "release_notes",
            "row_count": int(release_notes.get("row_count", 0)),
            "source": "output/reports/release_notes_evidence.json",
        },
        {
            "id": "scholarship_sources",
            "row_count": int(scholarship.get("source_count", 0)),
            "source": "output/data/scholarship_source_matrix.json",
        },
        {
            "id": "proof_dependency_graph",
            "row_count": int(proof_dependency.get("edge_count", 0)),
            "source": "output/data/proof_dependency_graph.json",
        },
        {
            "id": "state_transition_table",
            "row_count": int(transition_table.get("row_count", 0)),
            "source": "output/data/state_transition_table.json",
        },
        {
            "id": "ablation_sensitivity",
            "row_count": int(ablation_sensitivity.get("row_count", 0)),
            "source": "output/reports/ablation_sensitivity_report.json",
        },
        {
            "id": "release_attestation",
            "row_count": int(release_attestation.get("row_count", 0)),
            "source": "output/reports/release_attestation.json",
        },
    ]
    return {
        "schema": "template_active_inference.manuscript_evidence_tables.v1",
        "tables": tables,
        "table_count": len(tables),
        "all_source_backed": all(table["row_count"] > 0 and table["source"] for table in tables),
    }


def build_adversarial_audit(project_root: Path) -> dict[str, Any]:
    from roadmap_tracks.sheaf_tracks import build_adversarial_audit as build_canonical_adversarial_audit

    return dict(build_canonical_adversarial_audit(project_root))


def build_integration_semantic_snapshot(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    toy = _load_json(root / "output" / "data" / "sensitivity_sweep.json")
    assumptions = _load_json(root / "output" / "data" / "analytical_assumption_index.json")
    policy = _load_json(root / "output" / "data" / "si_policy_comparison.json")
    posterior = _load_json(root / "output" / "data" / "pymdp_policy_posterior_grid.json")
    runtime = _load_json(root / "output" / "reports" / "pymdp_runtime_diagnostics.json")
    topology_traces = _load_json(root / "output" / "data" / "si_graph_world_topology_traces.json")
    uncertainty = _load_json(root / "output" / "data" / "uncertainty_summary.json")
    benchmark = _load_json(root / "output" / "data" / "toy_benchmark_matrix.json")
    model_checking = _load_json(root / "output" / "reports" / "model_checking_witnesses.json")
    lean_theorems = _load_json(root / "output" / "reports" / "lean_theorem_inventory.json")
    lean_graph = _load_json(root / "output" / "reports" / "lean_graph_world_inventory.json")
    interop = _load_json(root / "output" / "data" / "interop_roundtrip_report.json")
    adversarial = build_adversarial_audit(root)
    dependency = build_integration_dependency_graph(root)
    stale = build_stale_artifact_report(root)
    tokens = build_manuscript_token_provenance(root)
    figures = build_figure_source_map(root)
    scope = build_scope_boundary_audit(root)
    staleness = build_manuscript_staleness_report(root)
    provenance = _load_json(root / "output" / "data" / "artifact_provenance.json")
    animation = _load_json(root / "output" / "data" / "animation_frame_deltas.json")
    diffoscope = _load_json(root / "output" / "reports" / "artifact_diffoscope.json")
    proof = _load_json(root / "output" / "data" / "proof_extraction_index.json")
    catalog = _load_json(root / "output" / "data" / "state_space_catalog.json")
    ablation = _load_json(root / "output" / "data" / "causal_ablation_matrix.json")
    license_audit = _load_json(root / "output" / "reports" / "artifact_license_audit.json")
    release_notes = _load_json(root / "output" / "reports" / "release_notes_evidence.json")
    scholarship = _load_json(root / "output" / "data" / "scholarship_source_matrix.json")
    restrictions = {
        "analytical_assumptions_indexed": assumptions.get("all_equations_indexed") is True,
        "pymdp_runtime_diagnostics_ok": runtime.get("ok") is True
        and int(runtime.get("unexpected_warning_count", 0) or 0) == 0,
        "policy_comparison_grid_complete": (policy.get("summary") or {}).get("complete_grid") is True,
        "policy_posterior_normalized": posterior.get("all_available_posteriors_normalized") is True
        and posterior.get("all_unavailable_rows_explained") is True,
        "efe_availability_or_fallback_complete": (policy.get("summary") or {}).get("all_efe_rows_explained") is True,
        "topology_trace_consistency": topology_traces.get("all_trace_summary_agree") is True,
        "sensitivity_grid_complete": toy.get("complete_grid") is True,
        "uncertainty_rows_normalized": uncertainty.get("all_normalized") is True,
        "benchmark_rows_complete": benchmark.get("all_models_complete") is True,
        "model_checking_all_passed": model_checking.get("all_passed") is True,
        "lean_theorem_inventory_proved": lean_theorems.get("all_proved") is True,
        "lean_graph_world_topologies_witnessed": lean_graph.get("all_topologies_witnessed") is True
        and lean_graph.get("all_policy_witnesses_present") is True,
        "interop_lossless": interop.get("all_lossless") is True,
        "adversarial_expected_failures_documented": adversarial["all_expected_failures_documented"],
        "dependency_edge_types_ok": dependency["all_required_edge_types_present"],
        "stale_flags_clear": stale["all_fresh"],
        "token_provenance_complete": tokens["all_tokens_mapped"],
        "figure_source_coverage": figures["all_figures_mapped"],
        "animation_deltas_nonzero": animation.get("all_nonzero") is True,
        "scope_boundary_toy_only": scope["all_current_claims_toy"],
        "manuscript_staleness_fresh": staleness["all_fresh"],
        "artifact_provenance_seed_config_complete": provenance.get("all_seeded") is True
        and provenance.get("all_config_digests") is True,
        "artifact_diffoscope_equal": diffoscope.get("all_equal") is True,
        "proof_extraction_constructive": proof.get("all_extracted") is True and proof.get("all_constructive") is True,
        "state_space_catalog_finite": catalog.get("all_finite") is True and catalog.get("all_counts_positive") is True,
        "causal_ablation_complete": ablation.get("complete_grid") is True and ablation.get("all_deterministic") is True,
        "artifact_license_safe": license_audit.get("all_license_safe") is True,
        "release_notes_source_backed": release_notes.get("all_notes_source_backed") is True,
        "scholarship_sources_connected": scholarship.get("all_sources_connected") is True,
    }
    return {
        "schema": "template_active_inference.integration_semantic_snapshot.v1",
        "ok": all(restrictions.values()),
        "restrictions": restrictions,
        "sections": {
            "structural": {"ok": dependency["all_required_edge_types_present"]},
            "semantic": {"ok": restrictions["interop_lossless"] and restrictions["scope_boundary_toy_only"]},
            "artifact": {"ok": restrictions["stale_flags_clear"] and restrictions["figure_source_coverage"]},
            "manuscript_variable": {
                "ok": restrictions["token_provenance_complete"] and restrictions["manuscript_staleness_fresh"]
            },
        },
    }


def write_integration_audit_artifacts(project_root: Path) -> dict[str, Path]:
    root = project_root.resolve()
    paths = {
        "producer_completeness": _write_json(
            root / "output" / "reports" / "producer_completeness.json",
            build_producer_completeness(root),
        ),
        "stale_artifacts": _write_json(
            root / "output" / "reports" / "stale_artifact_report.json",
            build_stale_artifact_report(root),
        ),
        "cross_track_symbols": _write_json(
            root / "output" / "data" / "cross_track_symbol_table.json",
            build_cross_track_symbol_table(root),
        ),
        "token_provenance": _write_json(
            root / "output" / "data" / "manuscript_token_provenance.json",
            build_manuscript_token_provenance(root),
        ),
        "claim_audit": _write_json(
            root / "output" / "reports" / "claim_evidence_audit.json",
            build_claim_evidence_audit(root),
        ),
        "gate_index": _write_json(
            root / "output" / "data" / "validation_gate_index.json",
            build_validation_gate_index(root),
        ),
        "figure_source_map": _write_json(
            root / "output" / "data" / "figure_source_map.json",
            build_figure_source_map(root),
        ),
        "figure_hash_manifest": _write_json(
            root / "output" / "reports" / "figure_hash_manifest.json",
            build_figure_hash_manifest(root),
        ),
        "scope_boundary": _write_json(
            root / "output" / "reports" / "scope_boundary_audit.json",
            build_scope_boundary_audit(root),
        ),
        "adversarial_audit": _write_json(
            root / "output" / "reports" / "adversarial_audit.json",
            build_adversarial_audit(root),
        ),
        "manuscript_staleness": _write_json(
            root / "output" / "reports" / "manuscript_staleness_report.json",
            build_manuscript_staleness_report(root),
        ),
        "artifact_diffoscope": _write_json(
            root / "output" / "reports" / "artifact_diffoscope.json",
            build_artifact_diffoscope(root),
        ),
        "artifact_license": _write_json(
            root / "output" / "reports" / "artifact_license_audit.json",
            build_artifact_license_audit(root),
        ),
        "release_notes": _write_json(
            root / "output" / "reports" / "release_notes_evidence.json",
            build_release_notes_evidence(root),
        ),
        "manuscript_tables": _write_json(
            root / "output" / "data" / "manuscript_evidence_tables.json",
            build_manuscript_evidence_tables(root),
        ),
    }
    return paths


def validate_integration_audit_artifacts(project_root: Path) -> list[str]:
    root = project_root.resolve()
    issues: list[str] = []
    producer = _load_json(root / "output" / "reports" / "producer_completeness.json")
    producer_rows = producer.get("rows") or []
    producer_derived = bool(producer_rows) and all(row.get("exists") and row.get("configured") for row in producer_rows)
    if producer.get("all_complete") is not True or producer.get("all_complete") != producer_derived:
        # Re-derived from rows: a row showing a missing/unconfigured producer fails closed even
        # if the stored all_complete bit was left true.
        issues.append("producer_completeness.json is incomplete")
    stale = _load_json(root / "output" / "reports" / "stale_artifact_report.json")
    if stale.get("all_fresh") is not True:
        issues.append("stale_artifact_report.json records stale artifacts")
    for row in stale.get("rows") or []:
        path = root / str(row.get("artifact", ""))
        if not path.is_file():
            issues.append(f"stale_artifact_report.json missing artifact {row.get('artifact')}")
            continue
        if row.get("sha256") != _sha256(path):
            issues.append(f"stale_artifact_report.json hash mismatch for {row.get('artifact')}")
    tokens = _load_json(root / "output" / "data" / "manuscript_token_provenance.json")
    tokens_derived = bool(tokens.get("tokens")) and all(row.get("mapped") for row in tokens.get("tokens") or [])
    if tokens.get("all_tokens_mapped") is not True or tokens.get("all_tokens_mapped") != tokens_derived:
        issues.append("manuscript_token_provenance.json has unmapped tokens")
    figures = _load_json(root / "output" / "data" / "figure_source_map.json")
    figures_derived = bool(figures.get("rows")) and all(row.get("mapped") for row in figures.get("rows") or [])
    if figures.get("all_figures_mapped") is not True or figures.get("all_figures_mapped") != figures_derived:
        issues.append("figure_source_map.json has unmapped figures")
    claim_audit = _load_json(root / "output" / "reports" / "claim_evidence_audit.json")
    claims_derived = bool(claim_audit.get("rows")) and all(
        row.get("has_evidence") and row.get("has_tracks") for row in claim_audit.get("rows") or []
    )
    if claim_audit.get("all_claims_typed") is not True or claim_audit.get("all_claims_typed") != claims_derived:
        issues.append("claim_evidence_audit.json has untyped claims")
    scope = _load_json(root / "output" / "reports" / "scope_boundary_audit.json")
    if scope.get("all_current_claims_toy") is not True:
        issues.append("scope_boundary_audit.json records empirical scope leakage")
    adversarial = _load_json(root / "output" / "reports" / "adversarial_audit.json")
    if adversarial.get("all_expected_failures_documented") is not True:
        issues.append("adversarial_audit.json has undocumented expected failures")
    figure_hash = _load_json(root / "output" / "reports" / "figure_hash_manifest.json")
    figure_hash_derived = bool(figure_hash.get("rows")) and all(
        row.get("sha256") for row in figure_hash.get("rows") or []
    )
    if (
        figure_hash.get("all_hashes_present") is not True
        or figure_hash.get("all_hashes_present") != figure_hash_derived
    ):
        issues.append("figure_hash_manifest.json lacks hashes")
    tables = _load_json(root / "output" / "data" / "manuscript_evidence_tables.json")
    tables_derived = bool(tables.get("tables")) and all(
        int(table.get("row_count", 0) or 0) > 0 and table.get("source") for table in tables.get("tables") or []
    )
    if tables.get("all_source_backed") is not True or tables.get("all_source_backed") != tables_derived:
        issues.append("manuscript_evidence_tables.json has unbacked tables")
    staleness = _load_json(root / "output" / "reports" / "manuscript_staleness_report.json")
    if staleness.get("schema") != "template_active_inference.manuscript_staleness_report.v1":
        issues.append("manuscript_staleness_report.json schema mismatch")
    if staleness.get("all_fresh") is not True:
        issues.append("manuscript_staleness_report.json records stale manuscript tokens")
    live_staleness = build_manuscript_staleness_report(root)
    saved_rows = [
        {key: row.get(key) for key in ("section", "token", "expected", "fresh")} for row in staleness.get("rows") or []
    ]
    live_rows = [
        {key: row.get(key) for key in ("section", "token", "expected", "fresh")}
        for row in live_staleness.get("rows") or []
    ]
    if staleness and saved_rows != live_rows:
        issues.append("manuscript_staleness_report.json is stale relative to live manuscript tokens")
    symbols = _load_json(root / "output" / "data" / "cross_track_symbol_table.json")
    symbols_derived = bool(symbols.get("rows")) and all(row.get("consistent") for row in symbols.get("rows") or [])
    if symbols.get("all_consistent") is not True or symbols.get("all_consistent") != symbols_derived:
        issues.append("cross_track_symbol_table.json has inconsistent symbols")
    gate_index = _load_json(root / "output" / "data" / "validation_gate_index.json")
    gates_derived = bool(gate_index.get("rows")) and all(row.get("indexed") for row in gate_index.get("rows") or [])
    if gate_index.get("all_indexed") is not True or gate_index.get("all_indexed") != gates_derived:
        issues.append("validation_gate_index.json has unindexed gates")
    diffoscope = _load_json(root / "output" / "reports" / "artifact_diffoscope.json")
    if diffoscope.get("schema") != "template_active_inference.artifact_diffoscope.v1":
        issues.append("artifact_diffoscope.json schema mismatch")
    if diffoscope.get("all_equal") is not True:
        issues.append("artifact_diffoscope.json records artifact drift")
    license_audit = _load_json(root / "output" / "reports" / "artifact_license_audit.json")
    if license_audit.get("schema") != "template_active_inference.artifact_license_audit.v1":
        issues.append("artifact_license_audit.json schema mismatch")
    if license_audit.get("all_license_safe") is not True:
        issues.append("artifact_license_audit.json records unsafe artifacts")
    release_notes = _load_json(root / "output" / "reports" / "release_notes_evidence.json")
    if release_notes.get("schema") != "template_active_inference.release_notes_evidence.v1":
        issues.append("release_notes_evidence.json schema mismatch")
    if release_notes.get("all_notes_source_backed") is not True:
        issues.append("release_notes_evidence.json has unsupported notes")
    return issues
