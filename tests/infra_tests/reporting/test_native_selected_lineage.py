"""Real JSON projection cases; no native owner, tool or domain oracle is replaced."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.reporting.native_format_pdf_semantic_plan import PDFSemanticPlan
from infrastructure.reporting.native_oracle_selected_lineage import (
    classify_selected_native_lineage,
    selected_asset_lineage_residuals,
    selected_lineage_residuals,
)

SCOPE = "templates/template_code_project"
PROJECT = "projects/" + SCOPE


def _seal(body: dict[str, Any]) -> dict[str, Any]:
    body.pop("content_digest", None)
    return {**body, "content_digest": canonical_digest(body)}


def _binding(path: str, digest: str = "a") -> dict[str, Any]:
    return {"path": path, "sha256": digest * 64, "bytes": 100}


def _graphs(*, generated: bool = False, run: str = "original") -> tuple[dict[str, Any], dict[str, Any]]:
    common = {"scope": SCOPE, "source_binding": ["b" * 40, "c" * 64], "pipeline_run_id": run, "plan_digest": "d" * 64}
    source = _binding(PROJECT + "/manuscript/01.md")
    consumed = _binding(PROJECT + "/output/manuscript/01.md", "e" if generated else "a")
    row: dict[str, Any] = {"ordinal": 1, "source": source, "consumed": consumed}
    if generated:
        row.update(
            transformation="shared-uppercase-token-hydration",
            hydration={
                "occurrences": [
                    {
                        "ordinal": 1,
                        "key": "RESULT_MIN_ITERATIONS",
                        "resolved": True,
                        "source_start_byte": 0,
                        "source_end_byte": 25,
                        "output_start_byte": 0,
                        "output_end_byte": 2,
                        "replacement_sha256": "f" * 64,
                    }
                ]
            },
        )
    else:
        row["transformation"] = "exact-authored-source-body"
    analysis = _seal(
        {
            **common,
            "schema_version": "template-native-analysis-boundary-graph-v3",
            "unresolved_edges": [],
            "produced_current_bodies": [],
        }
    )
    hydration = _seal(
        {
            **common,
            "schema_version": "template-native-hydration-reconstruction-v3",
            "unresolved_edges": [],
            "ordered_inputs": [row],
        }
    )
    return analysis, hydration


def _code(analysis: dict[str, Any], hydration: dict[str, Any]) -> dict[str, Any]:
    row = hydration["ordered_inputs"][0]
    occurrence = {"source": row["source"], "consumed": row["consumed"], **row["hydration"]["occurrences"][0]}
    key = occurrence["key"]
    return _seal(
        {
            "scope": SCOPE,
            "source_binding": analysis["source_binding"],
            "pipeline_run_id": analysis["pipeline_run_id"],
            "analysis_digest": analysis["content_digest"],
            "hydration_digest": hydration["content_digest"],
            "values": [{"key": key, "payload_sha256": "f" * 64, "selected_occurrences": [occurrence]}],
            "registered_origin": {"actual_completed_write_and_consuming_read": "DATA fixture; no native capability"},
            "residuals": [f"consumed-value-native-location-link:{occurrence['source']['path']}:1:{key}"],
        }
    )


def test_authored_json_no_generated_does_not_acquire_hypothetical_obligations(tmp_path: Path) -> None:
    analysis, hydration = _graphs()
    path = tmp_path / "actual-checked-data-shape.json"
    path.write_text(json.dumps([analysis, hydration]))
    held = json.loads(path.read_text())
    result = classify_selected_native_lineage(*held)
    assert result["residuals"] == []
    assert result["selected_occurrences"] == []
    assert all(result["advisory_limits"].values())
    assert selected_lineage_residuals((result,), *held, reader_phase=False) == ()


def test_dynamic_input_external_registry_edge_is_preserved_exactly() -> None:
    analysis, hydration = _graphs()
    reason = "analysis-to-render-hydration-boundary-intervening-metadata-and-resource-custody"
    analysis["unresolved_edges"] = [reason]
    analysis = _seal(analysis)
    assert classify_selected_native_lineage(analysis, hydration)["residuals"] == [reason]


def test_only_exact_universal_descriptions_move_to_advisory() -> None:
    analysis, hydration = _graphs()
    advisory = classify_selected_native_lineage(analysis, hydration)["advisory_limits"]
    specific = advisory["analysis_api"][0] + ":projects/selected/actual.csv"
    analysis["unresolved_edges"] = [*advisory["analysis_api"], specific]
    hydration["unresolved_edges"] = list(advisory["hydration_api"])
    result = classify_selected_native_lineage(_seal(analysis), _seal(hydration))
    assert result["residuals"] == [specific]
    assert result["advisory_limits"] == advisory


def test_generated_occurrence_without_actual_domain_join_remains_specific() -> None:
    analysis, hydration = _graphs(generated=True)
    result = classify_selected_native_lineage(analysis, hydration)
    assert result["residuals"] == [
        "selected-generated-value-domain-origin-native-location:"
        + PROJECT
        + "/manuscript/01.md:1:RESULT_MIN_ITERATIONS"
    ]


def test_checked_scalar_meaning_still_has_actual_native_location_gap() -> None:
    analysis, hydration = _graphs(generated=True)
    value = _code(analysis, hydration)
    result = classify_selected_native_lineage(analysis, hydration, code_values=value)
    assert result["residuals"] == value["residuals"]
    assert result["selected_occurrences"] == value["values"][0]["selected_occurrences"]


def test_unknown_metadata_or_scientific_key_is_not_promoted_by_payload_equality() -> None:
    analysis, hydration = _graphs(generated=True)
    hydration["ordered_inputs"][0]["hydration"]["occurrences"][0]["key"] = "STABILITY_SCORE"
    hydration = _seal(hydration)
    assert classify_selected_native_lineage(analysis, hydration)["residuals"][0].endswith(":1:STABILITY_SCORE")


@pytest.mark.parametrize("field", ["source_start_byte", "output_end_byte", "replacement_sha256"])
def test_actual_code_occurrence_interval_or_binding_change_refuses(field: str) -> None:
    analysis, hydration = _graphs(generated=True)
    value = _code(analysis, hydration)
    value["values"][0]["selected_occurrences"][0][field] = "changed"
    with pytest.raises(ValueError, match="correspondence"):
        classify_selected_native_lineage(analysis, hydration, code_values=_seal(value))


def test_empty_producer_aggregate_cannot_clear_native_occurrence() -> None:
    analysis, hydration = _graphs(generated=True)
    value = _code(analysis, hydration)
    value["residuals"] = []
    value["status"] = "pass"
    with pytest.raises(ValueError, match="unresolved native occurrence"):
        classify_selected_native_lineage(analysis, hydration, code_values=_seal(value))


def test_missing_completed_origin_retains_keyed_refusal() -> None:
    analysis, hydration = _graphs(generated=True)
    value = _code(analysis, hydration)
    value["registered_origin"] = None
    result = classify_selected_native_lineage(analysis, hydration, code_values=_seal(value))
    assert "selected-generated-value-completed-origin-unavailable:RESULT_MIN_ITERATIONS" in result["residuals"]


def test_custom_selected_fragment_does_not_pass_from_equal_bytes() -> None:
    analysis, hydration = _graphs()
    hydration["ordered_inputs"][0]["transformation"] = "Source-selected-project-authored-hydration"
    hydration["ordered_inputs"][0]["project_hydration"] = {"algorithm": "Source-project-custom-v1"}
    result = classify_selected_native_lineage(analysis, _seal(hydration))
    assert result["residuals"] == ["selected-generated-fragment-lineage:" + PROJECT + "/output/manuscript/01.md"]


def test_source_selected_ancillary_verbatim_has_no_generated_value_obligation() -> None:
    analysis, hydration = _graphs()
    for graph in (analysis, hydration):
        graph["scope"] = "templates/template_template"
    for field in ("source", "consumed"):
        hydration["ordered_inputs"][0][field]["path"] = hydration["ordered_inputs"][0][field]["path"].replace(
            "template_code_project", "template_template"
        )
    hydration["ordered_inputs"][0]["transformation"] = "Source-selected-project-authored-hydration"
    hydration["ordered_inputs"][0]["project_hydration"] = {"algorithm": "Source-template-ancillary-verbatim-v1"}
    assert classify_selected_native_lineage(_seal(analysis), _seal(hydration))["residuals"] == []


def _figure_facts() -> dict[str, Any]:
    analysis, hydration = _graphs()
    analysis["produced_current_bodies"] = [
        {
            "producer_stage": "analysis:figure.py",
            "body": _binding(PROJECT + "/output/figures/actual.png"),
        }
    ]
    return classify_selected_native_lineage(_seal(analysis), hydration)


def _office(assets: list[dict[str, Any]]) -> dict[str, Any]:
    return {"office_complete_source": {"reference": {"figures": [{"source": row} for row in assets], "cover": None}}}


def test_unused_produced_figure_has_no_selected_consumption_obligation() -> None:
    facts = _figure_facts()
    assert facts["generated_figure_roles"]
    assert facts["residuals"] == []
    assert selected_asset_lineage_residuals(facts, "manuscript:docx", _office([])) == ()


def test_actual_consumed_figure_retains_domain_and_native_role_gap() -> None:
    facts = _figure_facts()
    binding = {key: facts["generated_figure_roles"][0]["body"][key] for key in ("path", "sha256")}
    reasons = selected_asset_lineage_residuals(facts, "manuscript:docx", _office([binding]))
    assert reasons == ("consumed-figure-domain-and-native-lineage:manuscript:docx:0:" + binding["path"],)


def test_consumed_figure_without_actual_completed_producer_has_specific_origin_gap() -> None:
    facts = _figure_facts()
    binding = {"path": PROJECT + "/output/figures/foreign.png", "sha256": "f" * 64}
    reasons = selected_asset_lineage_residuals(facts, "manuscript:docx", _office([binding]))
    assert reasons[0] == "consumed-figure-completed-origin-unavailable:manuscript:docx:0:" + binding["path"]
    assert reasons[1].startswith("consumed-figure-domain-and-native-lineage:")


def test_missing_asset_roster_is_not_declared_empty_or_complete() -> None:
    facts = _figure_facts()
    assert selected_asset_lineage_residuals(facts, "manuscript:pdf", {})[0].startswith(
        "actual-generated-asset-consumer-roster-unavailable:manuscript:pdf:"
    )


def test_changed_actual_consumed_figure_refuses() -> None:
    facts = _figure_facts()
    binding = {"path": PROJECT + "/output/figures/actual.png", "sha256": "f" * 64}
    with pytest.raises(ValueError, match="observed producer body"):
        selected_asset_lineage_residuals(facts, "manuscript:docx", _office([binding]))


def test_selected_external_generated_resource_is_not_ignored() -> None:
    facts = _figure_facts()
    binding = {"path": "projects/templates/other/output/figures/actual.png", "sha256": "a" * 64}
    assert selected_asset_lineage_residuals(facts, "manuscript:docx", _office([binding])) == (
        "selected-external-generated-asset-lineage-unjoined:manuscript:docx:0:" + binding["path"],
    )


def test_actual_pdf_and_browser_asset_rosters_keep_consumed_figures() -> None:
    facts = _figure_facts()
    binding = {"path": PROJECT + "/output/figures/actual.png", "sha256": "a" * 64}
    expected = "consumed-figure-domain-and-native-lineage:manuscript:pdf:ast.2:" + binding["path"]
    assert selected_asset_lineage_residuals(facts, "manuscript:pdf", {}, pdf=_pdf({"ast.2": binding})) == (expected,)
    browser = {
        "observation": {"asset_contract": {"schema_version": "template-native-browser-assets-v1", "assets": [binding]}}
    }
    assert selected_asset_lineage_residuals(facts, "manuscript:html", browser) == (
        "consumed-figure-domain-and-native-lineage:manuscript:html:0:" + binding["path"],
    )


def test_reader_requires_actual_distinct_current_core_and_physical_graph_bindings() -> None:
    analysis, hydration = _graphs()
    original = classify_selected_native_lineage(analysis, hydration)
    current_graph, current_hydration = _graphs(run="current")
    current_graph["plan_digest"] = "e" * 64
    current_hydration["plan_digest"] = "e" * 64
    current = classify_selected_native_lineage(
        _seal(current_graph),
        _seal(current_hydration),
        graph_artifacts={
            "analysis": {"path": "proof/current/analysis.json", "sha256": "f" * 64},
            "hydration": {"path": "proof/current/hydration.json", "sha256": "a" * 64},
        },
    )
    actual = {"current_pipeline_run_id": "current", "current_plan_digest": "e" * 64}
    assert (
        selected_lineage_residuals(
            (original, current), analysis, hydration, reader_phase=True, current_artifacts=actual
        )
        == ()
    )
    changed = copy.deepcopy(current)
    changed["pipeline_run_id"] = "original"
    with pytest.raises(ValueError, match="reused Original"):
        selected_lineage_residuals(
            (original, _seal(changed)), analysis, hydration, reader_phase=True, current_artifacts=actual
        )
    with pytest.raises(ValueError, match="fresh Current Core"):
        selected_lineage_residuals(
            (original, current),
            analysis,
            hydration,
            reader_phase=True,
            current_artifacts={**actual, "current_plan_digest": "a" * 64},
        )


@pytest.mark.parametrize("changed", ["source_binding", "analysis_digest", "hydration_digest"])
def test_changed_original_source_or_graph_digest_refuses(changed: str) -> None:
    analysis, hydration = _graphs()
    facts = classify_selected_native_lineage(analysis, hydration)
    facts[changed] = ["foreign", "foreign"] if changed == "source_binding" else "f" * 64
    with pytest.raises(ValueError):
        selected_lineage_residuals((_seal(facts),), analysis, hydration, reader_phase=False)


def test_status_or_fulfilled_metadata_is_not_phase_lineage_data() -> None:
    analysis, hydration = _graphs()
    with pytest.raises(ValueError, match="checked Source"):
        selected_lineage_residuals(({"status": "pass", "fulfilled": True},), analysis, hydration, reader_phase=False)


def _pdf(assets: dict[str, dict[str, str]]) -> dict[str, Any]:
    plan = {
        "schema_version": "template-native-pdf-semantic-source-plan-v1",
        "artifact_id": "manuscript:pdf",
        "source_ast_sha256": "f" * 64,
        "sources": [],
        "text": [],
        "notes": [],
        "occurrences": [{"identity": identity, "kind": "Image"} for identity in assets],
        "tables": [],
        "blockers": [],
    }
    return {
        "source_predicates": {
            "assets": assets,
            "source_plan": plan,
            "witness": {
                "source_plan_digest": canonical_digest(plan),
                "figures": {"figures": [], "findings": [], "blockers": []},
            },
        }
    }


def test_consumed_office_cover_has_its_own_generated_lineage_residual() -> None:
    facts = _figure_facts()
    binding = {"path": PROJECT + "/output/figures/actual.png", "sha256": "a" * 64}
    observer = _office([])
    observer["office_complete_source"]["reference"]["cover"] = {
        "source": binding,
        "consumed": {"path": "proof/frozen-cover.png", "sha256": "a" * 64},
        "alt": "actual configured cover",
    }
    assert selected_asset_lineage_residuals(facts, "manuscript:epub", observer) == (
        "consumed-figure-domain-and-native-lineage:manuscript:epub:cover:" + binding["path"],
    )


def test_office_figures_without_actual_cover_absence_do_not_declare_a_complete_roster() -> None:
    observer = _office([])
    del observer["office_complete_source"]["reference"]["cover"]
    assert selected_asset_lineage_residuals(_figure_facts(), "manuscript:epub", observer)[0].startswith(
        "actual-generated-asset-consumer-roster-unavailable:manuscript:epub:"
    )


@pytest.mark.parametrize("mode", ["refused", "missing-witness", "altered-plan", "selected-image-missing"])
def test_pdf_failure_empty_asset_return_is_not_a_complete_roster(mode: str) -> None:
    pdf = _pdf({})
    predicates = pdf["source_predicates"]
    if mode == "refused":
        predicates["witness"]["figures"]["blockers"] = ["actual asset compiler refused"]
    elif mode == "missing-witness":
        predicates["witness"] = {"blockers": ["actual projection refused"]}
    elif mode == "altered-plan":
        predicates["witness"]["source_plan_digest"] = "a" * 64
    else:
        predicates["source_plan"]["occurrences"] = [{"identity": "ast.2", "kind": "Image"}]
        predicates["witness"]["source_plan_digest"] = canonical_digest(predicates["source_plan"])
    assert selected_asset_lineage_residuals(_figure_facts(), "manuscript:pdf", {}, pdf=pdf)[0].startswith(
        "actual-generated-asset-consumer-roster-unavailable:manuscript:pdf:"
    )


def test_complete_bound_zero_figure_pdf_witness_establishes_actual_unused_output() -> None:
    facts = _figure_facts()
    assert selected_asset_lineage_residuals(facts, "manuscript:pdf", {}, pdf=_pdf({})) == ()
    scientific = _pdf({})["source_predicates"]
    scientific["semantic_plan"] = scientific.pop("source_plan")
    assert selected_asset_lineage_residuals(facts, "manuscript:pdf", {"scientific_pdf_source": scientific}) == ()


@pytest.mark.parametrize("image", [False, True])
def test_actual_live_pdf_semantic_plan_tuple_and_serialized_list_have_same_asset_closure(image: bool) -> None:
    binding = {"path": PROJECT + "/output/figures/actual.png", "sha256": "a" * 64}
    assets = {"ast.2": binding} if image else {}
    pdf = _pdf(assets)
    predicates = pdf["source_predicates"]
    source = predicates["source_plan"]
    live = PDFSemanticPlan(
        source["artifact_id"], source["source_ast_sha256"], (), (), (), tuple(source["occurrences"]), (), ()
    ).to_dict()
    assert isinstance(live["occurrences"], tuple)
    predicates["source_plan"] = live
    predicates["witness"]["source_plan_digest"] = canonical_digest(live)
    original = selected_asset_lineage_residuals(_figure_facts(), "manuscript:pdf", {}, pdf=pdf)
    held = json.loads(json.dumps(pdf))
    assert isinstance(held["source_predicates"]["source_plan"]["occurrences"], list)
    assert selected_asset_lineage_residuals(_figure_facts(), "manuscript:pdf", {}, pdf=held) == original
    assert bool(original) == image
