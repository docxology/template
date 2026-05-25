"""Tests for project configuration loading."""

from __future__ import annotations

from pathlib import Path

import pytest
from infrastructure.autoresearch import build_autoresearch_plan, parse_string_sequence

from src.config import (
    build_loop_config,
    load_loop_config,
    load_manuscript_loop_settings,
)


def test_load_loop_config_reads_questions_and_artifacts(project_root: Path) -> None:
    repo_root = project_root.parents[1]
    plan = build_autoresearch_plan(repo_root, project_root.name)
    config = load_loop_config(project_root, plan)

    assert config.topic.startswith("Deterministic AutoResearch")
    assert len(config.research_questions) == 3
    assert "output/data/autoresearch_loop.json" in config.required_artifacts
    assert "artifact_manifest" in config.quality_checks


def test_build_loop_config_uses_plan_required_artifacts(project_root: Path) -> None:
    repo_root = project_root.parents[1]
    plan = build_autoresearch_plan(repo_root, project_root.name)
    settings = load_manuscript_loop_settings(project_root)
    config = build_loop_config(plan, settings)

    assert config.required_artifacts == plan.required_artifacts
    assert config.quality_checks == plan.quality_checks
    assert config.topic == plan.config.topic


def test_load_loop_config_rejects_missing_questions(tmp_path: Path) -> None:
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "config.yaml").write_text("project_config: {}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="research_questions"):
        load_manuscript_loop_settings(tmp_path)


def test_load_loop_config_rejects_invalid_project_config(tmp_path: Path) -> None:
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "config.yaml").write_text("project_config: []\n", encoding="utf-8")

    with pytest.raises(ValueError, match="must be a mapping"):
        load_manuscript_loop_settings(tmp_path)


def test_load_loop_config_rejects_invalid_yaml_root(tmp_path: Path) -> None:
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "config.yaml").write_text("- invalid\n", encoding="utf-8")

    with pytest.raises(ValueError, match="YAML root"):
        load_manuscript_loop_settings(tmp_path)


def test_load_loop_config_rejects_invalid_question_entries(tmp_path: Path) -> None:
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "config.yaml").write_text(
        "project_config:\n  research_questions:\n    - not-a-mapping\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="entries must be mappings"):
        load_manuscript_loop_settings(tmp_path)


def test_load_loop_config_rejects_incomplete_question(tmp_path: Path) -> None:
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "config.yaml").write_text(
        "project_config:\n  research_questions:\n    - id: rq\n      question: Missing evidence\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="expected_evidence"):
        load_manuscript_loop_settings(tmp_path)


def test_parse_string_sequence_accepts_defaults_and_scalars() -> None:
    assert parse_string_sequence(None, default=("x",)) == ("x",)
    assert parse_string_sequence("x", default=()) == ("x",)
    assert parse_string_sequence(["x", "y"], default=()) == ("x", "y")
    with pytest.raises(ValueError, match="list values"):
        parse_string_sequence(["x", 1], default=())
    with pytest.raises(ValueError, match="sequence values"):
        parse_string_sequence({"x": "y"}, default=())
