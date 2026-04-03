"""Tests for infrastructure.reporting.coverage_json_parser — comprehensive coverage."""

import json

from infrastructure.reporting.coverage_json_parser import parse_coverage_json


class TestParseCoverageJson:
    def test_valid_coverage_file(self, tmp_path):
        data = {
            "files": {
                "module_a.py": {
                    "executed_lines": [1, 2, 3, 4, 5],
                    "missing_lines": [6, 7],
                    "excluded_lines": [8],
                },
                "module_b.py": {
                    "executed_lines": [1, 2, 3],
                    "missing_lines": [],
                    "excluded_lines": [],
                },
            }
        }
        f = tmp_path / "coverage.json"
        f.write_text(json.dumps(data))
        result = parse_coverage_json(f)
        assert result is not None
        assert result["total_executed"] == 8
        assert result["total_missing"] == 2
        assert result["total_excluded"] == 1
        assert result["total_lines"] == 11
        assert 70.0 < result["overall_coverage"] < 75.0

    def test_file_coverage_details(self, tmp_path):
        data = {
            "files": {
                "a.py": {
                    "executed_lines": [1, 2],
                    "missing_lines": [3],
                    "excluded_lines": [],
                }
            }
        }
        f = tmp_path / "coverage.json"
        f.write_text(json.dumps(data))
        result = parse_coverage_json(f)
        fc = result["file_coverage"]["a.py"]
        assert fc["executed_lines"] == 2
        assert fc["missing_lines"] == 1
        assert fc["total_lines"] == 3
        assert abs(fc["coverage_percent"] - 66.67) < 1.0

    def test_nonexistent_file(self, tmp_path):
        result = parse_coverage_json(tmp_path / "nonexistent.json")
        assert result is None

    def test_corrupt_json(self, tmp_path):
        f = tmp_path / "coverage.json"
        f.write_text("not valid json {{{")
        result = parse_coverage_json(f)
        assert result is None

    def test_empty_files_section(self, tmp_path):
        data = {"files": {}}
        f = tmp_path / "coverage.json"
        f.write_text(json.dumps(data))
        result = parse_coverage_json(f)
        assert result is not None
        assert result["overall_coverage"] == 0.0
        assert result["total_lines"] == 0

    def test_100_percent_coverage(self, tmp_path):
        data = {
            "files": {
                "perfect.py": {
                    "executed_lines": [1, 2, 3, 4, 5],
                    "missing_lines": [],
                    "excluded_lines": [],
                }
            }
        }
        f = tmp_path / "coverage.json"
        f.write_text(json.dumps(data))
        result = parse_coverage_json(f)
        assert result["overall_coverage"] == 100.0

    def test_zero_percent_coverage(self, tmp_path):
        data = {
            "files": {
                "empty.py": {
                    "executed_lines": [],
                    "missing_lines": [1, 2, 3],
                    "excluded_lines": [],
                }
            }
        }
        f = tmp_path / "coverage.json"
        f.write_text(json.dumps(data))
        result = parse_coverage_json(f)
        assert result["overall_coverage"] == 0.0

    def test_no_files_key(self, tmp_path):
        data = {"totals": {"percent_covered": 50}}
        f = tmp_path / "coverage.json"
        f.write_text(json.dumps(data))
        result = parse_coverage_json(f)
        assert result is not None
        assert result["total_lines"] == 0
