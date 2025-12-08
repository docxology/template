"""Tests for infrastructure.reporting.test_reporter."""

from __future__ import annotations

import json
from pathlib import Path

from infrastructure.reporting.test_reporter import (
    generate_test_report,
    parse_pytest_output,
    save_test_report,
)


def test_parse_pytest_output_extracts_counts():
    stdout = "5 passed, 1 failed, 2 skipped in 3.00s\nCoverage: 88.50%"
    results = parse_pytest_output(stdout, "", exit_code=1)

    assert results["passed"] == 5
    assert results["failed"] == 1
    assert results["skipped"] == 2
    assert results["total"] == 8
    assert results["exit_code"] == 1
    assert results["coverage_percent"] == 88.50


def test_generate_and_save_test_report(tmp_path):
    infra = {
        "passed": 3,
        "failed": 0,
        "skipped": 1,
        "total": 4,
        "exit_code": 0,
        "coverage_percent": 91.0,
    }
    project = {
        "passed": 5,
        "failed": 1,
        "skipped": 0,
        "total": 6,
        "exit_code": 1,
        "coverage_percent": 99.0,
    }

    report = generate_test_report(infra, project, Path("."))

    assert report["summary"]["total_tests"] == 10
    assert report["summary"]["total_failed"] == 1
    assert report["summary"]["all_passed"] is False

    json_path, md_path = save_test_report(report, tmp_path)
    assert json_path.exists()
    assert md_path.exists()

    data = json.loads(json_path.read_text())
    assert data["summary"]["total_passed"] == 8
    assert data["summary"]["total_failed"] == 1


