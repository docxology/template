from __future__ import annotations

import json
from pathlib import Path

from infrastructure.reporting.test_reporter import (
    generate_test_report,
    parse_pytest_output,
    save_test_report,
)


def test_parse_pytest_output_extracts_counts_and_coverage() -> None:
    stdout = "5 passed, 1 failed, 2 skipped, 1 deselected in 1.00s\nCoverage: 85.23%"
    result = parse_pytest_output(stdout=stdout, stderr="", exit_code=1)

    assert result["passed"] == 5
    assert result["failed"] == 1
    assert result["skipped"] == 2
    assert result["total"] == 8
    assert result["coverage_percent"] == 85.23
    assert result["exit_code"] == 1


def test_generate_test_report_combines_infra_and_project() -> None:
    infra = {"passed": 5, "failed": 0, "skipped": 1, "total": 6, "coverage_percent": 91.0, "exit_code": 0}
    project = {"passed": 7, "failed": 1, "skipped": 0, "total": 8, "coverage_percent": 93.5, "exit_code": 1}

    report = generate_test_report(infra_results=infra, project_results=project, repo_root=Path("."))

    summary = report["summary"]
    assert summary["total_passed"] == 12
    assert summary["total_failed"] == 1
    assert summary["total_tests"] == 14
    assert not summary["all_passed"]
    assert summary["infrastructure_coverage"] == 91.0
    assert summary["project_coverage"] == 93.5


def test_save_test_report_writes_json_and_markdown(tmp_path: Path) -> None:
    report = {
        "timestamp": "2025-01-01T00:00:00",
        "infrastructure": {"passed": 1, "failed": 0, "skipped": 0, "total": 1, "coverage_percent": 90.0},
        "project": {"passed": 2, "failed": 0, "skipped": 0, "total": 2, "coverage_percent": 95.0},
        "summary": {"total_passed": 3, "total_failed": 0, "total_tests": 3, "all_passed": True},
    }

    json_path, md_path = save_test_report(report, tmp_path)

    assert json_path.exists()
    assert md_path.exists()

    data = json.loads(json_path.read_text())
    assert data["summary"]["total_passed"] == 3

    md_content = md_path.read_text()
    assert "Coverage: 90.00%" in md_content
    assert "Coverage: 95.00%" in md_content


def test_parse_pytest_output_no_coverage() -> None:
    """Test parse_pytest_output when coverage is not present."""
    stdout = "5 passed, 1 failed, 2 skipped in 1.00s"
    result = parse_pytest_output(stdout=stdout, stderr="", exit_code=0)
    
    assert result["passed"] == 5
    assert result["failed"] == 1
    assert result["skipped"] == 2
    assert "coverage_percent" not in result


def test_parse_pytest_output_warnings() -> None:
    """Test parse_pytest_output counts warnings."""
    stdout = "5 passed in 1.00s"
    stderr = " warning: something\n warning: another"
    result = parse_pytest_output(stdout=stdout, stderr=stderr, exit_code=0)
    
    # The function counts ' warning' (with space before) in both stdout and stderr
    assert result["warnings"] == 2


def test_parse_pytest_output_deselected() -> None:
    """Test parse_pytest_output handles deselected tests."""
    stdout = "5 passed, 10 deselected in 1.00s"
    result = parse_pytest_output(stdout=stdout, stderr="", exit_code=0)
    
    assert result["passed"] == 5
    assert result["total"] == 5  # Deselected not counted in total


def test_generate_test_report_no_coverage() -> None:
    """Test generate_test_report when coverage is not present."""
    infra = {"passed": 5, "failed": 0, "skipped": 1, "total": 6, "exit_code": 0}
    project = {"passed": 7, "failed": 1, "skipped": 0, "total": 8, "exit_code": 1}
    
    report = generate_test_report(infra_results=infra, project_results=project, repo_root=Path("."))
    
    assert "infrastructure_coverage" not in report["summary"]
    assert "project_coverage" not in report["summary"]


def test_generate_test_report_all_passed() -> None:
    """Test generate_test_report when all tests pass."""
    infra = {"passed": 10, "failed": 0, "skipped": 0, "total": 10, "exit_code": 0}
    project = {"passed": 20, "failed": 0, "skipped": 0, "total": 20, "exit_code": 0}
    
    report = generate_test_report(infra_results=infra, project_results=project, repo_root=Path("."))
    
    assert report["summary"]["all_passed"] is True
    assert report["summary"]["total_passed"] == 30
    assert report["summary"]["total_failed"] == 0


def test_save_test_report_no_coverage(tmp_path: Path) -> None:
    """Test save_test_report when coverage is not present."""
    report = {
        "timestamp": "2025-01-01T00:00:00",
        "infrastructure": {"passed": 1, "failed": 0, "skipped": 0, "total": 1},
        "project": {"passed": 2, "failed": 0, "skipped": 0, "total": 2},
        "summary": {"total_passed": 3, "total_failed": 0, "total_tests": 3, "all_passed": True},
    }
    
    json_path, md_path = save_test_report(report, tmp_path)
    
    assert json_path.exists()
    assert md_path.exists()
    
    md_content = md_path.read_text()
    assert "Coverage:" not in md_content  # Should not mention coverage














