"""Tests for infrastructure.reporting.coverage_json_parser — comprehensive coverage."""

import json

from infrastructure.reporting.coverage_json_parser import parse_coverage_json


class TestParseCoverageJson:
    def test_basic_parsing(self, tmp_path):
        cov_file = tmp_path / "coverage.json"
        cov_file.write_text(json.dumps({
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
        }))
        result = parse_coverage_json(cov_file)
        assert result is not None
        assert result["total_executed"] == 8
        assert result["total_missing"] == 2
        assert result["total_excluded"] == 1
        assert result["total_lines"] == 11
        assert abs(result["overall_coverage"] - (8 / 11 * 100)) < 0.1

        # Check file-level
        assert "module_a.py" in result["file_coverage"]
        assert result["file_coverage"]["module_a.py"]["executed_lines"] == 5
        assert result["file_coverage"]["module_a.py"]["missing_lines"] == 2

    def test_nonexistent_file(self, tmp_path):
        result = parse_coverage_json(tmp_path / "missing.json")
        assert result is None

    def test_corrupt_json(self, tmp_path):
        cov_file = tmp_path / "coverage.json"
        cov_file.write_text("{bad json")
        result = parse_coverage_json(cov_file)
        assert result is None

    def test_empty_files(self, tmp_path):
        cov_file = tmp_path / "coverage.json"
        cov_file.write_text(json.dumps({"files": {}}))
        result = parse_coverage_json(cov_file)
        assert result is not None
        assert result["overall_coverage"] == 0.0
        assert result["total_lines"] == 0

    def test_no_files_key(self, tmp_path):
        cov_file = tmp_path / "coverage.json"
        cov_file.write_text(json.dumps({"totals": {"percent_covered": 80}}))
        result = parse_coverage_json(cov_file)
        assert result is not None
        assert result["total_lines"] == 0

    def test_file_with_zero_lines(self, tmp_path):
        cov_file = tmp_path / "coverage.json"
        cov_file.write_text(json.dumps({
            "files": {
                "empty.py": {
                    "executed_lines": [],
                    "missing_lines": [],
                    "excluded_lines": [],
                }
            }
        }))
        result = parse_coverage_json(cov_file)
        assert result is not None
        assert result["file_coverage"]["empty.py"]["coverage_percent"] == 0.0
