from __future__ import annotations
from pathlib import Path
import pytest
from template_madlib.config import (
    COMPOSITION_DEPTHS,
    SECTION_KEYS,
    MadlibConfigError,
    VisualizationConfig,
    load_madlib_config,
)
from helpers import base_payload, write_config


def test_load_madlib_config_parses_valid_schema(tmp_path: Path) -> None:
    write_config(tmp_path, base_payload())

    config = load_madlib_config(tmp_path)

    assert config.title == "Test Madlib"
    assert config.schema_version == 2
    assert config.source_schema_version == 1
    assert config.seed == 7
    assert config.composition_depth == "deep"
    assert config.section_conditions["discussion"] is False
    assert config.section_titles["methods"] == "Methods: Test Protocol"
    assert config.narrative_moves["methods"] == ("load config", "expand slots")
    assert config.method_protocol[0].output == "MadlibConfig"
    assert config.evaluation_criteria[0].gate == "tests"
    assert config.failure_modes[0].name == "Unresolved placeholder"
    assert config.design_principles[0].name == "Configuration owns prose choices"
    assert config.pipeline_phases[0].output_artifact == "MadlibConfig"
    assert config.quality_probes[0].artifact == "output/manuscript"
    assert config.authoring_obligations[0].review_surface == "output/manuscript"
    assert config.visualizations.enabled is True
    assert config.visualizations.enabled_flags == (
        "configured_field_matrix",
        "section_configuration_heatmap",
        "field_origin_summary",
        "token_injection_flow",
        "section_token_allocation",
        "provenance_trace_map",
        "quality_gate_matrix",
    )
    assert "madlib.seed" in config.explicit_paths
    assert "madlib.section_titles.methods" in config.explicit_paths
    assert "madlib.section_titles.abstract" in config.defaulted_paths
    assert "madlib.slots.first_adjective.count" in config.defaulted_paths
    assert "madlib.visualizations.enabled" in config.defaulted_paths
    assert "Every placeholder resolves." in config.audit_rules
    assert "Every method protocol row identifies action, evidence, and output." in config.audit_rules
    assert "Every fork that adds domain claims must add validators." in config.audit_rules
    assert any("review handoff" in rule for rule in config.audit_rules)
    assert "Config-owned tokens are auditable." in config.contribution_claims
    assert any("Review packets" in claim for claim in config.contribution_claims)
    assert config.slots[1].count == 2
    assert "discussion" not in config.enabled_sections


def test_missing_optional_schema_blocks_use_defaults(tmp_path: Path) -> None:
    payload = base_payload()
    for key in (
        "method_protocol",
        "evaluation_criteria",
        "failure_modes",
        "design_principles",
        "pipeline_phases",
        "quality_probes",
        "authoring_obligations",
        "audit_rules",
        "contribution_claims",
    ):
        del payload["madlib"][key]
    write_config(tmp_path, payload)

    config = load_madlib_config(tmp_path)

    assert config.method_protocol[0].output == "MadlibConfig"
    assert config.evaluation_criteria[0].gate == "pytest"
    assert config.failure_modes[0].name == "Unresolved placeholder"
    assert config.design_principles[0].name == "Configuration owns prose choices"
    assert config.pipeline_phases[0].output_artifact == "MadlibConfig"
    assert config.quality_probes[0].artifact == "output/manuscript"
    assert config.authoring_obligations[0].review_surface == "output/manuscript and output/web"
    assert config.visualizations.configured_field_matrix is True
    assert "madlib.visualizations" in config.defaulted_paths
    assert len(config.audit_rules) == 3
    assert len(config.contribution_claims) == 2


def test_current_schema_version_is_recorded(tmp_path: Path) -> None:
    payload = base_payload()
    payload["madlib"]["schema_version"] = 2
    write_config(tmp_path, payload)

    config = load_madlib_config(tmp_path)

    assert config.schema_version == 2
    assert config.source_schema_version == 2


def test_unknown_schema_version_fails_closed(tmp_path: Path) -> None:
    payload = base_payload()
    payload["madlib"]["schema_version"] = 99
    write_config(tmp_path, payload)

    with pytest.raises(MadlibConfigError, match="Unsupported madlib.schema_version"):
        load_madlib_config(tmp_path)


def test_boolean_schema_version_rejected(tmp_path: Path) -> None:
    """`bool` is an `int` subclass in Python; the loader must reject it explicitly."""
    payload = base_payload()
    payload["madlib"]["schema_version"] = True
    write_config(tmp_path, payload)

    with pytest.raises(MadlibConfigError, match="madlib.schema_version must be an integer"):
        load_madlib_config(tmp_path)


def test_non_numeric_schema_version_rejected(tmp_path: Path) -> None:
    payload = base_payload()
    payload["madlib"]["schema_version"] = "not-a-version"
    write_config(tmp_path, payload)

    with pytest.raises(MadlibConfigError, match="madlib.schema_version must be an integer"):
        load_madlib_config(tmp_path)


def test_visualization_config_tracks_explicit_and_defaulted_flags(tmp_path: Path) -> None:
    payload = base_payload()
    payload["madlib"]["visualizations"] = {
        "enabled": True,
        "configured_field_matrix": False,
    }
    write_config(tmp_path, payload)

    config = load_madlib_config(tmp_path)

    assert config.visualizations.configured_field_matrix is False
    assert config.visualizations.section_configuration_heatmap is True
    assert config.visualizations.enabled_flags == (
        "section_configuration_heatmap",
        "field_origin_summary",
        "token_injection_flow",
        "section_token_allocation",
        "provenance_trace_map",
        "quality_gate_matrix",
    )
    assert "madlib.visualizations" in config.explicit_paths
    assert "madlib.visualizations.configured_field_matrix" in config.explicit_paths
    assert "madlib.visualizations.section_configuration_heatmap" in config.defaulted_paths


def test_visualization_config_rejects_malformed_values(tmp_path: Path) -> None:
    payload = base_payload()
    payload["madlib"]["visualizations"] = {"enabled": "yes"}
    write_config(tmp_path, payload)

    with pytest.raises(MadlibConfigError, match="visualizations.enabled"):
        load_madlib_config(tmp_path)


def test_visualization_config_rejects_unknown_fields(tmp_path: Path) -> None:
    payload = base_payload()
    payload["madlib"]["visualizations"] = {"sparkles": True}
    write_config(tmp_path, payload)

    with pytest.raises(MadlibConfigError, match="unknown field"):
        load_madlib_config(tmp_path)


def test_missing_config_raises(tmp_path: Path) -> None:
    with pytest.raises(MadlibConfigError, match="Missing manuscript config"):
        load_madlib_config(tmp_path)


def test_empty_required_lexicon_category_rejected(tmp_path: Path) -> None:
    payload = base_payload()
    payload["madlib"]["lexicon"]["adjectives"] = []
    write_config(tmp_path, payload)

    with pytest.raises(MadlibConfigError, match="adjectives"):
        load_madlib_config(tmp_path)


def test_missing_slot_category_rejected(tmp_path: Path) -> None:
    payload = base_payload()
    payload["madlib"]["slots"].append({"name": "bad", "category": "missing", "section": "results"})
    write_config(tmp_path, payload)

    with pytest.raises(MadlibConfigError, match="missing lexicon categories"):
        load_madlib_config(tmp_path)


def test_unknown_section_condition_rejected(tmp_path: Path) -> None:
    payload = base_payload()
    payload["madlib"]["section_conditions"]["appendix"] = True
    write_config(tmp_path, payload)

    with pytest.raises(MadlibConfigError, match="unknown section"):
        load_madlib_config(tmp_path)


def test_invalid_composition_depth_rejected(tmp_path: Path) -> None:
    payload = base_payload()
    payload["madlib"]["composition_depth"] = "limitless"
    write_config(tmp_path, payload)

    with pytest.raises(MadlibConfigError, match="composition_depth"):
        load_madlib_config(tmp_path)


def test_unknown_section_title_rejected(tmp_path: Path) -> None:
    payload = base_payload()
    payload["madlib"]["section_titles"]["appendix"] = "Appendix"
    write_config(tmp_path, payload)

    with pytest.raises(MadlibConfigError, match="section_titles"):
        load_madlib_config(tmp_path)


def test_method_protocol_requires_complete_rows(tmp_path: Path) -> None:
    payload = base_payload()
    payload["madlib"]["method_protocol"] = [{"name": "Load", "action": "Parse"}]
    write_config(tmp_path, payload)

    with pytest.raises(MadlibConfigError, match="method_protocol"):
        load_madlib_config(tmp_path)


def test_evaluation_criteria_require_complete_rows(tmp_path: Path) -> None:
    payload = base_payload()
    payload["madlib"]["evaluation_criteria"] = [{"name": "Placeholder resolution"}]
    write_config(tmp_path, payload)

    with pytest.raises(MadlibConfigError, match="evaluation_criteria"):
        load_madlib_config(tmp_path)


def test_failure_modes_require_complete_rows(tmp_path: Path) -> None:
    payload = base_payload()
    payload["madlib"]["failure_modes"] = [{"name": "Unresolved placeholder"}]
    write_config(tmp_path, payload)

    with pytest.raises(MadlibConfigError, match="failure_modes"):
        load_madlib_config(tmp_path)


def test_design_principles_require_complete_rows(tmp_path: Path) -> None:
    payload = base_payload()
    payload["madlib"]["design_principles"] = [{"name": "Configuration owns prose choices"}]
    write_config(tmp_path, payload)

    with pytest.raises(MadlibConfigError, match="design_principles"):
        load_madlib_config(tmp_path)


def test_pipeline_phases_require_complete_rows(tmp_path: Path) -> None:
    payload = base_payload()
    payload["madlib"]["pipeline_phases"] = [{"name": "Schema parse"}]
    write_config(tmp_path, payload)

    with pytest.raises(MadlibConfigError, match="pipeline_phases"):
        load_madlib_config(tmp_path)


def test_quality_probes_require_complete_rows(tmp_path: Path) -> None:
    payload = base_payload()
    payload["madlib"]["quality_probes"] = [{"name": "Placeholder survival"}]
    write_config(tmp_path, payload)

    with pytest.raises(MadlibConfigError, match="quality_probes"):
        load_madlib_config(tmp_path)


def test_authoring_obligations_require_complete_rows(tmp_path: Path) -> None:
    payload = base_payload()
    payload["madlib"]["authoring_obligations"] = [{"name": "Review generated claims"}]
    write_config(tmp_path, payload)

    with pytest.raises(MadlibConfigError, match="authoring_obligations"):
        load_madlib_config(tmp_path)


# ---------------------------------------------------------------------------
# VisualizationConfig edge cases
# ---------------------------------------------------------------------------


def test_visualization_config_enabled_false_returns_empty_flags() -> None:
    """When enabled=False, enabled_flags must return an empty tuple."""
    viz = VisualizationConfig(enabled=False)
    assert viz.enabled_flags == ()


def test_visualization_config_all_false_returns_empty_flags() -> None:
    """When every individual flag is False, enabled_flags returns an empty tuple."""
    viz = VisualizationConfig(
        enabled=True,
        configured_field_matrix=False,
        section_configuration_heatmap=False,
        field_origin_summary=False,
        token_injection_flow=False,
        section_token_allocation=False,
        provenance_trace_map=False,
        quality_gate_matrix=False,
    )
    assert viz.enabled_flags == ()


def test_visualization_config_enabled_false_via_config(tmp_path: Path) -> None:
    """Loading a config with visualizations.enabled=False propagates to enabled_flags."""
    payload = base_payload()
    payload["madlib"]["visualizations"] = {"enabled": False}
    write_config(tmp_path, payload)

    config = load_madlib_config(tmp_path)

    assert config.visualizations.enabled is False
    assert config.visualizations.enabled_flags == ()


# ---------------------------------------------------------------------------
# All section keys round-trip (section_conditions defaults to True for all)
# ---------------------------------------------------------------------------


def test_all_section_keys_default_to_enabled(tmp_path: Path) -> None:
    """Without explicit section_conditions all SECTION_KEYS default to enabled."""
    payload = base_payload()
    del payload["madlib"]["section_conditions"]
    write_config(tmp_path, payload)

    config = load_madlib_config(tmp_path)

    for key in SECTION_KEYS:
        assert config.section_conditions[key] is True
    assert set(config.enabled_sections) == set(SECTION_KEYS)


# ---------------------------------------------------------------------------
# Multiple visualization flags with mix of explicit/defaulted tracking
# ---------------------------------------------------------------------------


def test_visualization_explicit_tracking_for_partial_block(tmp_path: Path) -> None:
    """Only the sub-keys actually in the YAML block are in explicit_paths."""
    payload = base_payload()
    payload["madlib"]["visualizations"] = {
        "enabled": True,
        "token_injection_flow": False,  # nosec B105
        "quality_gate_matrix": True,
    }
    write_config(tmp_path, payload)

    config = load_madlib_config(tmp_path)

    assert "madlib.visualizations.token_injection_flow" in config.explicit_paths
    assert "madlib.visualizations.quality_gate_matrix" in config.explicit_paths
    assert "madlib.visualizations.configured_field_matrix" in config.defaulted_paths
    assert config.visualizations.token_injection_flow is False
    assert config.visualizations.quality_gate_matrix is True


# ---------------------------------------------------------------------------
# MadlibConfig properties
# ---------------------------------------------------------------------------


def test_enabled_sections_excludes_disabled(tmp_path: Path) -> None:
    """enabled_sections only includes sections where section_conditions is True."""
    payload = base_payload()
    payload["madlib"]["section_conditions"] = {
        "abstract": True,
        "introduction": False,
        "methods": True,
        "discussion": False,
    }
    write_config(tmp_path, payload)

    config = load_madlib_config(tmp_path)

    enabled = config.enabled_sections
    assert "abstract" in enabled
    assert "methods" in enabled
    assert "introduction" not in enabled
    assert "discussion" not in enabled


# ---------------------------------------------------------------------------
# Multi-count slots produce correct variable names
# ---------------------------------------------------------------------------


def test_multi_count_slot_variable_names(tmp_path: Path) -> None:
    """Slots with count > 1 generate NAME_1, NAME_2, ... variable names."""
    from template_madlib.tokens import generate_token_plan

    payload = base_payload()
    payload["madlib"]["slots"] = [
        {"name": "triple_noun", "category": "nouns", "section": "methods", "count": 3},
    ]
    write_config(tmp_path, payload)

    config = load_madlib_config(tmp_path)
    plan = generate_token_plan(config)

    variable_names = [c.variable_name for c in plan.choices]
    assert "TRIPLE_NOUN_1" in variable_names
    assert "TRIPLE_NOUN_2" in variable_names
    assert "TRIPLE_NOUN_3" in variable_names


# ---------------------------------------------------------------------------
# Hypothesis field defaults
# ---------------------------------------------------------------------------


def test_hypothesis_defaults_when_missing(tmp_path: Path) -> None:
    """When hypothesis is absent the config falls back to the default string."""
    payload = base_payload()
    del payload["madlib"]["hypothesis"]
    write_config(tmp_path, payload)

    config = load_madlib_config(tmp_path)

    assert "Deterministic token injection" in config.hypothesis


# ---------------------------------------------------------------------------
# Seed defaults to 0
# ---------------------------------------------------------------------------


def test_seed_defaults_to_zero_when_missing(tmp_path: Path) -> None:
    """Omitting seed in the YAML should produce seed=0."""
    payload = base_payload()
    del payload["madlib"]["seed"]
    write_config(tmp_path, payload)

    config = load_madlib_config(tmp_path)

    assert config.seed == 0


# ---------------------------------------------------------------------------
# composition_depth defaults to 'standard'
# ---------------------------------------------------------------------------


def test_composition_depth_defaults_to_standard(tmp_path: Path) -> None:
    """Omitting composition_depth produces 'standard'."""
    payload = base_payload()
    del payload["madlib"]["composition_depth"]
    write_config(tmp_path, payload)

    config = load_madlib_config(tmp_path)

    assert config.composition_depth == "standard"


# ---------------------------------------------------------------------------
# All valid composition depths are accepted
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("depth", sorted(COMPOSITION_DEPTHS))
def test_all_valid_composition_depths_accepted(tmp_path: Path, depth: str) -> None:
    """Each value in COMPOSITION_DEPTHS must be accepted by the loader."""
    subdir = tmp_path / depth
    payload = base_payload()
    payload["madlib"]["composition_depth"] = depth
    write_config(subdir, payload)

    config = load_madlib_config(subdir)
    assert config.composition_depth == depth
