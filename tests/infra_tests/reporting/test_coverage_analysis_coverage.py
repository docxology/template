"""Tests for infrastructure.reporting.coverage_analysis — comprehensive coverage."""

from infrastructure.reporting.coverage_analysis import (
    format_coverage_status,
    analyze_coverage_gaps,
    format_failure_suggestions,
)


class TestFormatCoverageStatus:
    def test_above_threshold(self):
        result = format_coverage_status(85.0, 80.0)
        assert "85.0%" in result
        assert "meets" in result

    def test_close_to_threshold(self):
        # 90% of 80 = 72, so 75% is close
        result = format_coverage_status(75.0, 80.0)
        assert "75.0%" in result
        assert "close" in result

    def test_below_threshold(self):
        # 80% of 80 = 64, so 66% is below but not significantly
        result = format_coverage_status(66.0, 80.0)
        assert "66.0%" in result
        assert "below" in result

    def test_significantly_below(self):
        # Below 80% of threshold
        result = format_coverage_status(50.0, 80.0)
        assert "50.0%" in result
        assert "significantly" in result

    def test_exact_threshold(self):
        result = format_coverage_status(80.0, 80.0)
        assert "meets" in result


class TestAnalyzeCoverageGaps:
    def test_above_threshold_no_suggestions(self):
        results = {"coverage_percent": 90.0}
        suggestions = analyze_coverage_gaps(results, 80.0, "infrastructure", {})
        assert suggestions == []

    def test_below_threshold_basic(self):
        results = {"coverage_percent": 70.0}
        suggestions = analyze_coverage_gaps(results, 80.0, "infrastructure", {})
        assert len(suggestions) > 0
        assert any("10.0%" in s for s in suggestions)

    def test_with_file_coverage_data(self):
        results = {"coverage_percent": 60.0}
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
                            "coverage_percent": 40.0,
                            "total_lines": 200,
                            "missing_lines": 120,
                        },
                    }
                }
            }
        }
        suggestions = analyze_coverage_gaps(results, 80.0, "infrastructure", report)
        assert any("needing attention" in s for s in suggestions)
        assert any("module_a.py" in s for s in suggestions)

    def test_with_substantial_files(self):
        results = {"coverage_percent": 60.0}
        report = {
            "coverage_details": {
                "infrastructure": {
                    "file_coverage": {
                        "big_module.py": {
                            "coverage_percent": 50.0,
                            "total_lines": 500,
                            "missing_lines": 250,
                        },
                    }
                }
            }
        }
        suggestions = analyze_coverage_gaps(results, 80.0, "infrastructure", report)
        assert any("High-impact" in s for s in suggestions)

    def test_no_file_coverage_data(self):
        results = {"coverage_percent": 60.0}
        suggestions = analyze_coverage_gaps(results, 80.0, "infrastructure", {})
        assert any("cov-report=json" in s for s in suggestions)


class TestFormatFailureSuggestions:
    def test_import_errors_infra(self):
        failed = [{"error_type": "ImportError", "error_message": "No module named 'foo'"}]
        result = format_failure_suggestions(failed, "infrastructure")
        assert any("dependencies" in s for s in result)
        assert any("PYTHONPATH" in s for s in result)

    def test_import_errors_project(self):
        failed = [{"error_type": "ImportError", "error_message": "No module found"}]
        result = format_failure_suggestions(failed, "project", "my_project")
        assert any("pyproject.toml" in s for s in result)

    def test_assertion_errors_project(self):
        failed = [{"error_type": "AssertionError", "error_message": "1 != 2"}]
        result = format_failure_suggestions(failed, "project", "my_project")
        assert any("assertions" in s for s in result)

    def test_assertion_errors_infra_no_special(self):
        failed = [{"error_type": "AssertionError", "error_message": "1 != 2"}]
        result = format_failure_suggestions(failed, "infrastructure")
        # Infrastructure doesn't get assertion-specific suggestions
        assert not any("assertions" in s and "Review" in s for s in result)

    def test_coverage_errors(self):
        failed = [{"error_type": "DataError", "error_message": "coverage database issue"}]
        result = format_failure_suggestions(failed, "infrastructure")
        assert any("coverage" in s.lower() for s in result)

    def test_timeout_errors(self):
        failed = [{"error_type": "TimeoutError", "error_message": "test timeout"}]
        result = format_failure_suggestions(failed, "infrastructure")
        assert any("timeout" in s.lower() for s in result)

    def test_infra_general_suggestions(self):
        result = format_failure_suggestions([], "infrastructure")
        assert any("infra_tests" in s for s in result)

    def test_project_general_suggestions(self):
        result = format_failure_suggestions([], "project", "my_proj")
        assert any("my_proj" in s for s in result)
