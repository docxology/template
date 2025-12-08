"""Tests for infrastructure.reporting.pipeline_reporter."""

from __future__ import annotations

import json
from pathlib import Path

from infrastructure.reporting.pipeline_reporter import (
    generate_pipeline_report,
    generate_markdown_report,
    save_pipeline_report,
)


def test_generate_and_save_pipeline_report(tmp_path):
    stage_results = [
        {"name": "setup", "exit_code": 0, "duration": 1.2},
        {"name": "tests", "exit_code": 1, "duration": 2.5},
    ]

    report = generate_pipeline_report(
        stage_results=stage_results,
        total_duration=3.7,
        repo_root=Path("."),
        test_results={"summary": {"total_tests": 10, "total_passed": 9, "total_failed": 1}},
        output_statistics={"pdf_files": 2, "figures": 3, "data_files": 1},
    )

    saved = save_pipeline_report(report, tmp_path, formats=["json", "markdown", "html"])
    assert set(saved.keys()) == {"json", "markdown", "html"}
    assert (tmp_path / "pipeline_report.json").exists()
    assert (tmp_path / "pipeline_report.md").exists()
    assert (tmp_path / "pipeline_report.html").exists()

    md_content = (tmp_path / "pipeline_report.md").read_text()
    assert "Stage Results" in md_content
    assert "Success Rate" in md_content

    data = json.loads((tmp_path / "pipeline_report.json").read_text())
    assert data["stages"][0]["name"] == "setup"
    assert data["stages"][1]["status"] == "failed"


def test_generate_markdown_report_counts_success_rate():
    stage_results = [
        {"name": "only-stage", "exit_code": 0, "duration": 0.5},
    ]
    report = generate_pipeline_report(
        stage_results=stage_results,
        total_duration=0.5,
        repo_root=Path("."),
    )
    md = generate_markdown_report(report)
    assert "Success Rate" in md
    assert "only-stage" in md


