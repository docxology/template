"""Tests for canonical pipeline stage vocabulary."""

from __future__ import annotations

from infrastructure.core.pipeline import stage_vocabulary as sv
from infrastructure.orchestration.menu import STAGE_NAMES


def test_project_analysis_in_core_stages() -> None:
    names = sv.core_stage_names()
    assert "Project Analysis" in names
    assert "PDF Rendering" in names
    assert "Output Validation" in names


def test_menu_stage_names_match_menu_module() -> None:
    assert STAGE_NAMES == sv.menu_stage_names()
    assert "Clean Output Directories" not in STAGE_NAMES


def test_stage_alias_resolves_analysis() -> None:
    aliases = sv.stage_aliases()
    assert aliases["analysis"] == "Project Analysis"


def test_text_mentions_stage_by_canonical_name() -> None:
    text = "Failure in Project Analysis — no figures generated."
    assert sv.text_mentions_stage(text, "Project Analysis")


def test_text_mentions_stage_by_script() -> None:
    text = "Isolate with scripts/02_run_analysis.py --project foo"
    assert sv.text_mentions_stage(text, "Project Analysis")


def test_text_mentions_stage_by_alias() -> None:
    text = "Re-run the analysis stage after uv sync."
    assert sv.text_mentions_stage(text, "Project Analysis")


def test_no_numeric_stage_four_in_api() -> None:
    """Vocabulary uses canonical names, not transient numeric stage indices."""
    for name in sv.core_stage_names():
        assert "stage 4" not in name.lower()
    assert "stage 4" not in str(sv.stage_aliases()).lower()
