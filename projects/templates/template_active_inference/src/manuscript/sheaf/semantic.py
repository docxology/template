"""Semantic gluing certificate for the multi-track manuscript sheaf."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gnn.parser import parse_gnn_file
from manuscript.variables import generate_variables
from ontology.bindings import (
    BERNOULLI_EXPECTED_TERMS,
    BERNOULLI_SYMBOL_MAP,
    SI_EXPECTED_TERMS,
    SI_SYMBOL_MAP,
    load_section_ontology,
    validate_all_gnn_ontology,
)

from .coverage import gray_cell_count, load_sheaf_coverage_context

SEMANTIC_SCHEMA = "template_active_inference.semantic_gluing.v2"

ARTIFACT_PRODUCERS: dict[str, str] = {
    "output/data/parameter_sweep.csv": "run_analytical_sweep.py",
    "output/data/si_tmaze_summary.json": "simulate_si_tmaze.py",
    "output/data/si_tmaze_trace.json": "simulate_si_tmaze.py",
    "output/data/si_policy_comparison.json": "simulate_si_tmaze.py",
    "output/data/si_graph_world_summary.json": "simulate_si_graph_world.py",
    "output/data/si_graph_world_trace.json": "simulate_si_graph_world.py",
    "output/data/analysis_statistics.json": "compute_statistics.py",
    "output/data/sheaf_coverage_matrix.json": "generate_figures.py",
    "output/data/manuscript_variables.json": "z_generate_manuscript_variables.py",
    "output/data/sheaf_evidence_crosswalk.json": "z_generate_manuscript_variables.py",
    "output/data/validation_dependency_graph.json": "z_generate_manuscript_variables.py",
    "output/data/sheaf_gluing_certificate.json": "z_generate_manuscript_variables.py",
    "output/data/artifact_provenance.json": "generate_validation_spine.py",
    "output/figures/semantic_gluing_graph.png": "generate_figures.py",
    "output/figures/si_belief_trajectory.gif": "render_animation.py",
    "output/figures/sheaf_layers_overview.png": "generate_figures.py",
    "output/figures/sheaf_coverage_heatmap.png": "generate_figures.py",
    "output/figures/figure_registry.json": "generate_figures.py",
    "output/reports/invariants.json": "run_analytical_sweep.py",
    "output/reports/si_invariants.json": "simulate_si_tmaze.py",
    "output/reports/si_tmaze_run_report.json": "simulate_si_tmaze.py",
    "output/reports/reproducibility_replay.json": "generate_validation_spine.py",
    "output/reports/counterexample_matrix.json": "generate_validation_spine.py",
}

ARTIFACT_CONSUMERS: dict[str, tuple[str, ...]] = {
    "output/data/si_policy_comparison.json": ("methods_pymdp", "results_si_tmaze"),
    "output/data/si_graph_world_summary.json": ("methods_pymdp", "results_si_tmaze"),
    "output/data/si_graph_world_trace.json": ("methods_pymdp", "results_si_tmaze", "appendix_full_sheaf"),
    "output/data/sheaf_gluing_certificate.json": ("methods_sheaf", "appendix_full_sheaf"),
    "output/data/sheaf_evidence_crosswalk.json": ("methods_sheaf",),
    "output/data/validation_dependency_graph.json": ("methods_sheaf",),
    "output/data/artifact_provenance.json": ("methods_sheaf",),
    "output/reports/counterexample_matrix.json": ("methods_sheaf",),
    "output/reports/reproducibility_replay.json": ("results_invariants",),
    "output/figures/semantic_gluing_graph.png": ("methods_sheaf",),
    "output/figures/si_belief_trajectory.gif": ("appendix_full_sheaf",),
}

ARTIFACT_GATES: dict[str, tuple[str, ...]] = {
    "output/data/sheaf_gluing_certificate.json": ("validate_manuscript", "validate_outputs"),
    "output/data/sheaf_evidence_crosswalk.json": ("validate_manuscript", "validate_outputs"),
    "output/data/validation_dependency_graph.json": ("validate_manuscript", "validate_outputs"),
    "output/data/artifact_provenance.json": ("validate_manuscript", "validate_outputs"),
    "output/data/si_policy_comparison.json": ("validate_outputs",),
    "output/data/si_graph_world_summary.json": ("validate_outputs",),
    "output/data/si_graph_world_trace.json": ("validate_outputs",),
    "output/figures/si_belief_trajectory.gif": ("validate_outputs",),
    "output/figures/semantic_gluing_graph.png": ("validate_outputs", "figure_registry"),
    "output/reports/reproducibility_replay.json": ("validate_outputs",),
    "output/reports/counterexample_matrix.json": ("validate_outputs", "validate_manuscript"),
}


def _rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


def _configured_analysis_scripts(root: Path) -> list[str]:
    import yaml

    config_path = root / "manuscript" / "config.yaml"
    if not config_path.is_file():
        return []
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    analysis = data.get("analysis") or {}
    scripts = analysis.get("scripts") or []
    return [str(script) for script in scripts]


def _claims_by_path(root: Path) -> dict[str, list[str]]:
    claims: dict[str, list[str]] = {}
    for claim in _claim_records(root):
        path = claim.get("path")
        claim_id = claim.get("id")
        if path and claim_id:
            claims.setdefault(str(path), []).append(str(claim_id))
    return claims


def _animation_frame_count(root: Path) -> int:
    gif_path = root / "output" / "figures" / "si_belief_trajectory.gif"
    if not gif_path.is_file():
        return 0
    try:
        from PIL import Image, ImageSequence

        with Image.open(gif_path) as image:
            return sum(1 for _ in ImageSequence.Iterator(image))
    except (ImportError, OSError, ValueError, EOFError):
        return 0


def _lean_status(root: Path) -> dict[str, Any]:
    try:
        from visualizations.lean_boundary import load_lean_boundary_rows

        rows = load_lean_boundary_rows(root)
    except (ImportError, OSError, ValueError):
        return {"module_count": 0, "proved_count": 0, "all_proved": False, "names": []}
    return {
        "module_count": len(rows),
        "proved_count": sum(1 for row in rows if row.status == "proved"),
        "all_proved": bool(rows) and all(row.status == "proved" for row in rows),
        "names": sorted(row.name for row in rows),
    }


def _policy_comparison_restrictions(root: Path) -> dict[str, Any]:
    path = root / "output" / "data" / "si_policy_comparison.json"
    data = _load_json(path)
    runs = data.get("runs") or []
    return {
        "run_count": int((data.get("summary") or {}).get("run_count", len(runs)) or 0),
        "modes": sorted({str(row.get("mode")) for row in runs if row.get("mode")}),
        "horizons": sorted({int(row.get("horizon")) for row in runs if row.get("horizon") is not None}),
        "goal_reached_count": sum(1 for row in runs if row.get("goal_reached") is True),
    }


def _graph_world_restrictions(root: Path) -> dict[str, Any]:
    summary = _load_json(root / "output" / "data" / "si_graph_world_summary.json")
    trace = _load_json(root / "output" / "data" / "si_graph_world_trace.json")
    trace_steps = trace.get("steps") or []
    summary_steps = int(summary.get("steps", 0) or 0)
    return {
        "steps": summary_steps,
        "trace_steps": len(trace_steps),
        "steps_match": summary_steps == len(trace_steps) and summary_steps > 0,
        "goal_reached": summary.get("goal_reached") is True,
    }


def _pymdp_hash_restrictions(root: Path) -> dict[str, Any]:
    summary = _load_json(root / "output" / "data" / "si_tmaze_summary.json")
    stats = _load_json(root / "output" / "data" / "analysis_statistics.json")
    return {
        "mode_match": not summary or not stats or summary.get("mode") == stats.get("pymdp_mode"),
        "config_hash_match": not summary or not stats or summary.get("config_hash") == stats.get("pymdp_config_hash"),
    }


def _gnn_symbols(root: Path, rel_path: str) -> dict[str, str]:
    path = root / rel_path
    if not path.is_file():
        return {}
    return dict(parse_gnn_file(path).ontology)


def _section_ontology_symbols(root: Path, rel_path: str) -> dict[str, str]:
    symbols = load_section_ontology(root / rel_path)
    return {str(key): str(value) for key, value in symbols.items()}


def _expected_symbol_gaps(
    *,
    label: str,
    gnn_symbols: dict[str, str],
    section_symbols: dict[str, str],
    symbol_map: dict[str, str],
    expected_terms: dict[str, str],
) -> list[str]:
    gaps: list[str] = []
    for _, variable in symbol_map.items():
        expected = expected_terms.get(variable)
        if expected is None:
            continue
        gnn_term = gnn_symbols.get(variable)
        section_term = section_symbols.get(variable)
        if gnn_term != expected:
            gaps.append(f"{label}: GNN variable {variable!r} annotated {gnn_term!r}, expected {expected!r}")
        if section_term != expected:
            gaps.append(
                f"{label}: section ontology variable {variable!r} annotated {section_term!r}, expected {expected!r}"
            )
    return gaps


def semantic_gluing_issues(project_root: Path) -> list[str]:
    """Return semantic cross-track disagreements not covered by structural laws."""
    root = project_root.resolve()
    issues: list[str] = []

    ctx = load_sheaf_coverage_context(root)
    missing = gray_cell_count(ctx.matrix)
    if missing:
        issues.append(f"coverage matrix has {missing} missing bound fragment(s)")

    issues.extend(validate_all_gnn_ontology(root))
    issues.extend(
        _expected_symbol_gaps(
            label="bernoulli_toy",
            gnn_symbols=_gnn_symbols(root, "gnn/bernoulli_toy.gnn.md"),
            section_symbols=_section_ontology_symbols(
                root,
                "manuscript/sections/imrad/methods_analytical/ontology.yaml",
            ),
            symbol_map=BERNOULLI_SYMBOL_MAP,
            expected_terms=BERNOULLI_EXPECTED_TERMS,
        )
    )
    issues.extend(
        _expected_symbol_gaps(
            label="si_tmaze",
            gnn_symbols=_gnn_symbols(root, "gnn/si_tmaze.gnn.md"),
            section_symbols=_section_ontology_symbols(
                root,
                "manuscript/sections/imrad/methods_pymdp/ontology.yaml",
            ),
            symbol_map=SI_SYMBOL_MAP,
            expected_terms=SI_EXPECTED_TERMS,
        )
    )

    variables_path = root / "output" / "data" / "manuscript_variables.json"
    if variables_path.is_file():
        saved = _load_json(variables_path)
        live = generate_variables(root, require_analysis_outputs=False)
        for key in ("sheaf_track_count", "pipeline_track_count", "imrad_manifest_rows"):
            if saved.get(key) != live.get(key):
                issues.append(f"manuscript variable {key!r} is stale: saved={saved.get(key)!r}, live={live.get(key)!r}")

    summary = _load_json(root / "output" / "data" / "si_tmaze_summary.json")
    stats = _load_json(root / "output" / "data" / "analysis_statistics.json")
    if summary and stats:
        if summary.get("mode") != stats.get("pymdp_mode"):
            issues.append(f"pymdp mode mismatch: summary={summary.get('mode')!r}, stats={stats.get('pymdp_mode')!r}")
        if summary.get("config_hash") != stats.get("pymdp_config_hash"):
            issues.append(
                f"pymdp config hash mismatch: summary={summary.get('config_hash')!r}, "
                f"stats={stats.get('pymdp_config_hash')!r}"
            )

    policy = _policy_comparison_restrictions(root)
    if set(policy["modes"]) != {"policy_inference", "state_inference"}:
        issues.append(f"policy comparison mode set invalid: {policy['modes']!r}")
    if policy["run_count"] < 4:
        issues.append(f"policy comparison run count too small: {policy['run_count']!r}")

    graph_world = _graph_world_restrictions(root)
    if not graph_world["steps_match"]:
        issues.append(
            "graph-world summary/trace mismatch: "
            f"summary steps={graph_world['steps']!r}, trace steps={graph_world['trace_steps']!r}"
        )
    if not graph_world["goal_reached"]:
        issues.append("graph-world summary does not record goal_reached=true")

    frame_count = _animation_frame_count(root)
    if frame_count < 2:
        issues.append(f"animation frame count too small: {frame_count}")

    lean = _lean_status(root)
    if not lean["all_proved"]:
        issues.append("Lean boundary is not fully proved")

    issues.extend(validate_configured_artifact_producers(root))

    from validation_spine import validate_validation_spine

    issues.extend(validate_validation_spine(root))

    from gates.claim_ledger import validate_typed_claim_evidence

    if not validate_typed_claim_evidence(root, allow_missing_certificate=True):
        issues.append("typed claim evidence failed")

    return issues


def _section_records(project_root: Path) -> list[dict[str, Any]]:
    ctx = load_sheaf_coverage_context(project_root)
    records: list[dict[str, Any]] = []
    by_id = {section.id: section for section in ctx.manifest.sections}
    for row in ctx.matrix.sections:
        section = by_id[row.section_id]
        records.append(
            {
                "id": section.id,
                "title": section.title,
                "imrad": section.imrad,
                "kind": section.kind,
                "compose": section.compose,
                "tracks": {
                    cell.track_id: {
                        "status": cell.status,
                        "path": cell.path,
                    }
                    for cell in row.cells
                    if cell.bound
                },
            }
        )
    return records


def _claim_records(root: Path) -> list[dict[str, Any]]:
    import yaml

    path = root / "data" / "claim_ledger.yaml"
    if not path.is_file():
        return []
    ledger = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    records: list[dict[str, Any]] = []
    for claim in ledger.get("claims") or []:
        records.append(
            {
                "id": claim.get("id"),
                "statement": claim.get("statement"),
                "path": claim.get("path"),
                "section": claim.get("section"),
                "tracks": claim.get("tracks") or [],
                "evidence": claim.get("evidence") or {},
            }
        )
    return records


def build_evidence_crosswalk(project_root: Path) -> dict[str, Any]:
    """Build a claim-to-artifact crosswalk from the typed claim ledger."""
    root = project_root.resolve()
    claims = []
    for claim in _claim_records(root):
        rel = str(claim.get("path") or "")
        artifact = root / rel
        claims.append(
            {
                **claim,
                "artifact_exists": artifact.exists(),
                "producer": ARTIFACT_PRODUCERS.get(rel, "manual"),
                "validation_gates": list(ARTIFACT_GATES.get(rel, ("validate_outputs",))),
            }
        )
    return {
        "schema": "template_active_inference.evidence_crosswalk.v1",
        "claim_count": len(claims),
        "claims": claims,
    }


def build_validation_dependency_graph(project_root: Path) -> dict[str, Any]:
    """Build script → artifact → manuscript/gate dependency records."""
    root = project_root.resolve()
    configured = _configured_analysis_scripts(root)
    claim_ids = _claims_by_path(root)
    artifacts: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, str]] = []
    for rel, producer in sorted(ARTIFACT_PRODUCERS.items()):
        consumers = list(ARTIFACT_CONSUMERS.get(rel, ()))
        gates = list(ARTIFACT_GATES.get(rel, ("validate_outputs",)))
        produced_by_configured_analysis = producer in configured
        artifacts[rel] = {
            "producer": producer,
            "exists": (root / rel).exists(),
            "produced_by_configured_analysis": produced_by_configured_analysis,
            "consumers": consumers,
            "validation_gates": gates,
            "claim_ids": sorted(claim_ids.get(rel, [])),
        }
        edges.append({"source": producer, "target": rel, "kind": "produces"})
        edges.extend({"source": rel, "target": consumer, "kind": "consumed_by"} for consumer in consumers)
        edges.extend({"source": rel, "target": gate, "kind": "validated_by"} for gate in gates)
    issues = validate_configured_artifact_producers(root, configured_scripts=configured)
    return {
        "schema": "template_active_inference.validation_dependency_graph.v1",
        "analysis_scripts": configured,
        "artifacts": artifacts,
        "edges": edges,
        "issues": issues,
    }


def validate_configured_artifact_producers(
    project_root: Path,
    *,
    configured_scripts: list[str] | None = None,
) -> list[str]:
    """Fail when required generated artifacts lack configured analysis producers."""
    root = project_root.resolve()
    configured = configured_scripts if configured_scripts is not None else _configured_analysis_scripts(root)
    issues: list[str] = []
    for rel, producer in sorted(ARTIFACT_PRODUCERS.items()):
        if producer not in configured:
            qualifier = " exists without" if (root / rel).exists() else " lacks"
            issues.append(f"required artifact {rel}{qualifier} configured producer {producer}")
    return issues


def build_semantic_gluing_certificate(project_root: Path) -> dict[str, Any]:
    """Build a JSON-serializable semantic certificate from live project state."""
    root = project_root.resolve()
    ctx = load_sheaf_coverage_context(root)
    issues = semantic_gluing_issues(root)
    variables = generate_variables(root, require_analysis_outputs=False)
    bernoulli_symbols = _gnn_symbols(root, "gnn/bernoulli_toy.gnn.md")
    si_symbols = _gnn_symbols(root, "gnn/si_tmaze.gnn.md")
    dependency_graph = build_validation_dependency_graph(root)
    policy = _policy_comparison_restrictions(root)
    graph_world = _graph_world_restrictions(root)
    pymdp_hash = _pymdp_hash_restrictions(root)
    lean = _lean_status(root)
    from validation_spine import validate_validation_spine

    return {
        "schema": SEMANTIC_SCHEMA,
        "ok": not issues,
        "issues": issues,
        "tracks": [
            {
                "id": tid,
                "renderer": spec.renderer,
                "optional": spec.optional,
                "order": spec.order,
            }
            for tid, spec in sorted(ctx.registry.tracks.items(), key=lambda item: item[1].order)
        ],
        "sections": _section_records(root),
        "shared_symbols": {
            "bernoulli": {var: bernoulli_symbols.get(var) for var in BERNOULLI_EXPECTED_TERMS},
            "si_tmaze": {var: si_symbols.get(var) for var in SI_EXPECTED_TERMS},
        },
        "artifact_sources": {
            "coverage_matrix": {
                "path": "output/data/sheaf_coverage_matrix.json",
                "exists": (root / "output" / "data" / "sheaf_coverage_matrix.json").exists(),
            },
            "si_summary": {
                "path": "output/data/si_tmaze_summary.json",
                "exists": (root / "output" / "data" / "si_tmaze_summary.json").exists(),
            },
            "analysis_statistics": {
                "path": "output/data/analysis_statistics.json",
                "exists": (root / "output" / "data" / "analysis_statistics.json").exists(),
            },
            "claim_ledger": {
                "path": "data/claim_ledger.yaml",
                "exists": (root / "data" / "claim_ledger.yaml").exists(),
            },
            "evidence_crosswalk": {
                "path": "output/data/sheaf_evidence_crosswalk.json",
                "exists": (root / "output" / "data" / "sheaf_evidence_crosswalk.json").exists(),
            },
            "dependency_graph": {
                "path": "output/data/validation_dependency_graph.json",
                "exists": (root / "output" / "data" / "validation_dependency_graph.json").exists(),
            },
        },
        "restrictions": {
            "coverage_missing": gray_cell_count(ctx.matrix),
            "section_count": len(ctx.manifest.sections),
            "track_count": len(ctx.registry.tracks),
            "claim_count": len(_claim_records(root)),
            "policy_comparison_run_count": policy["run_count"],
            "policy_comparison_modes": policy["modes"],
            "policy_comparison_horizons": policy["horizons"],
            "policy_comparison_goal_reached_count": policy["goal_reached_count"],
            "graph_world_steps_match": graph_world["steps_match"],
            "graph_world_goal_reached": graph_world["goal_reached"],
            "animation_frame_count": _animation_frame_count(root),
            "pymdp_mode_match": pymdp_hash["mode_match"],
            "pymdp_config_hash_match": pymdp_hash["config_hash_match"],
            "lean_all_proved": lean["all_proved"],
            "lean_proved_count": lean["proved_count"],
            "gnn_ontology_ok": not validate_all_gnn_ontology(root),
            "configured_artifact_producers_ok": not dependency_graph["issues"],
            "validation_spine_ok": not validate_validation_spine(root),
        },
        "artifact_graph": dependency_graph["artifacts"],
        "evidence_crosswalk": build_evidence_crosswalk(root),
        "claims": _claim_records(root),
        "manuscript_variables": variables,
    }


def write_semantic_gluing_certificate(
    project_root: Path,
    *,
    output_path: Path | None = None,
) -> Path:
    root = project_root.resolve()
    path = output_path or root / "output" / "data" / "sheaf_gluing_certificate.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = build_semantic_gluing_certificate(root)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_semantic_gluing_outputs(project_root: Path) -> dict[str, Path]:
    """Write semantic certificate, evidence crosswalk, and dependency graph outputs."""
    root = project_root.resolve()
    data_dir = root / "output" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    crosswalk_path = data_dir / "sheaf_evidence_crosswalk.json"
    dependency_path = data_dir / "validation_dependency_graph.json"
    certificate_path = data_dir / "sheaf_gluing_certificate.json"
    crosswalk_path.write_text(
        json.dumps(build_evidence_crosswalk(root), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    dependency_path.write_text(
        json.dumps(build_validation_dependency_graph(root), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    certificate_path.write_text(
        json.dumps(build_semantic_gluing_certificate(root), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "certificate": certificate_path,
        "crosswalk": crosswalk_path,
        "dependency_graph": dependency_path,
    }


def _stable_artifact_graph(payload: dict[str, Any]) -> dict[str, Any]:
    graph = payload.get("artifact_graph") or {}
    stable: dict[str, Any] = {}
    for rel, record in graph.items():
        if isinstance(record, dict):
            stable[rel] = {
                key: record.get(key)
                for key in ("producer", "produced_by_configured_analysis", "consumers", "validation_gates", "claim_ids")
            }
    return stable


def _stable_certificate_fields(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": payload.get("schema"),
        "tracks": payload.get("tracks"),
        "sections": payload.get("sections"),
        "shared_symbols": payload.get("shared_symbols"),
        "restrictions": payload.get("restrictions"),
        "artifact_graph": _stable_artifact_graph(payload),
    }


def validate_semantic_gluing(project_root: Path) -> list[str]:
    """Validate the live semantic certificate and its generated artifact."""
    root = project_root.resolve()
    issues = semantic_gluing_issues(root)
    path = root / "output" / "data" / "sheaf_gluing_certificate.json"
    if not path.is_file():
        issues.append("missing output/data/sheaf_gluing_certificate.json")
        return issues
    saved = _load_json(path)
    if saved.get("schema") != SEMANTIC_SCHEMA:
        issues.append(f"saved sheaf_gluing_certificate.json schema is not {SEMANTIC_SCHEMA}")
    if saved.get("ok") is not True:
        issues.append("saved sheaf_gluing_certificate.json is not ok")
    if saved.get("restrictions", {}).get("coverage_missing") != 0:
        issues.append("saved sheaf_gluing_certificate.json records missing coverage")
    live = build_semantic_gluing_certificate(root)
    if _stable_certificate_fields(saved) != _stable_certificate_fields(live):
        issues.append("saved sheaf_gluing_certificate.json is stale relative to live semantic fields")
    return issues
