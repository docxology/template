"""Promoted roadmap-track artifact tests and negative controls."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from gate_support import ensure_gate_artifacts

# These tests regenerate heavy sheaf gluing + roadmap-promotion artifacts (the negative
# controls mutate generated output/ artifacts, defeating the bootstrap cache). They run
# ~33-75s locally and can exceed the CI-wide --timeout=120 on slower runners, so give the
# whole module a wider per-test ceiling (a marker overrides the CLI --timeout value).
pytestmark = pytest.mark.timeout(300)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _relative_posix(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def test_promoted_roadmap_artifacts_are_written_and_valid(project_root: Path) -> None:
    from roadmap_tracks import (
        validate_formal_interop_artifacts,
        validate_integration_audit_artifacts,
        validate_sheaf_track_artifacts,
        validate_toy_sweep_artifacts,
        write_formal_interop_artifacts,
        write_integration_audit_artifacts,
        write_sheaf_track_artifacts,
        write_toy_sweep_artifacts,
    )

    ensure_gate_artifacts(project_root)
    toy = write_toy_sweep_artifacts(project_root)
    formal = write_formal_interop_artifacts(project_root)
    audit = write_integration_audit_artifacts(project_root)
    sheaf = write_sheaf_track_artifacts(project_root)

    assert _relative_posix(toy["sensitivity"], project_root) == "output/data/sensitivity_sweep.json"
    assert _relative_posix(toy["analytical_assumptions"], project_root) == (
        "output/data/analytical_assumption_index.json"
    )
    assert _relative_posix(toy["state_space_catalog"], project_root) == "output/data/state_space_catalog.json"
    assert _relative_posix(toy["causal_ablation"], project_root) == "output/data/causal_ablation_matrix.json"
    assert _relative_posix(formal["model_checking"], project_root) == ("output/reports/model_checking_witnesses.json")
    assert _relative_posix(formal["proof_extraction"], project_root) == "output/data/proof_extraction_index.json"
    assert _relative_posix(audit["gate_index"], project_root) == "output/data/validation_gate_index.json"
    assert _relative_posix(audit["artifact_diffoscope"], project_root) == ("output/reports/artifact_diffoscope.json")
    assert _relative_posix(audit["artifact_license"], project_root) == ("output/reports/artifact_license_audit.json")
    assert _relative_posix(audit["release_notes"], project_root) == "output/reports/release_notes_evidence.json"
    assert _relative_posix(sheaf["semantic"], project_root) == "output/data/sheaf_gluing_certificate.json"
    assert _relative_posix(sheaf["dependency"], project_root) == "output/data/validation_dependency_graph.json"
    assert _relative_posix(sheaf["evidence_fields"], project_root) == "output/data/evidence_field_index.json"
    assert _relative_posix(sheaf["release_bundle"], project_root) == "output/reports/release_bundle_manifest.json"
    assert _relative_posix(sheaf["theorem_traceability"], project_root) == (
        "output/data/theorem_traceability_matrix.json"
    )
    assert _relative_posix(sheaf["proof_dependency_graph"], project_root) == ("output/data/proof_dependency_graph.json")
    assert _relative_posix(sheaf["state_transition_table"], project_root) == ("output/data/state_transition_table.json")
    assert _relative_posix(sheaf["ablation_sensitivity_report"], project_root) == (
        "output/reports/ablation_sensitivity_report.json"
    )
    assert _relative_posix(sheaf["release_attestation"], project_root) == "output/reports/release_attestation.json"
    topology = _load(project_root / "output" / "data" / "si_graph_world_topology_sweep.json")
    lean_graph = _load(project_root / "output" / "reports" / "lean_graph_world_inventory.json")
    topology_ids = {row["topology"] for row in topology["rows"]}
    witnessed_ids = {row["topology"] for row in lean_graph["rows"] if row.get("kind") == "topology"}
    assert "loop5" in topology_ids
    assert topology_ids == witnessed_ids
    assert lean_graph["all_topologies_witnessed"] is True
    assert validate_toy_sweep_artifacts(project_root) == []
    assert validate_formal_interop_artifacts(project_root) == []
    write_integration_audit_artifacts(project_root)
    assert validate_integration_audit_artifacts(project_root) == []
    write_sheaf_track_artifacts(project_root)
    assert validate_sheaf_track_artifacts(project_root) == []


def test_toy_sweep_negative_controls(project_root: Path) -> None:
    from roadmap_tracks import validate_toy_sweep_artifacts, write_toy_sweep_artifacts

    ensure_gate_artifacts(project_root)
    write_toy_sweep_artifacts(project_root)
    sensitivity = project_root / "output" / "data" / "sensitivity_sweep.json"
    assumptions = project_root / "output" / "data" / "analytical_assumption_index.json"
    uncertainty = project_root / "output" / "data" / "uncertainty_summary.json"
    benchmark = project_root / "output" / "data" / "toy_benchmark_matrix.json"
    observable = project_root / "output" / "data" / "analytical_observable_sweep.json"
    topology_traces = project_root / "output" / "data" / "si_graph_world_topology_traces.json"
    state_catalog = project_root / "output" / "data" / "state_space_catalog.json"
    causal_ablation = project_root / "output" / "data" / "causal_ablation_matrix.json"
    originals = {
        path: path.read_text(encoding="utf-8")
        for path in (
            sensitivity,
            assumptions,
            uncertainty,
            benchmark,
            observable,
            topology_traces,
            state_catalog,
            causal_ablation,
        )
    }
    try:
        data = _load(sensitivity)
        data["rows"] = data["rows"][:-1]
        data["row_count"] = len(data["rows"])
        data["complete_grid"] = False
        _write(sensitivity, data)
        assert any("grid is incomplete" in issue for issue in validate_toy_sweep_artifacts(project_root))
        sensitivity.write_text(originals[sensitivity], encoding="utf-8")

        data = _load(assumptions)
        data["equation_ids"] = ["eq:entangled_joint"]
        data["all_equations_indexed"] = False
        _write(assumptions, data)
        assert any("equation set is incomplete" in issue for issue in validate_toy_sweep_artifacts(project_root))
        assumptions.write_text(originals[assumptions], encoding="utf-8")

        data = _load(uncertainty)
        data["rows"][0]["posterior_sum"] = 1.5
        data["rows"][0]["normalized"] = False
        data["all_normalized"] = False
        _write(uncertainty, data)
        assert any("unnormalized" in issue for issue in validate_toy_sweep_artifacts(project_root))
        uncertainty.write_text(originals[uncertainty], encoding="utf-8")

        data = _load(benchmark)
        data["models"] = ["bernoulli_ising"]
        data["all_models_complete"] = False
        _write(benchmark, data)
        assert any("model set is incomplete" in issue for issue in validate_toy_sweep_artifacts(project_root))
        benchmark.write_text(originals[benchmark], encoding="utf-8")

        data = _load(observable)
        data["rows"][0]["residual"] = 0.01
        data["max_abs_residual"] = 0.01
        _write(observable, data)
        assert any("residual exceeds tolerance" in issue for issue in validate_toy_sweep_artifacts(project_root))
        observable.write_text(originals[observable], encoding="utf-8")

        data = _load(topology_traces)
        data["rows"][0]["trace_steps"] = 999
        data["rows"][0]["trace_summary_agree"] = False
        data["all_trace_summary_agree"] = False
        _write(topology_traces, data)
        assert any(
            "topology_traces.json summary/trace mismatch" in issue
            for issue in validate_toy_sweep_artifacts(project_root)
        )
        topology_traces.write_text(originals[topology_traces], encoding="utf-8")

        data = _load(state_catalog)
        data["rows"][0]["finite"] = False
        data["all_finite"] = False
        _write(state_catalog, data)
        assert any("state_space_catalog.json" in issue for issue in validate_toy_sweep_artifacts(project_root))
        state_catalog.write_text(originals[state_catalog], encoding="utf-8")

        data = _load(causal_ablation)
        data["rows"] = data["rows"][:-1]
        data["row_count"] = len(data["rows"])
        data["complete_grid"] = False
        _write(causal_ablation, data)
        assert any("causal_ablation_matrix.json" in issue for issue in validate_toy_sweep_artifacts(project_root))
    finally:
        for path, text in originals.items():
            path.write_text(text, encoding="utf-8")


def test_toy_sweep_uses_measured_policy_and_topology_trace_artifacts(project_root: Path) -> None:
    from roadmap_tracks import write_toy_sweep_artifacts
    from simulation.si_artifacts import write_policy_comparison, write_policy_posterior_grid

    ensure_gate_artifacts(project_root)
    write_policy_comparison(project_root)
    write_policy_posterior_grid(project_root)
    paths = write_toy_sweep_artifacts(project_root)

    policy_grid = _load(paths["policy_grid"])
    efe_terms = _load(paths["efe_terms"])
    observable = _load(paths["analytical_observable"])
    topology = _load(paths["graph_topology"])
    topology_traces = _load(paths["graph_topology_traces"])

    assert policy_grid["source"] == "output/data/si_policy_comparison.json"
    assert all(row["measured"] for row in policy_grid["rows"])
    assert {row["observable"] for row in observable["rows"]} >= {
        "same_state_probability",
        "posterior_correlation",
        "joint_entropy",
    }
    assert all(row["terms_available"] or row["fallback_reason"] for row in efe_terms["rows"])
    assert topology["topology_count"] >= 3
    assert topology_traces["topology_count"] == topology["topology_count"]
    assert topology_traces["all_trace_summary_agree"] is True
    assert efe_terms["schema"] == "template_active_inference.si_efe_values.v1"


def test_formal_interop_negative_controls(project_root: Path) -> None:
    from roadmap_tracks import validate_formal_interop_artifacts, write_formal_interop_artifacts

    ensure_gate_artifacts(project_root)
    write_formal_interop_artifacts(project_root)
    model_checking = project_root / "output" / "reports" / "model_checking_witnesses.json"
    interop = project_root / "output" / "data" / "interop_roundtrip_report.json"
    ontology_alias = project_root / "output" / "data" / "ontology_alias_index.json"
    topology_sweep = project_root / "output" / "data" / "si_graph_world_topology_sweep.json"
    lean_graph = project_root / "output" / "reports" / "lean_graph_world_inventory.json"
    proof = project_root / "output" / "data" / "proof_extraction_index.json"
    lean_file = project_root / "lean" / "TemplateActiveInference" / "SophisticatedInference.lean"
    originals = {
        path: path.read_text(encoding="utf-8")
        for path in (model_checking, interop, ontology_alias, topology_sweep, lean_graph, proof, lean_file)
    }
    try:
        data = _load(model_checking)
        data["rows"][0]["counterexamples"] = ["start cannot reach goal"]
        data["rows"][0]["passed"] = False
        data["all_passed"] = False
        _write(model_checking, data)
        assert any("finite counterexample" in issue for issue in validate_formal_interop_artifacts(project_root))
        model_checking.write_text(originals[model_checking], encoding="utf-8")

        data = _load(interop)
        data["rows"][0]["lossless"] = False
        data["all_lossless"] = False
        _write(interop, data)
        assert any("not lossless" in issue for issue in validate_formal_interop_artifacts(project_root))
        interop.write_text(originals[interop], encoding="utf-8")

        data = _load(ontology_alias)
        data["conflicts"] = ["x: A != B"]
        data["no_conflicts"] = False
        _write(ontology_alias, data)
        assert any("conflicting aliases" in issue for issue in validate_formal_interop_artifacts(project_root))
        ontology_alias.write_text(originals[ontology_alias], encoding="utf-8")

        lean_file.write_text(originals[lean_file] + "\naxiom bad_placeholder : True\n", encoding="utf-8")
        write_formal_interop_artifacts(project_root)
        assert any("not fully proved" in issue for issue in validate_formal_interop_artifacts(project_root))
        lean_file.write_text(originals[lean_file], encoding="utf-8")
        lean_graph.write_text(originals[lean_graph], encoding="utf-8")

        data = _load(topology_sweep)
        data["rows"].append(
            {
                "goal_reached": True,
                "node_count": 6,
                "steps": 6,
                "summary_trace_agreement": True,
                "topology": "unwitnessed6",
                "trace_steps": 6,
            }
        )
        data["topology_count"] = len(data["rows"])
        _write(topology_sweep, data)
        assert any("topology sweep" in issue for issue in validate_formal_interop_artifacts(project_root))
        topology_sweep.write_text(originals[topology_sweep], encoding="utf-8")

        data = _load(proof)
        data["rows"][0]["extracted"] = False
        data["all_extracted"] = False
        _write(proof, data)
        assert any("proof_extraction_index.json" in issue for issue in validate_formal_interop_artifacts(project_root))
    finally:
        for path, text in originals.items():
            path.write_text(text, encoding="utf-8")
        write_formal_interop_artifacts(project_root)


def test_integration_audit_negative_controls(project_root: Path) -> None:
    from roadmap_tracks import (
        validate_integration_audit_artifacts,
        write_integration_audit_artifacts,
        write_sheaf_track_artifacts,
    )

    ensure_gate_artifacts(project_root)
    write_integration_audit_artifacts(project_root)
    # Establish this test's own preconditions: artifact_diffoscope / artifact_provenance are
    # written by the sheaf-track pass and their rows derive from a fresh provenance build.
    # ensure_gate_artifacts() is run-once per session, so a prior test could leave these stale;
    # regenerate them here so the diffoscope-drift control below has a populated row to mutate.
    write_sheaf_track_artifacts(project_root)
    paths = [
        project_root / "output" / "reports" / "stale_artifact_report.json",
        project_root / "output" / "data" / "manuscript_token_provenance.json",
        project_root / "output" / "data" / "figure_source_map.json",
        project_root / "output" / "reports" / "scope_boundary_audit.json",
        project_root / "output" / "reports" / "adversarial_audit.json",
        project_root / "output" / "reports" / "manuscript_staleness_report.json",
        project_root / "output" / "reports" / "artifact_diffoscope.json",
        project_root / "output" / "reports" / "artifact_license_audit.json",
        project_root / "output" / "reports" / "release_notes_evidence.json",
    ]
    originals = {path: path.read_text(encoding="utf-8") for path in paths}
    try:
        stale = paths[0]
        data = _load(stale)
        data["rows"][0]["sha256"] = "0" * 64
        _write(stale, data)
        assert any("hash mismatch" in issue for issue in validate_integration_audit_artifacts(project_root))
        stale.write_text(originals[stale], encoding="utf-8")

        tokens = paths[1]
        data = _load(tokens)
        data["all_tokens_mapped"] = False
        _write(tokens, data)
        assert any("unmapped tokens" in issue for issue in validate_integration_audit_artifacts(project_root))
        tokens.write_text(originals[tokens], encoding="utf-8")

        figure_source = paths[2]
        data = _load(figure_source)
        data["rows"][0]["mapped"] = False
        data["all_figures_mapped"] = False
        _write(figure_source, data)
        assert any("unmapped figures" in issue for issue in validate_integration_audit_artifacts(project_root))
        figure_source.write_text(originals[figure_source], encoding="utf-8")

        scope = paths[3]
        data = _load(scope)
        data["all_current_claims_toy"] = False
        data["scope_boundary_status"] = "scope_leak"
        _write(scope, data)
        assert any("scope leakage" in issue for issue in validate_integration_audit_artifacts(project_root))
        scope.write_text(originals[scope], encoding="utf-8")

        adversarial = paths[4]
        data = _load(adversarial)
        data["rows"][0]["expected_failure"] = False
        data["all_expected_failures_documented"] = False
        _write(adversarial, data)
        assert any("expected failures" in issue for issue in validate_integration_audit_artifacts(project_root))
        adversarial.write_text(originals[adversarial], encoding="utf-8")

        staleness = paths[5]
        data = _load(staleness)
        data["rows"][0]["expected"] = "definitely stale"
        _write(staleness, data)
        assert any(
            "manuscript_staleness_report.json is stale" in issue
            for issue in validate_integration_audit_artifacts(project_root)
        )
        staleness.write_text(originals[staleness], encoding="utf-8")

        diffoscope = paths[6]
        data = _load(diffoscope)
        data["rows"][0]["equal"] = False
        data["all_equal"] = False
        _write(diffoscope, data)
        assert any(
            "artifact_diffoscope.json records artifact drift" in issue
            for issue in validate_integration_audit_artifacts(project_root)
        )
        diffoscope.write_text(originals[diffoscope], encoding="utf-8")

        license_audit = paths[7]
        data = _load(license_audit)
        data["rows"][0]["license_safe"] = False
        data["all_license_safe"] = False
        _write(license_audit, data)
        assert any(
            "artifact_license_audit.json records unsafe artifacts" in issue
            for issue in validate_integration_audit_artifacts(project_root)
        )
        license_audit.write_text(originals[license_audit], encoding="utf-8")

        release_notes = paths[8]
        data = _load(release_notes)
        data["rows"][0]["passed"] = False
        data["all_notes_source_backed"] = False
        _write(release_notes, data)
        assert any(
            "release_notes_evidence.json has unsupported notes" in issue
            for issue in validate_integration_audit_artifacts(project_root)
        )
    finally:
        for path, text in originals.items():
            path.write_text(text, encoding="utf-8")


def test_cross_track_symbol_table_binds_type_shape_and_section_ontology(project_root: Path) -> None:
    from roadmap_tracks.integration_audit import build_cross_track_symbol_table

    ensure_gate_artifacts(project_root)
    table = build_cross_track_symbol_table(project_root)
    pi_row = next(row for row in table["rows"] if row["model"] == "si_tmaze" and row["symbol"] == "pi")
    assert table["all_consistent"] is True
    assert pi_row["shape"] == [2, 1]
    assert pi_row["dtype"] == "float"
    assert pi_row["gnn_term"] == "PolicyPosterior"
    assert pi_row["section_ontology_term"] == "PolicyPosterior"

    ontology_path = project_root / "manuscript" / "sections" / "imrad" / "methods_pymdp" / "ontology.yaml"
    original = ontology_path.read_text(encoding="utf-8")
    try:
        ontology_path.write_text(original.replace("pi: PolicyPosterior", "pi: HiddenState"), encoding="utf-8")
        drifted = build_cross_track_symbol_table(project_root)
        drifted_pi = next(row for row in drifted["rows"] if row["model"] == "si_tmaze" and row["symbol"] == "pi")
        assert drifted["all_consistent"] is False
        assert drifted_pi["term_consistent"] is False
    finally:
        ontology_path.write_text(original, encoding="utf-8")


def test_promoted_scripts_are_configured_between_validation_spine_and_hydration(project_root: Path) -> None:
    from orchestration.pipeline_manifest import DEFAULT_ANALYSIS_SCRIPTS

    configured = yaml.safe_load((project_root / "manuscript" / "config.yaml").read_text(encoding="utf-8"))["analysis"][
        "scripts"
    ]
    promoted = [
        "generate_toy_sweep_tracks.py",
        "generate_formal_interop_tracks.py",
        "generate_integration_audit.py",
        "generate_sheaf_tracks.py",
    ]

    assert configured == [step.script for step in DEFAULT_ANALYSIS_SCRIPTS]
    assert configured.index("generate_validation_spine.py") < configured.index(promoted[0])
    assert configured.index(promoted[-1]) < configured.index("z_generate_manuscript_variables.py")


def test_proof_extraction_source_is_per_file(project_root: Path) -> None:
    """proof_extraction rows must carry their REAL Lean source file, not one hardcoded path."""
    from roadmap_tracks.formal_interop import build_proof_extraction_index

    index = build_proof_extraction_index(project_root)
    rows = index["rows"]
    by_name = {row["theorem"]: row for row in rows}
    # ising_coupling_sum_zero lives in BernoulliToy.lean, not SophisticatedInference.lean.
    assert "ising_coupling_sum_zero" in by_name, "expected the Bernoulli coupling theorem"
    assert by_name["ising_coupling_sum_zero"]["source"].endswith("BernoulliToy.lean")
    # Provenance is genuinely per-file: more than one distinct source across the inventory.
    assert len({row["source"] for row in rows}) >= 2
    # The hardcoded literal is gone; each row reports a real extracted leading tactic
    # (e.g. ising_coupling_sum_zero is proved by `decide`).
    assert "proof_dependency" not in rows[0]
    assert by_name["ising_coupling_sum_zero"]["leading_tactic"] == "decide"


def test_promoted_claims_have_falsifiable_negative_controls(project_root: Path) -> None:
    """Mutate a ROW (leaving the summary boolean true) and assert the gate still fails.

    These three validators re-derive their aggregate from rows, so a contradicted row cannot
    hide under a stale `true` summary. Mutating the row (not the bit) proves the gate tests
    artifact truth, not mere sensitivity to summary tampering.
    """
    import json

    from roadmap_tracks import validate_integration_audit_artifacts, validate_toy_sweep_artifacts

    def break_producer(data: dict) -> None:
        data["rows"][0]["configured"] = False  # contradicts all_complete, which we leave True
        data["all_complete"] = True

    def break_efe(data: dict) -> None:
        data["rows"][0]["terms_available"] = True
        data["rows"][0]["terms"] = {"values": []}  # claims terms but ships none
        data["all_rows_explained"] = True

    def break_invariant(data: dict) -> None:
        data["rows"][0]["passed"] = False  # a real invariant violation
        data["all_passed"] = True

    cases = [
        (
            project_root / "output" / "reports" / "producer_completeness.json",
            break_producer,
            validate_integration_audit_artifacts,
            "producer_completeness.json is incomplete",
        ),
        (
            project_root / "output" / "data" / "si_efe_terms.json",
            break_efe,
            validate_toy_sweep_artifacts,
            "si_efe_terms.json has unexplained EFE rows",
        ),
        (
            project_root / "output" / "reports" / "graph_world_invariants.json",
            break_invariant,
            validate_toy_sweep_artifacts,
            "graph_world_invariants.json records a failing invariant",
        ),
    ]
    for path, mutate, validator, expected_issue in cases:
        assert path.is_file(), f"missing artifact {path}"
        original = path.read_text(encoding="utf-8")
        try:
            data = json.loads(original)
            assert all(expected_issue not in issue for issue in validator(project_root)), (
                f"{path.name}: expected a clean baseline before mutation"
            )
            mutate(data)
            path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            issues = validator(project_root)
            assert any(expected_issue in issue for issue in issues), (
                f"{path.name}: gate did not catch a failing ROW under a true summary"
            )
        finally:
            path.write_text(original, encoding="utf-8")
