"""Promoted roadmap-track artifact tests and negative controls."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from gate_support import ensure_gate_artifacts, temporary_json_mutation, temporary_text_mutation

# These tests regenerate heavy sheaf gluing + roadmap-promotion artifacts (the negative
# controls mutate generated output/ artifacts, defeating the bootstrap cache). They run
# ~33-75s locally but ubuntu CI runners have been observed ~3.5x slower, so give the whole
# module a wide per-test ceiling (a marker overrides the CLI --timeout value). 600s covers
# the heaviest negative control on the slowest leg without masking a real hang.
pytestmark = pytest.mark.timeout(600)


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
    figure_source_map = _load(audit["figure_source_map"])
    scope_boundary = _load(audit["scope_boundary"])
    assert figure_source_map["all_figures_have_claim_lanes"] is True
    assert figure_source_map["all_claim_lanes_valid"] is True
    assert all(row["claim_lanes"] for row in figure_source_map["rows"])
    assert scope_boundary["all_required_scope_categories_present"] is True
    assert scope_boundary["all_future_rows_non_live"] is True
    assert scope_boundary["all_blocked_contexts_non_live"] is True
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

    def break_sensitivity(data: dict) -> None:
        data["rows"] = data["rows"][:-1]
        data["row_count"] = len(data["rows"])
        data["complete_grid"] = False

    def break_assumptions(data: dict) -> None:
        data["equation_ids"] = ["eq:entangled_joint"]
        data["all_equations_indexed"] = False

    def break_uncertainty(data: dict) -> None:
        data["rows"][0]["posterior_sum"] = 1.5
        data["rows"][0]["normalized"] = False
        data["all_normalized"] = False

    def break_benchmark(data: dict) -> None:
        data["models"] = ["bernoulli_ising"]
        data["all_models_complete"] = False

    def break_observable(data: dict) -> None:
        data["rows"][0]["residual"] = 0.01
        data["max_abs_residual"] = 0.01

    def break_topology_traces(data: dict) -> None:
        data["rows"][0]["trace_steps"] = 999
        data["rows"][0]["trace_summary_agree"] = False
        data["all_trace_summary_agree"] = False

    def break_state_catalog(data: dict) -> None:
        data["rows"][0]["finite"] = False
        data["all_finite"] = False

    def break_causal_ablation(data: dict) -> None:
        data["rows"] = data["rows"][:-1]
        data["row_count"] = len(data["rows"])
        data["complete_grid"] = False

    cases = (
        (sensitivity, break_sensitivity, "grid is incomplete"),
        (assumptions, break_assumptions, "equation set is incomplete"),
        (uncertainty, break_uncertainty, "unnormalized"),
        (benchmark, break_benchmark, "model set is incomplete"),
        (observable, break_observable, "residual exceeds tolerance"),
        (topology_traces, break_topology_traces, "topology_traces.json summary/trace mismatch"),
        (state_catalog, break_state_catalog, "state_space_catalog.json"),
        (causal_ablation, break_causal_ablation, "causal_ablation_matrix.json"),
    )
    for path, mutate, expected in cases:
        with temporary_json_mutation(path, mutate):
            assert any(expected in issue for issue in validate_toy_sweep_artifacts(project_root)), path.name


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
        "ising_spin_correlation",
        "joint_entropy",
    }
    ising_rows = [row for row in observable["rows"] if row["observable"] == "ising_spin_correlation"]
    assert ising_rows
    assert all(row["equation_id"] == "eq:ising_spin_correlation" for row in ising_rows)
    assert all(abs(float(row["closed_form"]) - float(row["empirical"])) <= 1e-9 for row in ising_rows)
    assert all(row["terms_available"] or row["fallback_reason"] for row in efe_terms["rows"])
    assert topology["topology_count"] >= 3
    assert "diamond5" in {row["topology"] for row in topology["rows"]}
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
    ontology_profile = project_root / "output" / "data" / "ontology_profile_matrix.json"
    gnn_lint = project_root / "output" / "reports" / "gnn_lint_report.json"
    topology_sweep = project_root / "output" / "data" / "si_graph_world_topology_sweep.json"
    proof = project_root / "output" / "data" / "proof_extraction_index.json"
    lean_file = project_root / "lean" / "TemplateActiveInference" / "SophisticatedInference.lean"

    def break_model_checking(data: dict) -> None:
        data["rows"][0]["counterexamples"] = ["start cannot reach goal"]
        data["rows"][0]["passed"] = False
        data["all_passed"] = False

    def break_interop(data: dict) -> None:
        data["rows"][0]["lossless"] = False
        data["all_lossless"] = False

    def break_ontology_alias(data: dict) -> None:
        data["conflicts"] = ["x: A != B"]
        data["no_conflicts"] = False

    def break_gnn_lint(data: dict) -> None:
        data["rows"][0]["shape"] = []
        data["rows"][0]["shape_declared"] = True
        data["all_variables_mapped_once"] = True

    def break_ontology_profile(data: dict) -> None:
        data["rows"] = [row for row in data["rows"] if row.get("profile_kind") != "toy_benchmark_model"]
        data["all_mapped_once"] = True

    def break_topology_sweep(data: dict) -> None:
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

    def break_proof(data: dict) -> None:
        data["rows"][0]["extracted"] = False
        data["all_extracted"] = False

    cases = (
        (model_checking, break_model_checking, "finite counterexample"),
        (interop, break_interop, "not lossless"),
        (ontology_alias, break_ontology_alias, "conflicting aliases"),
        (gnn_lint, break_gnn_lint, "type, shape, ontology, or round-trip rows"),
        (ontology_profile, break_ontology_profile, "ontology_profile_matrix.json"),
        (topology_sweep, break_topology_sweep, "topology sweep"),
        (proof, break_proof, "proof_extraction_index.json"),
    )
    for path, mutate, expected in cases:
        with temporary_json_mutation(path, mutate):
            assert any(expected in issue for issue in validate_formal_interop_artifacts(project_root)), path.name

    try:
        with temporary_text_mutation(lean_file, lambda text: text + "\naxiom bad_placeholder : True\n"):
            write_formal_interop_artifacts(project_root)
            assert any("not fully proved" in issue for issue in validate_formal_interop_artifacts(project_root))
    finally:
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
    paths = {
        "stale": project_root / "output" / "reports" / "stale_artifact_report.json",
        "tokens": project_root / "output" / "data" / "manuscript_token_provenance.json",
        "figure_source": project_root / "output" / "data" / "figure_source_map.json",
        "claim_audit": project_root / "output" / "reports" / "claim_evidence_audit.json",
        "gate_index": project_root / "output" / "data" / "validation_gate_index.json",
        "scope": project_root / "output" / "reports" / "scope_boundary_audit.json",
        "visualization_quality": project_root / "output" / "reports" / "visualization_quality_audit.json",
        "adversarial": project_root / "output" / "reports" / "adversarial_audit.json",
        "staleness": project_root / "output" / "reports" / "manuscript_staleness_report.json",
        "diffoscope": project_root / "output" / "reports" / "artifact_diffoscope.json",
        "license_audit": project_root / "output" / "reports" / "artifact_license_audit.json",
        "release_notes": project_root / "output" / "reports" / "release_notes_evidence.json",
    }

    def break_stale(data: dict) -> None:
        data["rows"][0]["sha256"] = "0" * 64

    def break_tokens(data: dict) -> None:
        data["all_tokens_mapped"] = False

    def break_figure_source(data: dict) -> None:
        data["rows"][0]["mapped"] = False
        data["all_figures_mapped"] = False

    def break_figure_claim_lanes(data: dict) -> None:
        data["rows"][0]["claim_lanes"] = []
        data["rows"][0]["claim_lane_count"] = 0
        data["all_figures_have_claim_lanes"] = True
        data["all_claim_lanes_valid"] = True

    def break_claim_audit(data: dict) -> None:
        data["rows"][0]["substantive"] = True
        data["rows"][0]["predicate"] = ""
        data["all_claims_typed"] = True

    def break_gate_index(data: dict) -> None:
        data["rows"][0]["declared_outputs"] = []
        data["all_indexed"] = True

    def break_scope(data: dict) -> None:
        data["rows"][0]["current_result_toy_only"] = False
        data["rows"][0]["scope_category"] = "blocked_llm"
        data["all_current_claims_toy"] = True
        data["scope_boundary_status"] = "toy_only_pass"

    def break_visualization_claim_lanes(data: dict) -> None:
        data["rows"][0]["claim_lanes"] = []
        data["rows"][0]["claim_lane_count"] = 0
        data["rows"][0]["claim_lanes_valid"] = True
        data["all_figures_have_claim_lanes"] = True
        data["all_claim_lanes_valid"] = True

    def break_adversarial(data: dict) -> None:
        data["rows"][0]["expected_failure"] = False
        data["all_expected_failures_documented"] = False

    def break_staleness(data: dict) -> None:
        data["rows"][0]["expected"] = "definitely stale"

    def break_diffoscope(data: dict) -> None:
        data["rows"][0]["equal"] = False
        data["all_equal"] = False

    def break_license_audit(data: dict) -> None:
        data["rows"][0]["license_safe"] = False
        data["all_license_safe"] = False

    def break_release_notes(data: dict) -> None:
        data["rows"][0]["passed"] = False
        data["all_notes_source_backed"] = False

    cases = (
        ("stale", break_stale, "hash mismatch"),
        ("tokens", break_tokens, "unmapped tokens"),
        ("figure_source", break_figure_source, "unmapped figures"),
        ("figure_source", break_figure_claim_lanes, "incomplete claim lanes"),
        ("claim_audit", break_claim_audit, "untyped claims"),
        ("gate_index", break_gate_index, "unindexed gates"),
        ("scope", break_scope, "scope leakage"),
        ("visualization_quality", break_visualization_claim_lanes, "incomplete claim-lane coverage"),
        ("adversarial", break_adversarial, "expected failures"),
        ("staleness", break_staleness, "manuscript_staleness_report.json is stale"),
        ("diffoscope", break_diffoscope, "artifact_diffoscope.json records artifact drift"),
        ("license_audit", break_license_audit, "artifact_license_audit.json records unsafe artifacts"),
        ("release_notes", break_release_notes, "release_notes_evidence.json has unsupported notes"),
    )
    for artifact_key, mutate, expected in cases:
        with temporary_json_mutation(paths[artifact_key], mutate):
            assert any(expected in issue for issue in validate_integration_audit_artifacts(project_root)), artifact_key


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
    with temporary_text_mutation(
        ontology_path,
        lambda text: text.replace("pi: PolicyPosterior", "pi: HiddenState"),
    ):
        drifted = build_cross_track_symbol_table(project_root)
        drifted_pi = next(row for row in drifted["rows"] if row["model"] == "si_tmaze" and row["symbol"] == "pi")
        assert drifted["all_consistent"] is False
        assert drifted_pi["term_consistent"] is False


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


def test_scholarship_matrix_has_row_level_negative_control(project_root: Path) -> None:
    from roadmap_tracks import validate_scholarship_source_matrix, write_sheaf_track_artifacts

    ensure_gate_artifacts(project_root)
    write_sheaf_track_artifacts(project_root)
    path = project_root / "output" / "data" / "scholarship_source_matrix.json"

    def break_scholarship_row(data: dict) -> None:
        assert validate_scholarship_source_matrix(project_root) == []
        data["rows"][0]["cited_in_manuscript"] = False
        data["rows"][0]["connected"] = True
        data["all_sources_connected"] = True

    with temporary_json_mutation(path, break_scholarship_row):
        assert any("disconnected source rows" in issue for issue in validate_scholarship_source_matrix(project_root))


def test_promoted_claims_have_falsifiable_negative_controls(project_root: Path) -> None:
    """Mutate a ROW (leaving the summary boolean true) and assert the gate still fails.

    These three validators re-derive their aggregate from rows, so a contradicted row cannot
    hide under a stale `true` summary. Mutating the row (not the bit) proves the gate tests
    artifact truth, not mere sensitivity to summary tampering.
    """
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

    def break_diffoscope(data: dict) -> None:
        # A row reports the live artifact differs from its provenance hash, yet the
        # summary bit is left true. The validator must re-derive all_equal from rows.
        data["rows"][0]["equal"] = False
        data["all_equal"] = True

    def break_figure_source_map(data: dict) -> None:
        # Inject a fabricated, non-existent SOURCE-CODE path (src/**, not output/**)
        # while claiming the row is mapped. The validator must re-check the path on
        # the filesystem rather than trust the stored mapped/all_figures_mapped bits.
        data["rows"][0]["sources"] = ["src/__fabricated_does_not_exist__.py"]
        data["rows"][0]["mapped"] = True
        data["all_figures_mapped"] = True

    def break_figure_claim_lanes(data: dict) -> None:
        # A figure with source data but no claim lane is invisible to the claim
        # surface even if the aggregate flags remain forged true.
        data["rows"][0]["claim_lanes"] = []
        data["rows"][0]["claim_lane_count"] = 0
        data["all_figures_have_claim_lanes"] = True
        data["all_claim_lanes_valid"] = True

    def break_scope_category(data: dict) -> None:
        # Keep the summary green while making a blocked context look live.
        row = next(row for row in data["rows"] if row.get("scope_category") == "blocked_llm")
        row["blocked_context"] = False
        row["non_live_context"] = False
        data["all_blocked_contexts_non_live"] = True
        data["scope_boundary_status"] = "toy_only_pass"

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
        (
            project_root / "output" / "reports" / "artifact_diffoscope.json",
            break_diffoscope,
            validate_integration_audit_artifacts,
            "artifact_diffoscope.json records artifact drift",
        ),
        (
            project_root / "output" / "data" / "figure_source_map.json",
            break_figure_source_map,
            validate_integration_audit_artifacts,
            "figure_source_map.json has unmapped figures",
        ),
        (
            project_root / "output" / "data" / "figure_source_map.json",
            break_figure_claim_lanes,
            validate_integration_audit_artifacts,
            "figure_source_map.json has incomplete claim lanes",
        ),
        (
            project_root / "output" / "reports" / "scope_boundary_audit.json",
            break_scope_category,
            validate_integration_audit_artifacts,
            "scope_boundary_audit.json records empirical scope leakage",
        ),
    ]
    for path, mutate, validator, expected_issue in cases:
        assert path.is_file(), f"missing artifact {path}"
        assert all(expected_issue not in issue for issue in validator(project_root)), (
            f"{path.name}: expected a clean baseline before mutation"
        )
        with temporary_json_mutation(path, mutate):
            issues = validator(project_root)
            assert any(expected_issue in issue for issue in issues), (
                f"{path.name}: gate did not catch a failing ROW under a true summary"
            )
