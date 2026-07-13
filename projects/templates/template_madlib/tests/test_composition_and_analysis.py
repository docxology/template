from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

from src.analysis import generate_artifacts
from src.analysis_fields import configured_field_counts, configured_field_inventory
from src.analysis_figures import (
    write_configured_field_matrix,
    write_cover_overview_figure,
    write_field_origin_summary,
    write_provenance_trace_map,
    write_quality_gate_matrix,
    write_section_configuration_heatmap,
    write_section_token_allocation_figure,
    write_token_density_figure,
    write_token_injection_flow_figure,
)
from src.markdown_tables import artifact_markdown_tables
from src.composition import (
    build_authoring_obligation_table,
    build_audit_rule_table,
    build_configured_field_summary_table,
    build_configured_field_table,
    build_configuration_figure_markdown,
    build_contribution_table,
    build_design_principle_table,
    build_evaluation_criteria_table,
    build_evaluation_figure_markdown,
    build_failure_mode_table,
    build_imrad_sections,
    build_method_protocol_table,
    build_methods_figure_markdown,
    build_pipeline_phase_table,
    build_provenance_matrix_table,
    build_results_figure_markdown,
    build_section_plan_table,
    build_section_title_table,
    build_token_inventory_table,
    build_quality_probe_table,
    section_title_variables,
)
from src.config import load_madlib_config
from src.tokens import generate_token_plan
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
    assert "Every method protocol row identifies action, evidence, and output" in build_audit_rule_table(config)
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


def test_claim_ledger_doi_claim_matches_live_config_publication_fields() -> None:
    """Bind the DOI boundary claim's text to the live config values it describes.

    Regression guard: `data/claim_ledger.yaml` once asserted DOIs were "blank
    for this exemplar" long after `manuscript/config.yaml`'s `publication.doi`
    and `publication.version_doi` were populated with real, deposited Zenodo
    records. That drift was invisible to CI because the ledger tests only
    checked claim-id/path-substring presence, never the claim's asserted
    content against the live config it cites. This test fails if the two
    diverge again in either direction: a real DOI in config that the ledger
    still calls blank, or a blank config DOI that the ledger claims is live.
    """
    config = yaml.safe_load((PROJECT_ROOT / "manuscript" / "config.yaml").read_text(encoding="utf-8"))
    publication = config["publication"]
    live_doi = publication.get("doi", "")
    live_version_doi = publication.get("version_doi", "")

    claim_ledger = yaml.safe_load((PROJECT_ROOT / "data" / "claim_ledger.yaml").read_text(encoding="utf-8"))
    claims = {claim["claim_id"]: claim for claim in claim_ledger["claims"]}
    assert "live-standalone-doi-published" in claims
    doi_claim_value = claims["live-standalone-doi-published"]["value"]

    doi_is_live = bool(live_doi) and bool(live_version_doi)
    assert doi_is_live, "config.yaml publication DOIs are blank; update the claim ledger if this exemplar is unpublished"
    # The claim must actually cite the live DOI values, not just assert they exist.
    assert live_doi in doi_claim_value
    assert live_version_doi in doi_claim_value
    # And it must not still describe DOIs as blank/unpublished.
    assert "blank" not in doi_claim_value.lower()


def _png_is_nonblank(path: Path) -> bool:
    import matplotlib.image as mpimg

    pixels = mpimg.imread(path)
    return bool(pixels.size and float(pixels.max()) > float(pixels.min()))


def _figure_labels_from_tables(tables: dict[str, str]) -> set[str]:
    keys = ("METHODS_FIGURES", "RESULTS_FIGURES", "CONFIGURATION_FIGURES", "EVALUATION_FIGURES")
    return {match for key in keys for match in re.findall(r"#(fig:[A-Za-z0-9-]+)", tables[key])}


# ---------------------------------------------------------------------------
# build_methods_figure_markdown disabled paths
# ---------------------------------------------------------------------------


def test_methods_figure_markdown_when_visualizations_disabled(tmp_path: Path) -> None:
    """When visualizations.enabled=False the methods figure returns a disabled notice."""
    payload = base_payload()
    payload["madlib"]["visualizations"] = {"enabled": False}
    write_config(tmp_path, payload)
    config = load_madlib_config(tmp_path)

    result = build_methods_figure_markdown(config)

    assert "disabled" in result.lower()
    assert "token_injection_flow.png" not in result


def test_methods_figure_markdown_when_injection_flow_flag_false(tmp_path: Path) -> None:
    """When token_injection_flow=False the methods figure returns a disabled notice."""
    payload = base_payload()
    payload["madlib"]["visualizations"] = {"enabled": True, "token_injection_flow": False}  # nosec B105
    write_config(tmp_path, payload)
    config = load_madlib_config(tmp_path)

    result = build_methods_figure_markdown(config)

    assert "disabled" in result.lower()
    assert "token_injection_flow.png" not in result


def test_methods_figure_markdown_when_enabled(tmp_path: Path) -> None:
    """When all visualizations are enabled the methods figure markdown is present."""
    write_config(tmp_path, base_payload())
    config = load_madlib_config(tmp_path)

    result = build_methods_figure_markdown(config)

    assert "token_injection_flow.png" in result
    assert "fig:token-injection-flow" in result


# ---------------------------------------------------------------------------
# build_results_figure_markdown disabled / partial paths
# ---------------------------------------------------------------------------


def test_results_figure_markdown_density_always_present(tmp_path: Path) -> None:
    """token_density.png is always in the results figure markdown."""
    payload = base_payload()
    payload["madlib"]["visualizations"] = {"enabled": False}
    write_config(tmp_path, payload)
    config = load_madlib_config(tmp_path)

    result = build_results_figure_markdown(config)

    assert "token_density.png" in result


def test_results_figure_markdown_optional_figures_disabled(tmp_path: Path) -> None:
    """With visualizations.enabled=False, optional result figures are omitted."""
    payload = base_payload()
    payload["madlib"]["visualizations"] = {"enabled": False}
    write_config(tmp_path, payload)
    config = load_madlib_config(tmp_path)

    result = build_results_figure_markdown(config)

    assert "section_token_allocation.png" not in result
    assert "provenance_trace_map.png" not in result


def test_results_figure_markdown_optional_flags_individually_disabled(tmp_path: Path) -> None:
    """Each optional flag controls its figure independently."""
    payload = base_payload()
    payload["madlib"]["visualizations"] = {
        "enabled": True,
        "section_token_allocation": False,  # nosec B105
        "provenance_trace_map": False,
    }
    write_config(tmp_path, payload)
    config = load_madlib_config(tmp_path)

    result = build_results_figure_markdown(config)

    assert "token_density.png" in result
    assert "section_token_allocation.png" not in result
    assert "provenance_trace_map.png" not in result


def test_results_figure_markdown_all_optional_enabled(tmp_path: Path) -> None:
    """With all flags enabled, all three result figures appear."""
    write_config(tmp_path, base_payload())
    config = load_madlib_config(tmp_path)

    result = build_results_figure_markdown(config)

    assert "token_density.png" in result
    assert "section_token_allocation.png" in result
    assert "provenance_trace_map.png" in result


# ---------------------------------------------------------------------------
# build_configuration_figure_markdown disabled paths
# ---------------------------------------------------------------------------


def test_configuration_figure_markdown_when_visualizations_disabled(tmp_path: Path) -> None:
    """When visualizations.enabled=False the configuration figures return a disabled notice."""
    payload = base_payload()
    payload["madlib"]["visualizations"] = {"enabled": False}
    write_config(tmp_path, payload)
    config = load_madlib_config(tmp_path)

    result = build_configuration_figure_markdown(config)

    assert "disabled" in result.lower()


def test_configuration_figure_markdown_individual_flags_disabled(tmp_path: Path) -> None:
    """When all configured-field flags are False the fallback string is returned."""
    payload = base_payload()
    payload["madlib"]["visualizations"] = {
        "enabled": True,
        "configured_field_matrix": False,
        "section_configuration_heatmap": False,
        "field_origin_summary": False,
    }
    write_config(tmp_path, payload)
    config = load_madlib_config(tmp_path)

    result = build_configuration_figure_markdown(config)

    assert "disabled" in result.lower()
    assert "configured_field_matrix.png" not in result


def test_configuration_figure_markdown_partial_flags(tmp_path: Path) -> None:
    """When some flags are enabled, only those figure references appear."""
    payload = base_payload()
    payload["madlib"]["visualizations"] = {
        "enabled": True,
        "configured_field_matrix": True,
        "section_configuration_heatmap": False,
        "field_origin_summary": False,
    }
    write_config(tmp_path, payload)
    config = load_madlib_config(tmp_path)

    result = build_configuration_figure_markdown(config)

    assert "configured_field_matrix.png" in result
    assert "section_configuration_heatmap.png" not in result
    assert "field_origin_summary.png" not in result


def test_configuration_figure_markdown_all_enabled(tmp_path: Path) -> None:
    """With all configuration visualization flags enabled, all three figures appear."""
    write_config(tmp_path, base_payload())
    config = load_madlib_config(tmp_path)

    result = build_configuration_figure_markdown(config)

    assert "configured_field_matrix.png" in result
    assert "section_configuration_heatmap.png" in result
    assert "field_origin_summary.png" in result


# ---------------------------------------------------------------------------
# build_evaluation_figure_markdown disabled paths
# ---------------------------------------------------------------------------


def test_evaluation_figure_markdown_when_visualizations_disabled(tmp_path: Path) -> None:
    """When visualizations.enabled=False the evaluation figure returns a disabled notice."""
    payload = base_payload()
    payload["madlib"]["visualizations"] = {"enabled": False}
    write_config(tmp_path, payload)
    config = load_madlib_config(tmp_path)

    result = build_evaluation_figure_markdown(config)

    assert "disabled" in result.lower()
    assert "quality_gate_matrix.png" not in result


def test_evaluation_figure_markdown_when_gate_matrix_flag_false(tmp_path: Path) -> None:
    """When quality_gate_matrix=False the evaluation figure returns a disabled notice."""
    payload = base_payload()
    payload["madlib"]["visualizations"] = {"enabled": True, "quality_gate_matrix": False}
    write_config(tmp_path, payload)
    config = load_madlib_config(tmp_path)

    result = build_evaluation_figure_markdown(config)

    assert "disabled" in result.lower()
    assert "quality_gate_matrix.png" not in result


def test_evaluation_figure_markdown_when_enabled(tmp_path: Path) -> None:
    """When quality_gate_matrix=True the evaluation figure markdown contains the path."""
    write_config(tmp_path, base_payload())
    config = load_madlib_config(tmp_path)

    result = build_evaluation_figure_markdown(config)

    assert "quality_gate_matrix.png" in result
    assert "fig:quality-gate-matrix" in result


# ---------------------------------------------------------------------------
# build_section_plan_table and build_section_title_table
# ---------------------------------------------------------------------------


def test_section_plan_table_shows_disabled_sections(tmp_path: Path) -> None:
    """The section plan table should show 'False' for disabled sections."""
    write_config(tmp_path, base_payload())
    config = load_madlib_config(tmp_path)
    plan = generate_token_plan(config)

    table = build_section_plan_table(config, plan)

    # discussion is disabled in base_payload
    assert "False" in table
    # abstract should be enabled
    assert "True" in table


def test_section_title_table_contains_all_sections(tmp_path: Path) -> None:
    """Section title table must have an entry for every section key."""
    from src.config import SECTION_KEYS

    write_config(tmp_path, base_payload())
    config = load_madlib_config(tmp_path)

    table = build_section_title_table(config)

    for section in SECTION_KEYS:
        assert section in table


# ---------------------------------------------------------------------------
# build_provenance_matrix_table with no-token sections
# ---------------------------------------------------------------------------


def test_provenance_matrix_table_shows_none_for_token_less_sections(tmp_path: Path) -> None:
    """Sections that receive no token choices should show 'none' in the variable column."""
    payload = base_payload()
    # Only one slot assigned to 'abstract'; other sections get no tokens
    payload["madlib"]["slots"] = [
        {"name": "only_adj", "category": "adjectives", "section": "abstract"},
    ]
    write_config(tmp_path, payload)
    config = load_madlib_config(tmp_path)
    plan = generate_token_plan(config)

    table = build_provenance_matrix_table(config, plan)

    # 'methods' gets 0 tokens in this config → should show 'none'
    assert "none" in table


# ---------------------------------------------------------------------------
# Disabled section body content
# ---------------------------------------------------------------------------


def test_disabled_section_body_names_config_key(tmp_path: Path) -> None:
    """A disabled section body should name the controlling section_conditions key."""
    write_config(tmp_path, base_payload())
    config = load_madlib_config(tmp_path)
    plan = generate_token_plan(config)

    sections = build_imrad_sections(config, plan)

    # discussion is disabled in base_payload
    assert "section_conditions.discussion" in sections["DISCUSSION_BODY"]
    assert (
        "intentionally disabled" in sections["DISCUSSION_BODY"].lower()
        or "disabled" in sections["DISCUSSION_BODY"].lower()
    )


def test_disabled_section_body_does_not_contain_enabled_section_claims(tmp_path: Path) -> None:
    """A disabled section body must not contain claims from an enabled section."""
    write_config(tmp_path, base_payload())
    config = load_madlib_config(tmp_path)
    plan = generate_token_plan(config)

    sections = build_imrad_sections(config, plan)

    # The disabled DISCUSSION_BODY should not reference abstract-specific tokens
    assert "complete IMRAD manuscript" not in sections["DISCUSSION_BODY"]


# ---------------------------------------------------------------------------
# All IMRAD section bodies are produced
# ---------------------------------------------------------------------------


def test_all_enabled_imrad_sections_are_non_empty(tmp_path: Path) -> None:
    """Every section key should produce a non-empty body."""
    payload = base_payload()
    # Enable all sections
    payload["madlib"]["section_conditions"] = {}
    write_config(tmp_path, payload)
    config = load_madlib_config(tmp_path)
    plan = generate_token_plan(config)

    sections = build_imrad_sections(config, plan)

    from src.config import SECTION_KEYS

    for key in SECTION_KEYS:
        body_key = f"{key.upper()}_BODY"
        assert body_key in sections
        assert len(sections[body_key]) > 0


# ---------------------------------------------------------------------------
# Contribution table
# ---------------------------------------------------------------------------


def test_contribution_table_includes_boundary_note(tmp_path: Path) -> None:
    """Each contribution claim row must carry a local-claim boundary note."""
    write_config(tmp_path, base_payload())
    config = load_madlib_config(tmp_path)

    table = build_contribution_table(config)

    assert "Local exemplar claim" in table
    assert "no live DOI" in table


# ---------------------------------------------------------------------------
# configured_field_summary_table
# ---------------------------------------------------------------------------


def test_configured_field_summary_table_all_labels_present(tmp_path: Path) -> None:
    """The configured field summary table must contain all nine label rows."""
    from src.analysis_fields import configured_field_counts, configured_field_inventory

    write_config(tmp_path, base_payload())
    config = load_madlib_config(tmp_path)
    plan = generate_token_plan(config)
    inventory = configured_field_inventory(config, plan)
    counts = configured_field_counts(config, inventory)

    table = build_configured_field_summary_table(counts)

    assert "Total tracked field paths" in table
    assert "Explicit YAML paths" in table
    assert "Loader-defaulted paths" in table
    assert "Enabled visualization flags" in table
    assert "Section-level paths" in table
    assert "Lexicon-level paths" in table
    assert "Slot-level paths" in table
    assert "Visualization-control paths" in table
    assert "Top-level schema paths" in table


# ---------------------------------------------------------------------------
# Section title variables
# ---------------------------------------------------------------------------


def test_section_title_variables_covers_all_sections(tmp_path: Path) -> None:
    """section_title_variables must produce TITLE_ variables for every section."""
    from src.config import SECTION_KEYS

    write_config(tmp_path, base_payload())
    config = load_madlib_config(tmp_path)

    titles = section_title_variables(config)

    for key in SECTION_KEYS:
        assert f"TITLE_{key.upper()}" in titles


# ---------------------------------------------------------------------------
# build_configured_field_table row format
# ---------------------------------------------------------------------------


def test_configured_field_table_row_format(tmp_path: Path) -> None:
    """Each row in the configured_field_table should have path, origin, scope, summary columns."""
    from src.analysis_fields import configured_field_inventory

    write_config(tmp_path, base_payload())
    config = load_madlib_config(tmp_path)
    plan = generate_token_plan(config)
    inventory = configured_field_inventory(config, plan)

    table = build_configured_field_table(inventory)

    # Header should be present
    assert "Path" in table
    assert "Origin" in table
    assert "Scope" in table
    assert "Summary" in table
    # At least one explicit row for seed
    assert "madlib.seed" in table


# ---------------------------------------------------------------------------
# _sentence_list single-item branch (line 696 in composition.py)
# ---------------------------------------------------------------------------


def test_imrad_section_with_single_narrative_move(tmp_path: Path) -> None:
    """When a section has exactly one narrative move, _sentence_list returns it directly."""
    payload = base_payload()
    # Set a single move for the abstract section
    payload["madlib"]["narrative_moves"]["abstract"] = ["state the problem"]
    write_config(tmp_path, payload)
    config = load_madlib_config(tmp_path)
    plan = generate_token_plan(config)

    sections = build_imrad_sections(config, plan)

    # The abstract body uses narrative_moves["abstract"] via _sentence_list
    # With a single move, the text should contain that move directly
    assert "state the problem" in sections["ABSTRACT_BODY"]


def test_imrad_limitations_with_single_move(tmp_path: Path) -> None:
    """limitations section with a single narrative move exercises the single-item path."""
    payload = base_payload()
    payload["madlib"]["narrative_moves"]["limitations"] = ["state non-claims"]
    write_config(tmp_path, payload)
    config = load_madlib_config(tmp_path)
    plan = generate_token_plan(config)

    sections = build_imrad_sections(config, plan)

    assert "state non-claims" in sections["LIMITATIONS_BODY"]


def test_imrad_scope_with_single_move(tmp_path: Path) -> None:
    """scope section with a single narrative move exercises the single-item path."""
    payload = base_payload()
    payload["madlib"]["narrative_moves"]["scope"] = ["distinguish generation from truth"]
    write_config(tmp_path, payload)
    config = load_madlib_config(tmp_path)
    plan = generate_token_plan(config)

    sections = build_imrad_sections(config, plan)

    assert "distinguish generation from truth" in sections["SCOPE_BODY"]


# ---------------------------------------------------------------------------
# __init__.py public API import coverage
# ---------------------------------------------------------------------------


def test_init_exports_all_public_symbols() -> None:
    """Importing from the package __init__ must expose all documented public symbols."""
    import src as module

    expected = [
        "EvaluationCriterion",
        "FailureMode",
        "AuthoringObligation",
        "DesignPrinciple",
        "MadlibConfig",
        "MadlibConfigError",
        "MethodStep",
        "PipelinePhase",
        "QualityProbe",
        "SlotSpec",
        "VisualizationConfig",
        "TokenChoice",
        "TokenPlan",
        "generate_token_plan",
        "load_madlib_config",
    ]
    for name in expected:
        assert hasattr(module, name), f"__init__.py missing: {name}"


# ---------------------------------------------------------------------------
# analysis.generate_artifacts with all visualizations disabled
# ---------------------------------------------------------------------------


def test_generate_artifacts_with_visualizations_disabled(tmp_path: Path) -> None:
    """With all visualizations disabled, only token_density and cover figures are written."""
    from src.analysis import generate_artifacts

    payload = base_payload()
    payload["madlib"]["visualizations"] = {"enabled": False}
    write_config(tmp_path, payload)

    artifacts = generate_artifacts(tmp_path)

    # Core artifacts must always be present
    assert artifacts["token_inventory"].is_file()
    assert artifacts["section_plan"].is_file()
    assert artifacts["injection_trace"].is_file()
    assert artifacts["figure"].is_file()  # token_density
    assert artifacts["cover_overview"].is_file()

    # Conditional visualization artifacts should NOT exist
    # (figure files don't exist when the flag is off)
    assert not artifacts["token_injection_flow"].is_file()
    assert not artifacts["section_token_allocation"].is_file()
    assert not artifacts["provenance_trace_map"].is_file()
    assert not artifacts["quality_gate_matrix"].is_file()
    assert not artifacts["configured_field_matrix"].is_file()
    assert not artifacts["section_configuration_heatmap"].is_file()
    assert not artifacts["field_origin_summary"].is_file()


def test_generate_artifacts_figure_registry_omits_disabled_figures(tmp_path: Path) -> None:
    """The figure registry must not include entries for disabled visualizations."""
    from src.analysis import generate_artifacts

    payload = base_payload()
    payload["madlib"]["visualizations"] = {"enabled": False}
    write_config(tmp_path, payload)

    artifacts = generate_artifacts(tmp_path)

    registry = json.loads(artifacts["figure_registry"].read_text(encoding="utf-8"))

    # Disabled figures should not be registered
    assert "fig:token-injection-flow" not in registry
    assert "fig:section-token-allocation" not in registry
    assert "fig:provenance-trace-map" not in registry
    assert "fig:quality-gate-matrix" not in registry
    assert "fig:configured-field-matrix" not in registry
    assert "fig:section-configuration-heatmap" not in registry
    assert "fig:field-origin-summary" not in registry

    # Core figures are always registered
    assert "fig:token-density" in registry
    assert "fig:madlib-cover-overview" in registry


def test_generate_artifacts_with_partial_visualizations(tmp_path: Path) -> None:
    """With some visualizations disabled, only enabled ones are in the registry."""
    from src.analysis import generate_artifacts

    payload = base_payload()
    payload["madlib"]["visualizations"] = {
        "enabled": True,
        "token_injection_flow": True,  # nosec B105
        "section_token_allocation": False,  # nosec B105
        "provenance_trace_map": False,
        "quality_gate_matrix": True,
        "configured_field_matrix": False,
        "section_configuration_heatmap": False,
        "field_origin_summary": False,
    }
    write_config(tmp_path, payload)

    artifacts = generate_artifacts(tmp_path)

    registry = json.loads(artifacts["figure_registry"].read_text(encoding="utf-8"))

    assert "fig:token-injection-flow" in registry
    assert "fig:quality-gate-matrix" in registry
    assert "fig:section-token-allocation" not in registry
    assert "fig:provenance-trace-map" not in registry
    assert "fig:configured-field-matrix" not in registry


# ---------------------------------------------------------------------------
# analysis_fields: _slot_summary with unknown slot name
# ---------------------------------------------------------------------------


def test_slot_summary_unknown_slot_returns_slot_string(tmp_path: Path) -> None:
    """_slot_summary for an unknown slot path should return 'slot'."""
    from src.analysis_fields import _slot_summary

    write_config(tmp_path, base_payload())
    from src.config import load_madlib_config

    config = load_madlib_config(tmp_path)

    # Pass a path for a slot name that doesn't exist in config
    result = _slot_summary(config, "madlib.slots.nonexistent_slot")

    assert result == "slot"


# ---------------------------------------------------------------------------
# analysis_fields: _field_scope covers all scope categories
# ---------------------------------------------------------------------------


def test_field_scope_section_paths(tmp_path: Path) -> None:
    """Paths containing .section_conditions., .section_titles., .narrative_moves. → 'section'."""
    from src.analysis_fields import _field_scope

    assert _field_scope("madlib.section_conditions.abstract") == "section"
    assert _field_scope("madlib.section_titles.methods") == "section"
    assert _field_scope("madlib.narrative_moves.results") == "section"


def test_field_scope_lexicon_path(tmp_path: Path) -> None:
    """Paths containing .lexicon. → 'lexicon'."""
    from src.analysis_fields import _field_scope

    assert _field_scope("madlib.lexicon.adjectives") == "lexicon"


def test_field_scope_slot_path(tmp_path: Path) -> None:
    """Paths containing .slots. → 'slot'."""
    from src.analysis_fields import _field_scope

    assert _field_scope("madlib.slots.first_adjective") == "slot"
    assert _field_scope("madlib.slots.first_adjective.count") == "slot"


def test_field_scope_visualization_path(tmp_path: Path) -> None:
    """Paths containing .visualizations → 'visualization'."""
    from src.analysis_fields import _field_scope

    assert _field_scope("madlib.visualizations.enabled") == "visualization"
    assert _field_scope("madlib.visualizations") == "visualization"


def test_field_scope_schema_path(tmp_path: Path) -> None:
    """Paths not matching any special prefix → 'schema'."""
    from src.analysis_fields import _field_scope

    assert _field_scope("madlib.seed") == "schema"
    assert _field_scope("madlib.composition_depth") == "schema"
    assert _field_scope("madlib.hypothesis") == "schema"
    assert _field_scope("madlib") == "schema"


# ---------------------------------------------------------------------------
# analysis_fields: _field_summary for all branches
# ---------------------------------------------------------------------------


def test_field_summary_for_various_paths(tmp_path: Path) -> None:
    """_field_summary must return meaningful strings for all known path patterns."""
    from src.analysis_fields import _field_summary
    from src.config import load_madlib_config
    from src.tokens import generate_token_plan

    write_config(tmp_path, base_payload())
    config = load_madlib_config(tmp_path)
    plan = generate_token_plan(config)

    # Core schema fields
    assert _field_summary(config, plan, "madlib.seed") == str(config.seed)
    assert _field_summary(config, plan, "madlib.composition_depth") == config.composition_depth
    assert _field_summary(config, plan, "madlib.hypothesis") == config.hypothesis

    # Aggregate fields
    assert "categories" in _field_summary(config, plan, "madlib.lexicon")
    assert "slot rules" in _field_summary(config, plan, "madlib.slots")
    assert _field_summary(config, plan, "madlib.visualizations") in ("enabled", "disabled")

    # Section-level fields
    assert _field_summary(config, plan, "madlib.section_conditions.abstract") in ("enabled", "disabled")
    assert len(_field_summary(config, plan, "madlib.section_titles.methods")) > 0
    assert "moves" in _field_summary(config, plan, "madlib.narrative_moves.methods")

    # Lexicon level
    assert "tokens" in _field_summary(config, plan, "madlib.lexicon.adjectives")

    # Visualization flags
    result = _field_summary(config, plan, "madlib.visualizations.enabled")
    assert result in ("true", "false")

    # Slot sub-fields
    assert _field_summary(config, plan, "madlib.slots.first_adjective.count") == "1"
    assert _field_summary(config, plan, "madlib.slots.noun_pair.section") == "introduction"

    # Block count fields
    for block in (
        "madlib.method_protocol",
        "madlib.evaluation_criteria",
        "madlib.failure_modes",
        "madlib.design_principles",
        "madlib.pipeline_phases",
        "madlib.quality_probes",
        "madlib.authoring_obligations",
        "madlib.audit_rules",
        "madlib.contribution_claims",
    ):
        summary = _field_summary(config, plan, block)
        assert "entries" in summary, f"Expected 'entries' in summary for {block!r}, got {summary!r}"

    # Unknown path
    assert _field_summary(config, plan, "madlib.unknown_field") == "configured field"


# ---------------------------------------------------------------------------
# analysis_fields: configured_field_inventory contains expected scopes
# ---------------------------------------------------------------------------


def test_configured_field_inventory_scopes(tmp_path: Path) -> None:
    """The inventory must contain rows for schema, section, lexicon, slot, and visualization scopes."""
    from src.analysis_fields import configured_field_inventory
    from src.config import load_madlib_config
    from src.tokens import generate_token_plan

    write_config(tmp_path, base_payload())
    config = load_madlib_config(tmp_path)
    plan = generate_token_plan(config)

    inventory = configured_field_inventory(config, plan)

    scopes_present = {row["scope"] for row in inventory}

    assert "schema" in scopes_present
    assert "section" in scopes_present
    assert "lexicon" in scopes_present
    assert "slot" in scopes_present
    assert "visualization" in scopes_present


def test_configured_field_inventory_origins(tmp_path: Path) -> None:
    """The inventory must contain both explicit and defaulted origins."""
    from src.analysis_fields import configured_field_inventory
    from src.config import load_madlib_config
    from src.tokens import generate_token_plan

    write_config(tmp_path, base_payload())
    config = load_madlib_config(tmp_path)
    plan = generate_token_plan(config)

    inventory = configured_field_inventory(config, plan)

    origins_present = {row["origin"] for row in inventory}

    assert "explicit" in origins_present
    assert "defaulted" in origins_present


def test_configured_field_inventory_no_duplicates(tmp_path: Path) -> None:
    """Each path should appear at most once in the inventory."""
    from src.analysis_fields import configured_field_inventory
    from src.config import load_madlib_config
    from src.tokens import generate_token_plan

    write_config(tmp_path, base_payload())
    config = load_madlib_config(tmp_path)
    plan = generate_token_plan(config)

    inventory = configured_field_inventory(config, plan)

    paths = [row["path"] for row in inventory]
    assert len(paths) == len(set(paths))


# ---------------------------------------------------------------------------
# analysis_fields: configured_field_counts aggregation
# ---------------------------------------------------------------------------


def test_configured_field_counts_total_matches_inventory_length(tmp_path: Path) -> None:
    """The 'total' count must equal the length of the inventory."""
    from src.analysis_fields import configured_field_counts, configured_field_inventory
    from src.config import load_madlib_config
    from src.tokens import generate_token_plan

    write_config(tmp_path, base_payload())
    config = load_madlib_config(tmp_path)
    plan = generate_token_plan(config)
    inventory = configured_field_inventory(config, plan)
    counts = configured_field_counts(config, inventory)

    assert counts["total"] == len(inventory)
    assert counts["explicit"] + counts["defaulted"] == counts["total"]
