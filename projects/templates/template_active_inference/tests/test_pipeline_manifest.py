"""Pipeline manifest contract tests."""

from __future__ import annotations

from pathlib import Path

import yaml

from orchestration.pipeline_manifest import DEFAULT_ANALYSIS_SCRIPTS, analysis_scripts


def test_pipeline_manifest_lists_scripts() -> None:
    root = Path(__file__).resolve().parents[1]
    scripts = analysis_scripts(root)
    assert len(scripts) == len(DEFAULT_ANALYSIS_SCRIPTS)


def test_config_analysis_scripts_match_default_manifest_order() -> None:
    root = Path(__file__).resolve().parents[1]
    config = yaml.safe_load((root / "manuscript" / "config.yaml").read_text(encoding="utf-8"))
    configured = config["analysis"]["scripts"]

    assert configured == [step.script for step in DEFAULT_ANALYSIS_SCRIPTS]
