#!/usr/bin/env python3
"""Tests for infrastructure.core.pipeline.single_stage."""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.core.pipeline.single_stage import execute_single_stage


def test_unknown_stage_exits_with_message() -> None:
    with pytest.raises(SystemExit, match="Unknown stage"):
        execute_single_stage("not_a_real_stage", "template_code_project", Path("."))


def test_known_stage_key_is_mapped() -> None:
    from infrastructure.core.pipeline import single_stage

    assert "render_pdf" in single_stage._STAGE_TO_SCRIPT
    assert single_stage._STAGE_TO_SCRIPT["render_pdf"][0].endswith("03_render_pdf.py")
