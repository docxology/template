"""Tests for infrastructure.validation.security_gate skipped-tool semantics."""

from __future__ import annotations

import json
from pathlib import Path

from infrastructure.validation.security_gate import (
    aggregate_security_findings,
    _pip_audit_vulnerabilities,
    run_security_scan,
    write_security_report,
)


class TestAggregateSecurityFindings:
    def test_skipped_tools_are_reported_separately(self) -> None:
        report = aggregate_security_findings(
            [
                {"status": "skipped", "reason": "bandit not installed", "tool": "bandit"},
                {
                    "tool": "safety",
                    "summary": {"total": 2, "high": 0, "medium": 1, "low": 1},
                    "findings": [],
                },
            ]
        )
        assert report["tools_run"] == ["safety"]
        assert report["skipped_tools"] == [{"tool": "bandit", "reason": "bandit not installed", "required": True}]
        assert report["failed_tools"] == [{"tool": "bandit", "reason": "bandit not installed", "required": True}]
        assert report["has_required_tool_failures"] is True
        assert report["total_findings"] == 2
        assert report["tool_counts"]["safety"] == 2

    def test_optional_safety_skip_does_not_fail_closed(self) -> None:
        report = aggregate_security_findings(
            [
                {
                    "tool": "bandit",
                    "summary": {"total": 0, "high": 0, "medium": 0, "low": 0},
                    "findings": [],
                },
                {"status": "skipped", "reason": "safety not installed", "tool": "safety"},
                {
                    "tool": "pip_audit",
                    "summary": {"total": 0, "high": 0, "medium": 0, "low": 0},
                    "findings": [],
                },
            ]
        )

        assert report["tools_run"] == ["bandit", "pip_audit"]
        assert report["skipped_tools"] == [{"tool": "safety", "reason": "safety not installed", "required": False}]
        assert report["failed_tools"] == []
        assert report["has_required_tool_failures"] is False
        assert report["has_blocking_findings"] is False

    def test_all_skipped_records_required_tool_failures(self) -> None:
        report = aggregate_security_findings(
            [
                {"status": "skipped", "reason": "bandit not installed", "tool": "bandit"},
                {"status": "skipped", "reason": "safety not installed", "tool": "safety"},
                {"status": "skipped", "reason": "pip-audit not installed", "tool": "pip_audit"},
            ]
        )
        assert report["tools_run"] == []
        assert len(report["skipped_tools"]) == 3
        assert {row["tool"] for row in report["failed_tools"]} == {"bandit", "pip_audit"}
        assert report["has_required_tool_failures"] is True
        assert report["total_findings"] == 0
        assert report["has_high_severity"] is False

    def test_high_severity_sets_fail_flag(self) -> None:
        report = aggregate_security_findings(
            [
                {
                    "tool": "bandit",
                    "summary": {"total": 2, "high": 1, "medium": 1, "low": 0},
                    "findings": [{"issue_severity": "HIGH"}],
                }
            ]
        )

        assert report["severity_counts"]["HIGH"] == 1
        assert report["tool_counts"]["bandit"] == 2
        assert report["has_high_severity"] is True
        assert report["has_blocking_findings"] is True

    def test_pip_audit_vulnerabilities_are_blocking_without_severity(self) -> None:
        report = aggregate_security_findings(
            [
                {
                    "tool": "pip_audit",
                    "summary": {"total": 1, "high": 0, "medium": 0, "low": 0},
                    "findings": [{"id": "PYSEC-0000"}],
                }
            ]
        )

        assert report["has_high_severity"] is False
        assert report["blocking_findings"] == [{"tool": "pip_audit", "count": 1}]
        assert report["has_blocking_findings"] is True

    def test_pip_audit_vulnerabilities_supports_dependency_json_shape(self) -> None:
        data = {"dependencies": [{"name": "pkg", "vulns": [{"id": "PYSEC-0000"}]}]}

        assert _pip_audit_vulnerabilities(data) == [{"id": "PYSEC-0000"}]


def test_write_security_report_persists_json(tmp_path: Path) -> None:
    report = {"tools_run": ["bandit"], "total_findings": 0, "severity_counts": {"HIGH": 0}}
    out = tmp_path / "reports" / "security.json"
    write_security_report(report, out)
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded["tools_run"] == ["bandit"]


def test_run_security_scan_skips_missing_tools_with_empty_path(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PATH", str(tmp_path / "empty-bin"))

    report, exit_code = run_security_scan(tmp_path)

    assert exit_code == 1
    assert report["tools_run"] == []
    assert {row["tool"] for row in report["skipped_tools"]} == {"bandit", "safety", "pip_audit"}
    assert {row["tool"] for row in report["failed_tools"]} == {"bandit", "pip_audit"}
    assert report["has_required_tool_failures"] is True
    assert (tmp_path / ".cache" / "template" / "security_report.json").exists()
