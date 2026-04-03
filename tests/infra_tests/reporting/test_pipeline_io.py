"""Tests for infrastructure.reporting.pipeline_io — comprehensive coverage."""

import json

from infrastructure.reporting.pipeline_io import (
    _atomic_write_json,
    _atomic_write_text,
    generate_error_markdown,
    generate_validation_markdown,
    save_error_summary,
    save_performance_report,
    save_test_results,
    save_validation_report,
)


class TestAtomicWriteJson:
    def test_writes_valid_json(self, tmp_path):
        path = tmp_path / "data.json"
        _atomic_write_json(path, {"key": "value", "num": 42})
        data = json.loads(path.read_text())
        assert data["key"] == "value"
        assert data["num"] == 42

    def test_no_tmp_file_left(self, tmp_path):
        path = tmp_path / "data.json"
        _atomic_write_json(path, {"a": 1})
        assert not (tmp_path / "data.json.tmp").exists()

    def test_overwrites_existing(self, tmp_path):
        path = tmp_path / "data.json"
        path.write_text('{"old": true}')
        _atomic_write_json(path, {"new": True})
        data = json.loads(path.read_text())
        assert data["new"] is True


class TestAtomicWriteText:
    def test_writes_text(self, tmp_path):
        path = tmp_path / "file.txt"
        _atomic_write_text(path, "Hello, World!")
        assert path.read_text() == "Hello, World!"

    def test_no_tmp_file_left(self, tmp_path):
        path = tmp_path / "file.txt"
        _atomic_write_text(path, "content")
        assert not (tmp_path / "file.txt.tmp").exists()


class TestSaveTestResults:
    def test_creates_file(self, tmp_path):
        results = {"total": 100, "passed": 95, "failed": 5}
        path = save_test_results(results, tmp_path)
        assert path.exists()
        assert path.name == "test_results.json"
        data = json.loads(path.read_text())
        assert data["total"] == 100

    def test_creates_directory(self, tmp_path):
        out_dir = tmp_path / "nested" / "output"
        save_test_results({"x": 1}, out_dir)
        assert out_dir.exists()


class TestSaveValidationReport:
    def test_creates_json_and_markdown(self, tmp_path):
        results = {"checks": {"pdf_valid": True, "links_ok": False}}
        saved = save_validation_report(results, tmp_path)
        assert "json" in saved
        assert "markdown" in saved
        assert saved["json"].exists()
        assert saved["markdown"].exists()

    def test_json_content(self, tmp_path):
        results = {"checks": {"test_a": True}}
        saved = save_validation_report(results, tmp_path)
        data = json.loads(saved["json"].read_text())
        assert data["checks"]["test_a"] is True

    def test_markdown_content(self, tmp_path):
        results = {"checks": {"pdf_check": True, "link_check": False}}
        saved = save_validation_report(results, tmp_path)
        md = saved["markdown"].read_text()
        assert "Validation Report" in md
        assert "PASS" in md
        assert "FAIL" in md


class TestGenerateValidationMarkdown:
    def test_with_checks(self):
        results = {"checks": {"a": True, "b": False}}
        md = generate_validation_markdown(results)
        assert "Validation Report" in md
        assert "Validation Checks" in md

    def test_without_checks(self):
        md = generate_validation_markdown({})
        assert "Validation Report" in md
        assert "Validation Checks" not in md


class TestSavePerformanceReport:
    def test_creates_json_file(self, tmp_path):
        metrics = {"cpu_time": 10.5, "memory_peak_mb": 256.0}
        path = save_performance_report(metrics, tmp_path)
        assert path.exists()
        assert path.name == "performance_report.json"
        data = json.loads(path.read_text())
        assert data["cpu_time"] == 10.5


class TestSaveErrorSummary:
    def test_aggregates_errors(self, tmp_path):
        errors = [
            {"type": "import", "message": "Module not found"},
            {"type": "import", "message": "Another import error"},
            {"type": "runtime", "message": "Timeout"},
        ]
        summary = save_error_summary(errors, tmp_path)
        assert summary["total_errors"] == 3
        assert summary["errors_by_type"]["import"] == 2
        assert summary["errors_by_type"]["runtime"] == 1

    def test_creates_files(self, tmp_path):
        errors = [{"type": "test", "message": "Failed assertion"}]
        save_error_summary(errors, tmp_path)
        assert (tmp_path / "error_summary.json").exists()
        assert (tmp_path / "error_summary.md").exists()

    def test_empty_errors(self, tmp_path):
        summary = save_error_summary([], tmp_path)
        assert summary["total_errors"] == 0
        assert summary["errors_by_type"] == {}


class TestGenerateErrorMarkdown:
    def test_basic_structure(self):
        summary = {
            "total_errors": 2,
            "errors_by_type": {"import": 1, "runtime": 1},
            "errors": [
                {"type": "import", "message": "Module X not found"},
                {"type": "runtime", "message": "Timeout after 10s"},
            ],
        }
        md = generate_error_markdown(summary)
        assert "Error Summary" in md
        assert "Total Errors" in md
        assert "2" in md
        assert "import" in md
        assert "runtime" in md

    def test_with_file_and_suggestions(self):
        summary = {
            "total_errors": 1,
            "errors_by_type": {"test": 1},
            "errors": [
                {
                    "type": "test",
                    "message": "AssertionError",
                    "file": "test_foo.py",
                    "suggestions": ["Check assertions", "Review test data"],
                }
            ],
        }
        md = generate_error_markdown(summary)
        assert "test_foo.py" in md
        assert "Check assertions" in md

    def test_truncation_over_10_errors(self):
        errors = [{"type": "test", "message": f"Error {i}"} for i in range(15)]
        summary = {"total_errors": 15, "errors_by_type": {"test": 15}, "errors": errors}
        md = generate_error_markdown(summary)
        assert "and 5 more errors" in md

    def test_empty_summary(self):
        summary = {"total_errors": 0}
        md = generate_error_markdown(summary)
        assert "Error Summary" in md
        assert "0" in md
