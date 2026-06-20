from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

from analysis import (
    artifact_markdown_tables,
    configured_field_counts,
    configured_field_inventory,
    generate_artifacts,
    write_cover_overview_figure,
    write_configured_field_matrix,
    write_field_origin_summary,
    write_provenance_trace_map,
    write_quality_gate_matrix,
    write_section_configuration_heatmap,
    write_section_token_allocation_figure,
    write_token_density_figure,
    write_token_injection_flow_figure,
)
from composition import (
    build_authoring_obligation_table,
    build_audit_rule_table,
    build_design_principle_table,
    build_evaluation_criteria_table,
    build_failure_mode_table,
    build_imrad_sections,
    build_method_protocol_table,
    build_pipeline_phase_table,
    build_section_plan_table,
    build_section_title_table,
    build_token_inventory_table,
    build_quality_probe_table,
    section_title_variables,
)
from config import load_madlib_config
from tokens import generate_token_plan
from .helpers import base_payload, write_config


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_section_conditions_disable_section_body(tmp_path: Path) -> None:
    write_config(tmp_path, base_payload())
    config = load_madlib_config(tmp_path)
    plan = generate_token_plan(config)

    sections = build_imrad_sections(config, plan)

    assert "disabled by `madlib.section_conditions.discussion`" in sections["DISCUSSION_BODY"]
    assert "complete IMRAD manuscript" in sections["ABSTRACT_BODY"]


def test_markdown_tables_include_live_plan(tmp_path: Path) -> None:
    write_config(tmp_path, base_payload())
    config = load_madlib_config(tmp_path)
    plan = generate_token_plan(config)

    section_table = build_section_plan_table(config, plan)
    inventory_table = build_token_inventory_table(plan)

    assert "| discussion | Discussion: Accountability Boundaries for Generated Prose | False | 0 |" in section_table
    assert "`FIRST_ADJECTIVE`" in inventory_table
    assert "madlib.lexicon.adjectives" in inventory_table

    field_inventory = configured_field_inventory(config, plan)
    field_counts = configured_field_counts(config, field_inventory)

    assert {"path": "madlib.seed", "origin": "explicit", "scope": "schema", "summary": "7"} in field_inventory
    assert any(row["path"] == "madlib.visualizations.enabled" for row in field_inventory)
    assert field_counts["explicit"] > 0
    assert field_counts["defaulted"] > 0


def test_protocol_title_and_audit_tables_are_generated(tmp_path: Path) -> None:
    write_config(tmp_path, base_payload())
    config = load_madlib_config(tmp_path)

    assert "Methods: Test Protocol" in build_section_title_table(config)
    assert "MadlibConfig" in build_method_protocol_table(config)
    assert "Track configured field origins" in build_method_protocol_table(config)
    assert "Review selection invariants" in build_method_protocol_table(config)
    assert "Generate evidence tables and figures" in build_method_protocol_table(config)
    assert "Align claims with evidence ledger" in build_method_protocol_table(config)
    assert "Configuration owns prose choices" in build_design_principle_table(config)
    assert "Forks must add validators" in build_design_principle_table(config)
    assert "Review packet is a method artifact" in build_design_principle_table(config)
    assert "Schema parse" in build_pipeline_phase_table(config)
    assert "Evidence and visualization emission" in build_pipeline_phase_table(config)
    assert "Review packet assembly" in build_pipeline_phase_table(config)
    assert "Placeholder survival" in build_quality_probe_table(config)
    assert "Method completeness" in build_quality_probe_table(config)
    assert "Digest invariant review" in build_quality_probe_table(config)
    assert "Review generated claims" in build_authoring_obligation_table(config)
    assert "Assemble reviewer packet" in build_authoring_obligation_table(config)
    assert "Every placeholder resolves" in build_audit_rule_table(config)
    assert "Every method protocol row identifies action, evidence, and output" in build_audit_rule_table(
        config
    )
    assert "Placeholder resolution" in build_evaluation_criteria_table(config)
    assert "Unresolved placeholder" in build_failure_mode_table(config)
    assert "Fork without validators" in build_failure_mode_table(config)
    assert "Review packet incompleteness" in build_failure_mode_table(config)
    assert section_title_variables(config)["TITLE_METHODS"] == "Methods: Test Protocol"


def test_generated_methods_body_explains_method_contract(tmp_path: Path) -> None:
    write_config(tmp_path, base_payload())
    config = load_madlib_config(tmp_path)
    plan = generate_token_plan(config)

    methods = build_imrad_sections(config, plan)["METHODS_BODY"]

    assert "deterministic digest recipe" in methods
    assert "explicit YAML path" in methods
    assert "loader-defaulted path" in methods
    assert "slot-to-section allocation" in methods
    assert "visual audit figures" in methods
    assert "quality probes" in methods
    assert "review scenario" in methods
    assert "Method invariants" in methods
    assert "Claim-ledger alignment" in methods
    assert "reviewer packet" in methods
    assert "claim-boundary contract" in methods
    assert "human-review handoff" in methods
    assert "Fork migration" in methods


def test_generate_artifacts_writes_data_reports_and_figure(tmp_path: Path) -> None:
    write_config(tmp_path, base_payload())

    artifacts = generate_artifacts(tmp_path)

    assert artifacts["token_inventory"].is_file()
    assert artifacts["section_plan"].is_file()
    assert artifacts["configured_field_inventory"].is_file()
    assert artifacts["injection_trace"].is_file()
    assert artifacts["summary"].read_text(encoding="utf-8").startswith("# Test Madlib")
    assert artifacts["configured_field_summary"].is_file()
    assert artifacts["cover_overview"].is_file()
    assert artifacts["figure"].is_file()
    assert artifacts["configured_field_matrix"].is_file()
    assert artifacts["section_configuration_heatmap"].is_file()
    assert artifacts["field_origin_summary"].is_file()
    assert artifacts["token_injection_flow"].is_file()
    assert artifacts["section_token_allocation"].is_file()
    assert artifacts["provenance_trace_map"].is_file()
    assert artifacts["quality_gate_matrix"].is_file()
    assert artifacts["figure_registry"].is_file()

    token_inventory = json.loads(artifacts["token_inventory"].read_text(encoding="utf-8"))
    field_inventory = json.loads(artifacts["configured_field_inventory"].read_text(encoding="utf-8"))
    trace = json.loads(artifacts["injection_trace"].read_text(encoding="utf-8"))

    assert token_inventory[0]["variable_name"] == "FIRST_ADJECTIVE"
    assert any(row["path"] == "madlib.seed" and row["origin"] == "explicit" for row in field_inventory)
    assert trace["provenance"]["FIRST_ADJECTIVE"]["category"] == "adjectives"
    registry = json.loads(artifacts["figure_registry"].read_text(encoding="utf-8"))
    assert registry["fig:madlib-cover-overview"]["filename"] == "madlib_cover_overview.png"
    assert registry["fig:token-density"]["filename"] == "token_density.png"
    assert registry["fig:token-injection-flow"]["filename"] == "token_injection_flow.png"
    assert registry["fig:section-token-allocation"]["filename"] == "section_token_allocation.png"
    assert registry["fig:provenance-trace-map"]["filename"] == "provenance_trace_map.png"
    assert registry["fig:quality-gate-matrix"]["filename"] == "quality_gate_matrix.png"
    assert registry["fig:configured-field-matrix"]["filename"] == "configured_field_matrix.png"
    assert registry["fig:section-configuration-heatmap"]["filename"] == "section_configuration_heatmap.png"
    assert registry["fig:field-origin-summary"]["filename"] == "field_origin_summary.png"
    section_plan = json.loads(artifacts["section_plan"].read_text(encoding="utf-8"))
    assert "madlib.seed" in section_plan["explicit_paths"]
    assert "madlib.visualizations.enabled" in section_plan["defaulted_paths"]
    assert section_plan["configured_field_counts"]["visualized"] == 7
    assert section_plan["method_protocol"][0]["output"] == "MadlibConfig"
    assert section_plan["evaluation_criteria"][0]["gate"] == "tests"
    assert section_plan["failure_modes"][0]["name"] == "Unresolved placeholder"
    assert section_plan["design_principles"][0]["name"] == "Configuration owns prose choices"
    assert section_plan["pipeline_phases"][0]["output_artifact"] == "MadlibConfig"
    assert section_plan["quality_probes"][0]["artifact"] == "output/manuscript"
    assert section_plan["authoring_obligations"][0]["review_surface"] == "output/manuscript"


def test_artifact_markdown_tables_match_generation(tmp_path: Path) -> None:
    write_config(tmp_path, base_payload())
    artifacts = generate_artifacts(tmp_path)

    tables = artifact_markdown_tables(tmp_path)

    assert "SECTION_PLAN_TABLE" in tables
    assert "TOKEN_INVENTORY_TABLE" in tables
    assert "CONFIGURED_FIELD_TABLE" in tables
    assert "CONFIGURED_FIELD_SUMMARY_TABLE" in tables
    assert "CONFIGURATION_FIGURES" in tables
    assert "CONFIGURED_FIELD_FIGURES" in tables
    assert "METHODS_FIGURES" in tables
    assert "RESULTS_FIGURES" in tables
    assert "EVALUATION_FIGURES" in tables
    assert "METHOD_PROTOCOL_TABLE" in tables
    assert "DESIGN_PRINCIPLE_TABLE" in tables
    assert "PIPELINE_PHASE_TABLE" in tables
    assert "AUDIT_RULE_TABLE" in tables
    assert "EVALUATION_CRITERIA_TABLE" in tables
    assert "QUALITY_PROBE_TABLE" in tables
    assert "FAILURE_MODE_TABLE" in tables
    assert "AUTHORING_OBLIGATION_TABLE" in tables
    assert "FIRST_ADJECTIVE" in tables["TOKEN_INVENTORY_TABLE"]
    assert "madlib.seed" in tables["CONFIGURED_FIELD_TABLE"]
    assert "Deterministic token-injection flow" in tables["METHODS_FIGURES"]
    assert "Section token allocation" in tables["RESULTS_FIGURES"]
    assert "Configured field origin matrix" in tables["CONFIGURED_FIELD_FIGURES"]
    assert "Quality gate matrix" in tables["EVALUATION_FIGURES"]

    registry = json.loads(artifacts["figure_registry"].read_text(encoding="utf-8"))
    figure_labels = _figure_labels_from_tables(tables)
    assert figure_labels == {
        "fig:configured-field-matrix",
        "fig:field-origin-summary",
        "fig:provenance-trace-map",
        "fig:quality-gate-matrix",
        "fig:section-configuration-heatmap",
        "fig:section-token-allocation",
        "fig:token-density",
        "fig:token-injection-flow",
    }
    assert figure_labels.issubset(set(registry))
    for label in figure_labels:
        figure_path = tmp_path / "output" / "figures" / registry[label]["filename"]
        assert figure_path.is_file(), label


def test_write_token_density_figure_handles_minimal_plan(tmp_path: Path) -> None:
    write_config(tmp_path, base_payload())
    config = load_madlib_config(tmp_path)
    plan = generate_token_plan(config)

    figure = write_token_density_figure(plan, tmp_path / "density.png")
    field_inventory = configured_field_inventory(config, plan)
    field_counts = configured_field_counts(config, field_inventory)
    cover = write_cover_overview_figure(config, plan, field_counts, tmp_path / "cover.png")
    flow = write_token_injection_flow_figure(config, plan, tmp_path / "flow.png")
    allocation = write_section_token_allocation_figure(config, plan, tmp_path / "allocation.png")
    provenance = write_provenance_trace_map(config, plan, tmp_path / "provenance.png")
    gates = write_quality_gate_matrix(config, tmp_path / "gates.png")
    matrix = write_configured_field_matrix(field_inventory, tmp_path / "matrix.png")
    heatmap = write_section_configuration_heatmap(config, plan, tmp_path / "heatmap.png")
    summary = write_field_origin_summary(field_counts, tmp_path / "summary.png")

    for path in (figure, cover, flow, allocation, provenance, gates, matrix, heatmap, summary):
        assert path.is_file()
        assert _png_is_nonblank(path)


def test_project_cover_config_points_to_generated_file() -> None:
    config = yaml.safe_load((PROJECT_ROOT / "manuscript" / "config.yaml").read_text(encoding="utf-8"))

    assert config["paper"]["cover"]["image"] == "figures/madlib_cover_overview.png"
    artifacts = generate_artifacts(PROJECT_ROOT)
    cover_path = PROJECT_ROOT / "output" / config["paper"]["cover"]["image"]

    assert artifacts["cover_overview"] == cover_path
    assert _png_is_nonblank(cover_path)


def test_project_config_declares_expanded_method_surface() -> None:
    config = yaml.safe_load((PROJECT_ROOT / "manuscript" / "config.yaml").read_text(encoding="utf-8"))
    madlib = config["madlib"]

    protocol_names = {row["name"] for row in madlib["method_protocol"]}
    phase_names = {row["name"] for row in madlib["pipeline_phases"]}
    failure_names = {row["name"] for row in madlib["failure_modes"]}
    claim_text = " ".join(madlib["contribution_claims"])

    assert len(madlib["method_protocol"]) >= 18
    assert "Track field origin" in protocol_names
    assert "Declare review scenario" in protocol_names
    assert "Record selection invariants" in protocol_names
    assert "Align claims with evidence ledger" in protocol_names
    assert "Assemble reviewer packet" in protocol_names
    assert "Document fork migration" in protocol_names
    assert "Generate visual audit surface" in protocol_names
    assert "Manuscript hydration" in phase_names
    assert "Invariant review" in phase_names
    assert "Claim-ledger alignment" in phase_names
    assert "Review packet assembly" in phase_names
    assert "Fork contract documentation" in phase_names
    assert "Visualization emission" in phase_names
    assert "Fork without validators" in failure_names
    assert "Review packet incompleteness" in failure_names
    assert "generated Methods section" in claim_text
    assert "review handoff" in claim_text


def test_project_docs_and_claim_ledger_describe_review_packet_contract() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    standalone = (PROJECT_ROOT / "STANDALONE.md").read_text(encoding="utf-8")
    manuscript_readme = (PROJECT_ROOT / "manuscript" / "README.md").read_text(encoding="utf-8")
    todo = (PROJECT_ROOT / "TODO.md").read_text(encoding="utf-8")
    tests_agents = (PROJECT_ROOT / "tests" / "AGENTS.md").read_text(encoding="utf-8")
    claim_ledger = yaml.safe_load((PROJECT_ROOT / "data" / "claim_ledger.yaml").read_text(encoding="utf-8"))
    claims = {claim["claim_id"]: claim for claim in claim_ledger["claims"]}

    assert "review packet" in readme.lower() or "reviewer packet" in readme.lower()
    assert "Token-selection invariants" in readme
    assert "Fork Migration Checklist" in readme
    assert "Stage 04 validators" in readme
    assert "output/reports/output_statistics.json" in readme
    assert "Assemble a review packet" in standalone
    assert "Review-packet handoff" in manuscript_readme
    assert "claim-ledger evidence" in todo
    assert "output/reports/output_statistics.json" in tests_agents
    assert "digest-invariant-contract" in claims
    assert "review-packet-method-artifact" in claims
    assert "fork-migration-documentation" in claims
    review_value = claims["review-packet-method-artifact"]["value"]
    for required_surface in (
        "output/manuscript",
        "output/pdf",
        "output/web",
        "output/slides",
        "output/figures",
        "output/data",
        "output/reports",
        "output/reports/output_statistics.json",
    ):
        assert required_surface in review_value
        assert required_surface in readme or required_surface in manuscript_readme


def _png_is_nonblank(path: Path) -> bool:
    import matplotlib.image as mpimg

    pixels = mpimg.imread(path)
    return bool(pixels.size and float(pixels.max()) > float(pixels.min()))


def _figure_labels_from_tables(tables: dict[str, str]) -> set[str]:
    keys = ("METHODS_FIGURES", "RESULTS_FIGURES", "CONFIGURATION_FIGURES", "EVALUATION_FIGURES")
    return {
        match
        for key in keys
        for match in re.findall(r"#(fig:[A-Za-z0-9-]+)", tables[key])
    }
