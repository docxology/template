#!/usr/bin/env python3
"""Comprehensive documentation scan and improvement analysis.

This script performs a systematic seven-step documentation scan:
1. Discovery and inventory
2. Accuracy verification
3. Completeness analysis
4. Quality assessment
5. Improvements
6. Verification and validation
7. Reporting
"""

import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from infrastructure.core.logging.utils import get_logger, log_header, log_success
from infrastructure.validation.docs.accuracy import verify_documentation_accuracy
from infrastructure.validation.docs.completeness import analyze_documentation_completeness
from infrastructure.validation.docs.discovery import (
    discover_documentation,
    discover_markdown_files,
)
from infrastructure.validation.docs.models import (
    CompletenessGap,
    DocumentationFile,
    LinkIssue,
    QualityIssue,
    ScanAccuracyIssue,
    ScanResults,
)
from infrastructure.validation.docs.quality import assess_documentation_quality
from infrastructure.validation.docs._docs_scan_report import build_documentation_scan_report
from infrastructure.validation.docs.verification import run_verification_checks


class AccuracyIssue(ScanAccuracyIssue):
    """Backward-compatible wrapper around :class:`ScanAccuracyIssue`."""

    def __init__(
        self,
        file: str,
        line: int,
        issue_type: str,
        issue_message: str,
        severity: str = "warning",
        details: str = "",
    ) -> None:
        super().__init__(
            category=issue_type,
            severity=severity,
            file=file,
            line=line,
            message=issue_message,
            details=details,
        )

    @property
    def issue_type(self) -> str:
        """Compatibility alias for the legacy field name."""
        return self.category

    @property
    def issue_message(self) -> str:
        """Compatibility alias for the legacy field name."""
        return self.message


__all__ = [
    "DocumentationScanner",
    "AccuracyIssue",
    "ScanAccuracyIssue",
    "CompletenessGap",
    "DocumentationFile",
    "LinkIssue",
    "QualityIssue",
    "ScanResults",
]

logger = get_logger(__name__)


class DocumentationScanner:
    """Main scanner class for comprehensive documentation analysis."""

    def __init__(self, repo_root: Path):
        """Initialize the scanner with repository root path."""
        self.repo_root = repo_root.resolve()
        self.results = ScanResults(scan_date=datetime.now().isoformat())
        self.all_headings: dict[str, set[str]] = {}
        self.script_files: list[Path] = []
        self.config_files: dict[str, Path] = {}
        self.documentation_structure: dict[str, list[str]] = defaultdict(list)

    def discover_inventory(self) -> dict[str, Any]:
        """Discovery and inventory."""

        inventory = discover_documentation(self.repo_root)

        # Update results
        self.results.documentation_files = inventory.get("documentation_files", [])
        self.results.total_files = inventory["markdown_files"]
        self.config_files = inventory["config_files_dict"]
        self.script_files = [self.repo_root / path for path in inventory["script_files_list"]]

        self.results.statistics["discovery"] = inventory
        return inventory

    def verify_accuracy(self) -> dict[str, Any]:
        """Accuracy verification."""
        md_files = discover_markdown_files(self.repo_root)

        accuracy_report, link_issues, accuracy_issues, all_headings = verify_documentation_accuracy(
            md_files, self.repo_root, self.config_files
        )

        self.results.link_issues.extend(link_issues)
        self.results.accuracy_issues.extend(accuracy_issues)
        self.all_headings = all_headings

        self.results.statistics["accuracy"] = accuracy_report
        return accuracy_report

    def analyze_completeness(self) -> dict[str, Any]:
        """Completeness analysis."""
        completeness_report, gaps = analyze_documentation_completeness(
            self.repo_root, self.results.documentation_files, self.config_files
        )

        self.results.completeness_gaps.extend(gaps)
        self.results.statistics["completeness"] = completeness_report
        return dict(completeness_report)

    def assess_quality(self) -> dict[str, Any]:
        """Quality assessment."""
        md_files = discover_markdown_files(self.repo_root)
        quality_report, quality_issues = assess_documentation_quality(md_files, self.repo_root)

        self.results.quality_issues.extend(quality_issues)
        self.results.statistics["quality"] = quality_report
        return quality_report

    def identify_improvements(self) -> dict[str, Any]:
        """Identify intelligent improvements."""
        logger.info("Identifying improvements...")

        improvements = []

        # Fix broken links
        link_fixes = self._identify_link_fixes()
        improvements.extend(link_fixes)

        # Identify other improvements
        other_improvements = self._identify_other_improvements()
        improvements.extend(other_improvements)

        self.results.improvements_made = improvements

        improvement_report = {
            "total_improvements": len(improvements),
            "link_fixes": len([i for i in improvements if i.get("type") == "link_fix"]),
            "content_updates": len([i for i in improvements if i.get("type") == "content_update"]),
            "structural_changes": len([i for i in improvements if i.get("type") == "structural"]),
        }

        self.results.statistics["improvements"] = improvement_report
        logger.info("  Identified %s improvements", len(improvements))
        return improvement_report

    def run_verification_checks(self) -> dict[str, Any]:
        """Verification and validation."""
        verification_results = run_verification_checks(self.repo_root)
        self.results.statistics["verification"] = verification_results
        return verification_results

    def build_scan_report(self) -> str:
        """Generate comprehensive report."""
        logger.info("Generating scan report...")
        return build_documentation_scan_report(self.results)

    def _identify_link_fixes(self) -> list[dict[str, Any]]:
        """Identify link fixes needed."""
        fixes = []
        for issue in self.results.link_issues:
            if issue.issue_type in ("broken_anchor", "broken_file"):
                fixes.append(
                    {
                        "type": "link_fix",
                        "file": issue.file,
                        "line": issue.line,
                        "target": issue.target,
                        "issue": issue.issue_message,
                    }
                )
        return fixes

    def _identify_other_improvements(self) -> list[dict[str, Any]]:
        """Identify other improvements needed."""
        improvements = []

        # Based on quality issues
        for issue in self.results.quality_issues:
            if issue.issue_type == "formatting" and "heading" in issue.issue_message.lower():
                improvements.append(
                    {
                        "type": "structural",
                        "file": issue.file,
                        "line": issue.line,
                        "description": issue.issue_message,
                    }
                )

        return improvements

    def run_full_scan(self) -> tuple[ScanResults, str]:
        """Run all steps of the documentation scan."""
        logger.info("Starting comprehensive documentation scan...")
        logger.info("=" * 60)

        self.discover_inventory()
        self.verify_accuracy()
        self.analyze_completeness()
        self.assess_quality()
        self.identify_improvements()
        self.run_verification_checks()
        report = self.build_scan_report()

        logger.info("=" * 60)
        logger.info("Scan complete!")

        return self.results, report


def main() -> int:
    """Execute comprehensive documentation scan and generate report.

    Discovers the repository root from the script location, runs a full
    documentation scan across all markdown files, and saves the report
    to docs/DOCUMENTATION_SCAN_REPORT.md.

    Returns:
        int: Exit code - 0 if no link or accuracy issues found, 1 otherwise.

    Raises:
        OSError: If report file cannot be written to the docs directory.
    """
    repo_root = Path(__file__).parent.parent.parent
    scanner = DocumentationScanner(repo_root)

    results, report = scanner.run_full_scan()

    # Save report
    report_path = repo_root / "docs" / "DOCUMENTATION_SCAN_REPORT.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    _tmp = report_path.with_suffix(report_path.suffix + ".tmp")
    try:
        _tmp.write_text(report, encoding="utf-8")
        _tmp.replace(report_path)
    except Exception:
        _tmp.unlink(missing_ok=True)
        raise
    log_success(f"Report saved to: {report_path}", logger)

    # Print summary
    log_header("SUMMARY", logger)
    logger.info(f"Total files scanned: {results.total_files}")
    logger.info(f"Link issues: {len(results.link_issues)}")
    logger.info(f"Accuracy issues: {len(results.accuracy_issues)}")
    logger.info(f"Completeness gaps: {len(results.completeness_gaps)}")
    logger.info(f"Quality issues: {len(results.quality_issues)}")
    logger.info(f"Improvements identified: {len(results.improvements_made)}")

    return 0 if len(results.link_issues) == 0 and len(results.accuracy_issues) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
