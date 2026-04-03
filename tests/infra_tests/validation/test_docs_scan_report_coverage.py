"""Tests for infrastructure.validation.docs._docs_scan_report — coverage."""

from infrastructure.validation.docs._docs_scan_report import build_documentation_scan_report
from infrastructure.validation.docs.models import (
    LinkIssue,
    QualityIssue,
    ScanResults,
)


def _make_results(**overrides):
    defaults = {
        "scan_date": "2026-04-01T12:00:00",
        "total_files": 10,
    }
    defaults.update(overrides)
    return ScanResults(**defaults)


class TestBuildDocumentationScanReport:
    def test_minimal_report(self):
        results = _make_results()
        report = build_documentation_scan_report(results)
        assert "# Documentation Scan and Improvement Report" in report
        assert "2026-04-01T12:00:00" in report
        assert "10 markdown files" in report

    def test_with_phase1_stats(self):
        results = _make_results()
        results.statistics["phase1"] = {
            "markdown_files": 15,
            "agents_readme_files": 3,
            "config_files": 2,
            "script_files": 5,
        }
        report = build_documentation_scan_report(results)
        assert "15" in report
        assert "AGENTS.md/README.md" in report
        assert "Configuration Files" in report

    def test_with_phase2_stats(self):
        results = _make_results()
        results.statistics["phase2"] = {
            "link_issues": 5,
            "command_issues": 1,
            "path_issues": 2,
            "config_issues": 0,
            "terminology_issues": 3,
            "total_issues": 11,
        }
        report = build_documentation_scan_report(results)
        assert "Phase 2: Accuracy Verification" in report
        assert "Total Issues" in report

    def test_with_link_issues(self):
        results = _make_results()
        for i in range(25):
            results.link_issues.append(
                LinkIssue(
                    file=f"file{i}.md",
                    line=i + 1,
                    link_text=f"link{i}",
                    target=f"target{i}.md",
                    issue_type="broken_link",
                    issue_message=f"Not found {i}",
                )
            )
        report = build_documentation_scan_report(results)
        assert "Link Issues" in report
        # First 20 shown, then "and 5 more"
        assert "and 5 more" in report

    def test_with_quality_issues(self):
        results = _make_results()
        results.quality_issues.append(
            QualityIssue(
                file="doc.md", line=1, issue_type="fmt", issue_message="bad",
            )
        )
        report = build_documentation_scan_report(results)
        assert "1 quality issues" in report

    def test_with_improvements(self):
        results = _make_results()
        results.improvements_made.append({"type": "link_fix", "description": "Fixed link"})
        report = build_documentation_scan_report(results)
        assert "1 improvements" in report

    def test_completeness_gaps(self):
        from infrastructure.validation.docs.models import CompletenessGap

        results = _make_results()
        results.completeness_gaps.append(
            CompletenessGap(
                category="docs", item="README", description="Missing",
            )
        )
        report = build_documentation_scan_report(results)
        assert "1 completeness gaps" in report

    def test_recommendations_section(self):
        results = _make_results()
        report = build_documentation_scan_report(results)
        assert "## Recommendations" in report
        assert "Fix all broken links" in report
        assert "Next Review Recommended" in report
