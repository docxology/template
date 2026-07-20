#!/usr/bin/env python3
"""Tests for infrastructure.core.pipeline.stage_registry."""

from __future__ import annotations

import pytest

from infrastructure.core.pipeline.stage_registry import (
    MENU_KEY_TO_STAGE,
    STAGE_DISPATCH,
    resolve_stage_definition,
    script_argv_for_stage,
)
from infrastructure.core.pipeline.dag import PipelineDAG

from pathlib import Path


def test_stage_dispatch_covers_menu_keys() -> None:
    for stage in MENU_KEY_TO_STAGE.values():
        assert stage in STAGE_DISPATCH


def test_render_pdf_maps_to_expected_script() -> None:
    script, *_args = script_argv_for_stage("render_pdf")
    assert script.endswith("stage_03_render.py")


def test_tests_stage_includes_infra_smoke_scope() -> None:
    script, *args = script_argv_for_stage("tests")
    assert script.endswith("stage_01_test.py")
    assert "--infra-scope" in args
    assert "pipeline-smoke" in args


def test_unknown_stage_exits() -> None:
    with pytest.raises(SystemExit, match="Unknown stage"):
        script_argv_for_stage("not_a_real_stage")


def test_clean_is_not_a_dispatchable_stage() -> None:
    """'clean' is an executor built-in, not a single-stage script.

    Regression: a ``"clean"`` dispatch pointing at 00_setup_environment.py made
    ``--stage clean`` silently run setup and clean nothing.
    """
    assert "clean" not in STAGE_DISPATCH
    with pytest.raises(SystemExit, match="Unknown stage"):
        script_argv_for_stage("clean")


def test_single_stage_routes_match_pipeline_yaml() -> None:
    """Full-DAG and single-stage execution resolve the same implementation."""
    yaml_path = Path(__file__).resolve().parents[4] / "infrastructure/core/pipeline/pipeline.yaml"
    dag = PipelineDAG.from_yaml(yaml_path)
    for stage in dag.stages:
        if stage.script is None:
            continue
        assert stage.key is not None
        dispatch = STAGE_DISPATCH[stage.key]
        assert dispatch.script == stage.script
        assert dispatch.args == tuple(stage.args)


def test_stage_identity_resolves_keys_and_compatible_display_names() -> None:
    yaml_path = Path(__file__).resolve().parents[4] / "infrastructure/core/pipeline/pipeline.yaml"
    dag = PipelineDAG.from_yaml(yaml_path)

    by_key = resolve_stage_definition(dag, "render_pdf")
    by_name = resolve_stage_definition(dag, "PDF Rendering")
    by_normalized_name = resolve_stage_definition(dag, "pdf_rendering")

    assert by_key is by_name is by_normalized_name
    assert by_key.key == "render_pdf"
