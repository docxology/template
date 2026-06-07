"""Semantic sheaf-gluing and typed claim-evidence tests."""

from __future__ import annotations

import json
from pathlib import Path

from gate_support import ensure_gate_artifacts


def test_semantic_certificate_covers_tracks_symbols_and_variables(project_root: Path) -> None:
    from manuscript.sheaf.semantic import build_semantic_gluing_certificate

    ensure_gate_artifacts(project_root)
    cert = build_semantic_gluing_certificate(project_root)

    assert cert["schema"] == "template_active_inference.semantic_gluing.v2"
    assert cert["ok"] is True
    assert cert["manuscript_variables"]["sheaf_track_count"] == 33
    assert cert["shared_symbols"]["bernoulli"]["J"] == "CrossStreamCouplingPotential"
    assert cert["shared_symbols"]["si_tmaze"]["pi"] == "PolicyPosterior"
    assert cert["artifact_sources"]["si_summary"]["path"] == "output/data/si_tmaze_summary.json"
    assert cert["artifact_graph"]["output/data/si_graph_world_trace.json"]["producer"] == "simulate_si_graph_world.py"
    assert (
        cert["artifact_graph"]["output/data/sheaf_section_status_matrix.json"]["producer"]
        == "generate_sheaf_tracks.py"
    )
    assert cert["artifact_graph"]["output/reports/sheaf_render_log.json"]["producer"] == "generate_sheaf_tracks.py"
    assert (
        cert["artifact_graph"]["output/reports/visualization_quality_audit.json"]["producer"]
        == "generate_integration_audit.py"
    )
    assert (
        cert["artifact_graph"]["output/data/statistical_visualization_bridge.json"]["producer"]
        == "generate_integration_audit.py"
    )
    assert "results_si_tmaze" in cert["artifact_graph"]["output/data/si_policy_comparison.json"]["consumers"]
    assert cert["artifact_graph"]["output/data/pymdp_policy_posterior_grid.json"]["producer"] == "simulate_si_tmaze.py"
    assert cert["restrictions"]["animation_frame_count"] >= 3
    assert cert["restrictions"]["pymdp_runtime_unexpected_warning_count"] == 0
    assert cert["restrictions"]["policy_posterior_normalized"] is True
    assert cert["restrictions"]["policy_comparison_complete_grid"] is True
    assert cert["restrictions"]["section_status_all_bound_present"] is True
    assert cert["restrictions"]["section_status_all_sections_have_status"] is True
    assert cert["restrictions"]["section_status_cell_count"] > 0
    assert cert["restrictions"]["sheaf_render_log_all_events_ok"] is True
    assert cert["restrictions"]["visualization_quality_ok"] is True
    assert cert["restrictions"]["visualization_intent_metadata_complete"] is True
    assert cert["restrictions"]["visualization_paper_claims_complete"] is True
    assert cert["restrictions"]["visualization_figures_section_bound"] is True
    assert cert["restrictions"]["visualization_statistics_bridge_ok"] is True
    assert cert["restrictions"]["statistical_visualization_crosswalk_ok"] is True
    assert cert["restrictions"]["statistical_visualization_figures_referenced"] is True
    assert cert["restrictions"]["statistical_visualization_reference_sections_sheaf_bound"] is True
    assert cert["restrictions"]["statistical_visualization_reference_sections_visualization_bound"] is True
    tracks_by_id = {track["id"]: track for track in cert["tracks"]}
    assert tracks_by_id["prose"]["paper_role"] == "Narrative framing and argument flow"
    assert (
        tracks_by_id["visualization"]["paper_use"]
        == "Injects registry figures into section-specific evidence blocks."
    )

    methods_pymdp = next(section for section in cert["sections"] if section["id"] == "methods_pymdp")
    assert {
        "prose",
        "formalism",
        "pymdp",
        "interop",
        "gnn",
        "ontology",
        "visualization",
    } <= set(methods_pymdp["tracks"])


def test_semantic_gluing_rejects_wrong_si_ontology(project_root: Path) -> None:
    from manuscript.sheaf.semantic import validate_semantic_gluing

    ensure_gate_artifacts(project_root)
    ontology_path = project_root / "manuscript" / "sections" / "imrad" / "methods_pymdp" / "ontology.yaml"
    original = ontology_path.read_text(encoding="utf-8")
    try:
        ontology_path.write_text(original.replace("pi: PolicyPosterior", "pi: HiddenState"), encoding="utf-8")
        issues = validate_semantic_gluing(project_root)
        assert any("si_tmaze" in issue and "PolicyPosterior" in issue for issue in issues)
    finally:
        ontology_path.write_text(original, encoding="utf-8")


def test_semantic_certificate_is_written_as_generated_artifact(project_root: Path) -> None:
    from manuscript.sheaf.semantic import write_semantic_gluing_outputs

    ensure_gate_artifacts(project_root)
    paths = write_semantic_gluing_outputs(project_root)
    path = paths["certificate"]
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert path.relative_to(project_root).as_posix() == "output/data/sheaf_gluing_certificate.json"
    assert paths["crosswalk"].relative_to(project_root).as_posix() == "output/data/sheaf_evidence_crosswalk.json"
    assert (
        paths["dependency_graph"].relative_to(project_root).as_posix()
        == "output/data/validation_dependency_graph.json"
    )
    assert payload["ok"] is True
    assert payload["restrictions"]["coverage_missing"] == 0
    assert "si_graph_world_trace" in json.dumps(paths["crosswalk"].read_text(encoding="utf-8"))


def test_semantic_gluing_rejects_stale_saved_certificate(project_root: Path) -> None:
    from manuscript.sheaf.semantic import validate_semantic_gluing, write_semantic_gluing_outputs

    ensure_gate_artifacts(project_root)
    paths = write_semantic_gluing_outputs(project_root)
    original = paths["certificate"].read_text(encoding="utf-8")
    payload = json.loads(original)
    try:
        payload["artifact_graph"]["output/data/si_graph_world_trace.json"]["producer"] = "tests_only.py"
        paths["certificate"].write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

        issues = validate_semantic_gluing(project_root)
    finally:
        paths["certificate"].write_text(original, encoding="utf-8")

    assert any("stale" in issue or "producer" in issue for issue in issues)


def test_semantic_gluing_rejects_missing_or_malformed_saved_certificate(project_root: Path) -> None:
    from manuscript.sheaf.semantic import validate_semantic_gluing, write_semantic_gluing_outputs

    ensure_gate_artifacts(project_root)
    paths = write_semantic_gluing_outputs(project_root)
    certificate = paths["certificate"]
    original = certificate.read_text(encoding="utf-8")
    try:
        certificate.unlink()
        missing_issues = validate_semantic_gluing(project_root)
        assert any("missing output/data/sheaf_gluing_certificate.json" in issue for issue in missing_issues)

        payload = json.loads(original)
        payload["schema"] = "template_active_inference.semantic_gluing.v1"
        payload["ok"] = False
        payload["restrictions"]["coverage_missing"] = 1
        certificate.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        malformed_issues = validate_semantic_gluing(project_root)
        assert any("schema is not" in issue for issue in malformed_issues)
        assert any("is not ok" in issue for issue in malformed_issues)
        assert any("records missing coverage" in issue for issue in malformed_issues)
    finally:
        certificate.write_text(original, encoding="utf-8")


def test_dependency_graph_rejects_required_artifact_without_configured_producer(project_root: Path) -> None:
    from manuscript.sheaf.semantic import validate_configured_artifact_producers

    config_path = project_root / "manuscript" / "config.yaml"
    original = config_path.read_text(encoding="utf-8")
    try:
        config_path.write_text(original.replace("    - simulate_si_graph_world.py\n", ""), encoding="utf-8")
        issues = validate_configured_artifact_producers(project_root)
    finally:
        config_path.write_text(original, encoding="utf-8")

    assert any("si_graph_world_summary.json" in issue for issue in issues)


def test_dependency_graph_distinguishes_missing_from_unconfigured_existing(project_root: Path) -> None:
    from manuscript.sheaf.semantic import validate_configured_artifact_producers

    ensure_gate_artifacts(project_root)
    graph_summary = project_root / "output" / "data" / "si_graph_world_summary.json"
    original = graph_summary.read_text(encoding="utf-8")
    try:
        existing_issues = validate_configured_artifact_producers(project_root, configured_scripts=[])
        assert any("exists without configured producer" in issue for issue in existing_issues)

        graph_summary.unlink()
        missing_issues = validate_configured_artifact_producers(project_root, configured_scripts=[])
        assert any("si_graph_world_summary.json lacks configured producer" in issue for issue in missing_issues)
    finally:
        graph_summary.write_text(original, encoding="utf-8")


def test_semantic_gluing_rejects_mutated_policy_posterior(project_root: Path) -> None:
    from manuscript.sheaf.semantic import validate_semantic_gluing, write_semantic_gluing_outputs
    from simulation.si_artifacts import write_policy_comparison, write_policy_posterior_grid

    ensure_gate_artifacts(project_root)
    write_policy_comparison(project_root)
    posterior_path = write_policy_posterior_grid(project_root)
    write_semantic_gluing_outputs(project_root)
    original = posterior_path.read_text(encoding="utf-8")
    try:
        payload = json.loads(original)
        row = next(row for row in payload["rows"] if row["posterior_available"])
        row["q_pi"] = [0.7, 0.7]
        row["normalized"] = False
        payload["all_available_posteriors_normalized"] = False
        posterior_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        issues = validate_semantic_gluing(project_root)
    finally:
        posterior_path.write_text(original, encoding="utf-8")

    assert any("stale relative to live semantic fields" in issue for issue in issues)


def test_semantic_certificate_records_lean_graph_world_topology_witnesses(project_root: Path) -> None:
    from manuscript.sheaf.semantic import build_semantic_gluing_certificate

    ensure_gate_artifacts(project_root)
    cert = build_semantic_gluing_certificate(project_root)

    assert cert["ok"] is True
    assert cert["restrictions"]["lean_all_proved"] is True
    assert cert["restrictions"]["model_checking_all_passed"] is True


def test_typed_claim_evidence_rejects_wrong_expected_value(project_root: Path, tmp_path: Path) -> None:
    from gates.claim_ledger import validate_typed_claim_evidence

    ledger = tmp_path / "claim_ledger.yaml"
    ledger.write_text(
        "\n".join(
            [
                "claims:",
                "  - id: bad_sheaf_count",
                "    statement: Sheaf count is intentionally wrong.",
                "    path: output/data/manuscript_variables.json",
                "    evidence:",
                "      field: sheaf_track_count",
                "      equals: 999",
                "    tracks: [manuscript]",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    assert validate_typed_claim_evidence(project_root, ledger_path=ledger) is False


def test_typed_claim_evidence_supports_structured_predicates(tmp_path: Path) -> None:
    from gates.claim_ledger import validate_typed_claim_evidence

    data_dir = tmp_path / "output" / "data"
    data_dir.mkdir(parents=True)
    artifact = data_dir / "predicate_payload.json"
    artifact.write_text(
        json.dumps(
            {
                "modes": ["state_inference", "policy_inference"],
                "runs": [{"ok": True}, {"ok": True}],
                "score": 1.001,
            }
        ),
        encoding="utf-8",
    )
    ledger = tmp_path / "claim_ledger.yaml"
    ledger.write_text(
        "\n".join(
            [
                "claims:",
                "  - id: modes",
                "    statement: mode set",
                "    path: output/data/predicate_payload.json",
                "    tracks: [pymdp]",
                "    evidence:",
                "      field: modes",
                "      set_equals: [policy_inference, state_inference]",
                "  - id: run_count",
                "    statement: two runs",
                "    path: output/data/predicate_payload.json",
                "    tracks: [pymdp]",
                "    evidence:",
                "      field: runs",
                "      len_equals: 2",
                "  - id: approximate_score",
                "    statement: approximate score",
                "    path: output/data/predicate_payload.json",
                "    tracks: [pymdp]",
                "    evidence:",
                "      field: score",
                "      approx: 1.0",
                "      tolerance: 0.01",
                "  - id: all_ok",
                "    statement: all rows ok",
                "    path: output/data/predicate_payload.json",
                "    tracks: [pymdp]",
                "    evidence:",
                "      field: runs",
                "      all:",
                "        field: ok",
                "        equals: true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    assert validate_typed_claim_evidence(tmp_path, ledger_path=ledger) is True
    bad = ledger.read_text(encoding="utf-8").replace("len_equals: 2", "len_equals: 3")
    ledger.write_text(bad, encoding="utf-8")
    assert validate_typed_claim_evidence(tmp_path, ledger_path=ledger) is False


def test_validate_manuscript_checks_semantic_certificate(project_root: Path) -> None:
    from gates.validation import validate_manuscript
    from manuscript.sheaf.semantic import write_semantic_gluing_certificate

    ensure_gate_artifacts(project_root)
    write_semantic_gluing_certificate(project_root)
    checks = validate_manuscript(project_root)

    assert checks["semantic_sheaf_gluing"] is True
