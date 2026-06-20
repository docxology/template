from __future__ import annotations

from pathlib import Path

import pytest

from config import MadlibConfigError, load_madlib_config
from .helpers import base_payload, write_config


def test_load_madlib_config_parses_valid_schema(tmp_path: Path) -> None:
    write_config(tmp_path, base_payload())

    config = load_madlib_config(tmp_path)

    assert config.title == "Test Madlib"
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
