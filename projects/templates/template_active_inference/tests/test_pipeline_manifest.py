"""Pipeline manifest contract tests."""

from __future__ import annotations

from pathlib import Path

from orchestration.pipeline_manifest import DEFAULT_ANALYSIS_SCRIPTS, analysis_scripts


def test_pipeline_manifest_lists_scripts() -> None:
    root = Path(__file__).resolve().parents[1]
    scripts = analysis_scripts(root)
    assert len(scripts) == len(DEFAULT_ANALYSIS_SCRIPTS)
