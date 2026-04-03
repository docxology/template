"""Tests for infrastructure.reporting.coverage_analysis module.

Tests coverage formatting, gap analysis, and failure suggestion generation.
"""

from __future__ import annotations


from infrastructure.reporting.coverage_analysis import (
    analyze_coverage_gaps,
    format_coverage_status,
    format_failure_suggestions,
)


class TestFormatCoverageStatus:
    """Tests for format_coverage_status."""

    def test_meets_threshold(self):
        result = format_coverage_status(85.0, 60.0)
        assert "85.0%" in result
        assert "meets" in result

    def test_exactly_at_threshold(self):
        result = format_coverage_status(60.0, 60.0)
        assert "60.0%" in result
        assert "meets" in result

    def test_close_to_threshold(self):
        # 90% of 60 = 54, so 55% should be "close"
        result = format_coverage_status(55.0, 60.0)
        assert "55.0%" in result
        assert "close" in result

    def test_below_threshold(self):
        # 80% of 60 = 48, so 50% should be "below" but not "significantly"
        result = format_coverage_status(50.0, 60.0)
        assert "50.0%" in result
        assert "below" in result

    def test_significantly_below_threshold(self):
        # Below 80% of threshold
        result = format_coverage_status(30.0, 60.0)
        assert "30.0%" in result
        assert "significantly below" in result

    def test_zero_coverage(self):
        result = format_coverage_status(0.0, 60.0)
        assert "0.0%" in result
        assert "significantly below" in result

    def test_100_percent_coverage(self):
        result = format_coverage_status(100.0, 90.0)
        assert "100.0%" in result
        assert "meets" in result


class TestAnalyzeCoverageGaps:
    """Tests for analyze_coverage_gaps."""

    def test_no_gaps_when_above_threshold(self):
        results = {"coverage_percent": 85.0}
        report: dict = {}
        suggestions = analyze_coverage_gaps(results, 60.0, "Infrastructure", report)
        assert suggestions == []

    def test_gap_suggestions_below_threshold(self):
        results = {"coverage_percent": 40.0}
        report: dict = {}
        suggestions = analyze_coverage_gaps(results, 60.0, "Infrastructure", report)
        assert len(suggestions) > 0
        assert any("20.0%" in s for s in suggestions)

    def test_gap_with_file_coverage_details(self):
        results = {"coverage_percent": 50.0}
        report = {
            "coverage_details": {
                "infrastructure": {
                    "file_coverage": {
                        "module_a.py": {
                            "coverage_percent": 30.0,
                            "total_lines": 50,
                            "missing_lines": 35,
                        },
                        "module_b.py": {
                            "coverage_percent": 10.0,
                            "total_lines": 200,
                            "missing_lines": 180,
                        },
                    }
                }
            }
        }
        suggestions = analyze_coverage_gaps(results, 60.0, "Infrastructure", report)
        # Should have file-specific suggestions
        assert any("Files needing attention" in s for s in suggestions)

    def test_gap_with_substantial_files(self):
        results = {"coverage_percent": 50.0}
        report = {
            "coverage_details": {
                "infrastructure": {
                    "file_coverage": {
                        "big_module.py": {
                            "coverage_percent": 40.0,
                            "total_lines": 200,
                            "missing_lines": 120,
                        },
                    }
                }
            }
        }
        suggestions = analyze_coverage_gaps(results, 60.0, "Infrastructure", report)
        assert any("High-impact" in s for s in suggestions)

    def test_gap_without_file_coverage(self):
        results = {"coverage_percent": 50.0}
        report = {"coverage_details": {"infrastructure": {}}}
        suggestions = analyze_coverage_gaps(results, 60.0, "Infrastructure", report)
        assert any("--cov-report=json" in s for s in suggestions)

    def test_always_includes_target_suggestion(self):
        results = {"coverage_percent": 50.0}
        report: dict = {}
        suggestions = analyze_coverage_gaps(results, 60.0, "Infrastructure", report)
        assert any("Target" in s for s in suggestions)
        assert any("htmlcov" in s for s in suggestions)


class TestFormatFailureSuggestions:
    """Tests for format_failure_suggestions."""

    def test_empty_failures(self):
        suggestions = format_failure_suggestions([], "infrastructure")
        # Should still have general debug commands
        assert any("Run individual" in s for s in suggestions)

    def test_import_errors_infrastructure(self):
        # The function checks "import" (lowercase) in str(dict)
        failures = [{"error": "failed import: No module named 'foo'"}]
        suggestions = format_failure_suggestions(failures, "infrastructure")
        assert any("Missing dependencies" in s for s in suggestions)

    def test_import_errors_project(self):
        # "module" check is case-insensitive via .lower()
        failures = [{"error": "ModuleNotFoundError: No module named 'bar'"}]
        suggestions = format_failure_suggestions(failures, "project", "my_project")
        assert any("pyproject.toml" in s for s in suggestions)

    def test_assertion_errors_project(self):
        failures = [{"error": "AssertionError: expected 5 got 3"}]
        suggestions = format_failure_suggestions(failures, "project", "my_project")
        assert any("assertions" in s for s in suggestions)

    def test_assertion_errors_infrastructure_no_suggestion(self):
        failures = [{"error": "AssertionError: expected 5 got 3"}]
        suggestions = format_failure_suggestions(failures, "infrastructure")
        # Infrastructure assertion errors don't get special suggestions
        assert not any("assertions" in s for s in suggestions)

    def test_coverage_errors(self):
        failures = [{"error": "CoverageException: DataError: no such table"}]
        suggestions = format_failure_suggestions(failures, "infrastructure")
        assert any("database corruption" in s.lower() or "coverage" in s.lower() for s in suggestions)

    def test_timeout_errors_infrastructure(self):
        failures = [{"error": "Timeout: test took too long"}]
        suggestions = format_failure_suggestions(failures, "infrastructure")
        assert any("timeout" in s.lower() for s in suggestions)
        assert any("durations" in s for s in suggestions)

    def test_timeout_errors_project(self):
        failures = [{"error": "Timeout: test took too long"}]
        suggestions = format_failure_suggestions(failures, "project", "my_project")
        assert any("my_project" in s for s in suggestions)

    def test_multiple_error_types(self):
        # Note: the function checks "import" (lowercase) in str(dict),
        # and "module" in str(dict).lower() -- use lowercase import to match
        failures = [
            {"error": "failed to import module foo"},
            {"error": "Timeout: bar"},
            {"error": "CoverageException: dataerror: no such table"},
        ]
        suggestions = format_failure_suggestions(failures, "infrastructure")
        joined = "\n".join(suggestions).lower()
        assert "dependencies" in joined or "import" in joined
        assert "timeout" in joined
        assert "coverage" in joined

    def test_infrastructure_debug_commands(self):
        suggestions = format_failure_suggestions([], "infrastructure")
        assert any("infra_tests" in s for s in suggestions)

    def test_project_debug_commands(self):
        suggestions = format_failure_suggestions([], "project", "test_proj")
        assert any("test_proj" in s for s in suggestions)
