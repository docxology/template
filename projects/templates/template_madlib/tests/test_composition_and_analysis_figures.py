from __future__ import annotations

import json
import re
from pathlib import Path


from src.analysis import generate_artifacts
from src.analysis_fields import configured_field_counts, configured_field_inventory
from src.composition import (
    build_configured_field_summary_table,
    build_configured_field_table,
    build_configuration_figure_markdown,
    build_contribution_table,
    build_evaluation_figure_markdown,
    build_imrad_sections,
    build_methods_figure_markdown,
    build_provenance_matrix_table,
    build_results_figure_markdown,
    build_section_plan_table,
    build_section_title_table,
    section_title_variables,
)
from src.config import load_madlib_config
from src.tokens import generate_token_plan
from .helpers import base_payload, write_config

PROJECT_ROOT = Path(__file__).resolve().parent.parent


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
    assert "publication status remains config-declared" in table


# ---------------------------------------------------------------------------
# configured_field_summary_table
# ---------------------------------------------------------------------------


def test_configured_field_summary_table_all_labels_present(tmp_path: Path) -> None:
    """The configured field summary table must contain all nine label rows."""

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
