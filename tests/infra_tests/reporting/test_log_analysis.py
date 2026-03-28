"""Tests for infrastructure/reporting/log_analysis.py."""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.reporting.log_analysis import _collect_log_statistics, generate_log_summary


class TestCollectLogStatistics:
    """Tests for _collect_log_statistics."""

    def test_counts_debug_lines(self, tmp_path: Path) -> None:
        """Lines containing 'debug' increment the debug counter."""
        log = tmp_path / "pipeline.log"
        log.write_text("DEBUG: starting stage\nINFO: stage done\n")
        stats = _collect_log_statistics(log)
        assert stats["counts"]["debug"] == 1
        assert stats["counts"]["info"] == 1

    def test_counts_warning_lines(self, tmp_path: Path) -> None:
        """Lines containing 'warning' or 'warn' increment the warning counter."""
        log = tmp_path / "pipeline.log"
        log.write_text("WARNING: low disk\nwarn: retrying\n")
        stats = _collect_log_statistics(log)
        assert stats["counts"]["warning"] == 2
        assert len(stats["warnings"]) == 2

    def test_counts_error_lines(self, tmp_path: Path) -> None:
        """Lines containing 'error' increment the error counter and populate errors list."""
        log = tmp_path / "pipeline.log"
        log.write_text("ERROR: file not found\nERROR: timeout\n")
        stats = _collect_log_statistics(log)
        assert stats["counts"]["error"] == 2
        assert len(stats["errors"]) == 2

    def test_counts_critical_lines(self, tmp_path: Path) -> None:
        """Lines containing 'critical' increment the critical counter."""
        log = tmp_path / "pipeline.log"
        log.write_text("CRITICAL: disk full\n")
        stats = _collect_log_statistics(log)
        assert stats["counts"]["critical"] == 1

    def test_total_lines(self, tmp_path: Path) -> None:
        """total_lines equals the number of lines in the file."""
        log = tmp_path / "pipeline.log"
        log.write_text("line1\nline2\nline3\n")
        stats = _collect_log_statistics(log)
        assert stats["total_lines"] == 3

    def test_warnings_capped_at_10(self, tmp_path: Path) -> None:
        """warnings list is capped at 10 entries."""
        log = tmp_path / "pipeline.log"
        log.write_text("\n".join(f"WARNING: msg{i}" for i in range(15)) + "\n")
        stats = _collect_log_statistics(log)
        assert stats["counts"]["warning"] == 15
        assert len(stats["warnings"]) == 10

    def test_raises_for_missing_file(self, tmp_path: Path) -> None:
        """FileNotFoundError raised when the file does not exist."""
        with pytest.raises(FileNotFoundError):
            _collect_log_statistics(tmp_path / "nonexistent.log")

    def test_empty_file(self, tmp_path: Path) -> None:
        """Empty log file produces zero counts."""
        log = tmp_path / "empty.log"
        log.write_text("")
        stats = _collect_log_statistics(log)
        assert stats["total_lines"] == 0
        assert all(v == 0 for v in stats["counts"].values())


class TestGenerateLogSummary:
    """Tests for generate_log_summary."""

    def test_returns_string_for_valid_file(self, tmp_path: Path) -> None:
        """Returns a non-empty string for a readable log file."""
        log = tmp_path / "pipeline.log"
        log.write_text("INFO: pipeline started\nERROR: render failed\n")
        result = generate_log_summary(log)
        assert isinstance(result, str)
        assert "pipeline.log" in result
        assert "ERROR" in result

    def test_returns_none_for_missing_file(self, tmp_path: Path) -> None:
        """Returns None when the log file does not exist."""
        result = generate_log_summary(tmp_path / "missing.log")
        assert result is None

    def test_writes_output_file(self, tmp_path: Path) -> None:
        """Writes summary to output_file when provided."""
        log = tmp_path / "pipeline.log"
        log.write_text("INFO: done\n")
        out = tmp_path / "summary" / "log_summary.txt"
        generate_log_summary(log, output_file=out)
        assert out.exists()
        assert "pipeline.log" in out.read_text()

    def test_summary_includes_total_lines(self, tmp_path: Path) -> None:
        """Summary text includes the total line count."""
        log = tmp_path / "pipeline.log"
        log.write_text("INFO: a\nINFO: b\nINFO: c\n")
        result = generate_log_summary(log)
        assert result is not None
        assert "Total Lines: 3" in result

    def test_no_errors_section_when_clean(self, tmp_path: Path) -> None:
        """Summary omits 'Recent Errors' section when there are none."""
        log = tmp_path / "pipeline.log"
        log.write_text("INFO: all good\n")
        result = generate_log_summary(log)
        assert result is not None
        assert "Recent Errors" not in result
