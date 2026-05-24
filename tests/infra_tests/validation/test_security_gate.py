"""Tests for infrastructure.validation.security_gate skipped-tool semantics."""

from __future__ import annotations

import json
from pathlib import Path

from infrastructure.validation.security_gate import aggregate_security_findings, write_security_report


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
        assert report["skipped_tools"] == [{"tool": "bandit", "reason": "bandit not installed"}]
        assert report["total_findings"] == 2
        assert report["tool_counts"]["safety"] == 2

    def test_all_skipped_yields_zero_findings(self) -> None:
        report = aggregate_security_findings(
            [
                {"status": "skipped", "reason": "bandit not installed", "tool": "bandit"},
                {"status": "skipped", "reason": "safety not installed", "tool": "safety"},
            ]
        )
        assert report["tools_run"] == []
        assert len(report["skipped_tools"]) == 2
        assert report["total_findings"] == 0
        assert report["has_high_severity"] is False


def test_write_security_report_persists_json(tmp_path: Path) -> None:
    report = {"tools_run": ["bandit"], "total_findings": 0, "severity_counts": {"HIGH": 0}}
    out = tmp_path / "reports" / "security.json"
    write_security_report(report, out)
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded["tools_run"] == ["bandit"]
