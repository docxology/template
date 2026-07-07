#!/usr/bin/env python3
"""Tests for infrastructure.core.pipeline.stage_registry."""

from __future__ import annotations

import pytest

from infrastructure.core.pipeline.stage_registry import (
    MENU_KEY_TO_STAGE,
    STAGE_DISPATCH,
    script_argv_for_stage,
)


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
