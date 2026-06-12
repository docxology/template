"""End-to-end integration test using the bundled manuscript."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from src.config import load_project_config
from pipeline_helpers import run_prose_pipeline_with_analysis
from src.report import write_review_report


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_bundled_manuscript_runs(tmp_path: Path):
    """Copy the bundled manuscript into an isolated dir and run the full pipeline."""
    isolated = tmp_path / "iso"
    isolated.mkdir()
    shutil.copytree(PROJECT_ROOT / "manuscript", isolated / "manuscript")

    config = load_project_config(isolated / "manuscript" / "config.yaml")
    artifacts = run_prose_pipeline_with_analysis(config, project_root=isolated)

    assert artifacts.manuscript_report.total_words > 100
    assert (isolated / "output" / "manuscript_report.json").exists()
    payload = json.loads((isolated / "output" / "manuscript_report.json").read_text())
    assert payload["total_words"] == artifacts.manuscript_report.total_words

    # Write the review report and check for stable signposting.
    review = write_review_report(
        isolated / "output" / "review_report.md",
        title=config.title,
        manuscript_report=artifacts.manuscript_report,
        checks=artifacts.checks,
    )
    text = review.read_text(encoding="utf-8")
    assert config.title in text
    assert "Per-file metrics" in text
