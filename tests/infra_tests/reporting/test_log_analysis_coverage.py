"""Tests for infrastructure.reporting.log_analysis — comprehensive coverage."""

import pytest

from infrastructure.reporting.log_analysis import (
    _tally_log_level_counts,
    _collect_log_statistics,
    generate_log_summary,
)


class TestTallyLogLevelCounts:
    def test_basic_counts(self, tmp_path):
        log = tmp_path / "test.log"
        log.write_text(
            "2024-01-01 DEBUG starting up\n"
            "2024-01-01 INFO application ready\n"
            "2024-01-01 WARNING memory usage high\n"
            "2024-01-01 ERROR connection failed\n"
            "2024-01-01 CRITICAL system down\n"
        )
        stats = _tally_log_level_counts(log)
        assert stats["counts"]["debug"] == 1
        assert stats["counts"]["info"] == 1
        assert stats["counts"]["warning"] == 1
        assert stats["counts"]["error"] == 1
        assert stats["counts"]["critical"] == 1
        assert stats["total_lines"] == 5

    def test_critical_before_error(self, tmp_path):
        log = tmp_path / "test.log"
        log.write_text("CRITICAL error in main loop\n")
        stats = _tally_log_level_counts(log)
        # "critical" is checked before "error", so this counts as critical
        assert stats["counts"]["critical"] == 1
        assert stats["counts"]["error"] == 0

    def test_warning_and_warn(self, tmp_path):
        log = tmp_path / "test.log"
        log.write_text("WARN deprecated call\nWARNING slow query\n")
        stats = _tally_log_level_counts(log)
        assert stats["counts"]["warning"] == 2

    def test_errors_collected(self, tmp_path):
        log = tmp_path / "test.log"
        lines = [f"ERROR failure {i}\n" for i in range(15)]
        log.write_text("".join(lines))
        stats = _tally_log_level_counts(log)
        assert stats["counts"]["error"] == 15
        assert len(stats["errors"]) == 10  # capped at 10

    def test_warnings_collected(self, tmp_path):
        log = tmp_path / "test.log"
        lines = [f"WARNING issue {i}\n" for i in range(15)]
        log.write_text("".join(lines))
        stats = _tally_log_level_counts(log)
        assert len(stats["warnings"]) == 10  # capped at 10

    def test_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            _tally_log_level_counts(tmp_path / "nonexistent.log")

    def test_empty_log(self, tmp_path):
        log = tmp_path / "empty.log"
        log.write_text("")
        stats = _tally_log_level_counts(log)
        assert stats["total_lines"] == 0
        assert all(v == 0 for v in stats["counts"].values())

    def test_no_recognized_levels(self, tmp_path):
        log = tmp_path / "plain.log"
        log.write_text("just some text\nmore text\n")
        stats = _tally_log_level_counts(log)
        assert stats["total_lines"] == 2
        assert all(v == 0 for v in stats["counts"].values())

    def test_critical_added_to_errors_list(self, tmp_path):
        log = tmp_path / "crit.log"
        log.write_text("CRITICAL system failure\n")
        stats = _tally_log_level_counts(log)
        assert len(stats["errors"]) == 1
        assert "CRITICAL" in stats["errors"][0]


class TestCollectLogStatistics:
    def test_backward_compat(self, tmp_path):
        log = tmp_path / "test.log"
        log.write_text("INFO ready\n")
        result = _collect_log_statistics(log)
        assert result["counts"]["info"] == 1


class TestGenerateLogSummary:
    def test_basic_summary(self, tmp_path):
        log = tmp_path / "test.log"
        log.write_text(
            "INFO starting\n"
            "ERROR something broke\n"
            "WARNING be careful\n"
        )
        summary = generate_log_summary(log)
        assert summary is not None
        assert "LOG ANALYSIS" in summary
        assert "test.log" in summary
        assert "Total Lines: 3" in summary
        assert "INFO: 1" in summary
        assert "ERROR: 1" in summary
        assert "WARNING: 1" in summary

    def test_with_output_file(self, tmp_path):
        log = tmp_path / "test.log"
        log.write_text("INFO ready\n")
        out = tmp_path / "reports" / "summary.txt"
        summary = generate_log_summary(log, output_file=out)
        assert out.exists()
        assert out.read_text() == summary

    def test_nonexistent_file(self, tmp_path):
        result = generate_log_summary(tmp_path / "missing.log")
        assert result is None

    def test_errors_shown_in_summary(self, tmp_path):
        log = tmp_path / "test.log"
        log.write_text("ERROR connection timeout\nERROR disk full\n")
        summary = generate_log_summary(log)
        assert "Recent Errors" in summary
        assert "connection timeout" in summary

    def test_warnings_shown_in_summary(self, tmp_path):
        log = tmp_path / "test.log"
        log.write_text("WARNING slow query detected\n")
        summary = generate_log_summary(log)
        assert "Recent Warnings" in summary
        assert "slow query" in summary

    def test_only_nonzero_levels_shown(self, tmp_path):
        log = tmp_path / "test.log"
        log.write_text("INFO only info here\n")
        summary = generate_log_summary(log)
        assert "INFO: 1" in summary
        assert "DEBUG" not in summary
        assert "ERROR" not in summary
