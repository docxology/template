"""End-to-end pipeline integration tests with structured log assertions.

Executes scripts/execute_pipeline.py against a minimal test project and
validates completion using structured JSON log output. All tests use real
implementations — no mocks or fakes.
"""

from __future__ import annotations

import os
import sys
import subprocess
from pathlib import Path

import pytest

from tests.helpers.log_parser import (
    LogEntry,
    contains_message,
    filter_by_level,
    parse_structured_logs,
)

# Repository root
ROOT = Path(__file__).parent.parent.parent.resolve()


class TestFullPipelineStructuredLogs:
    """Test full pipeline execution with structured log assertions."""

    @pytest.fixture
    def minimal_project(self, tmp_path: Path) -> Path:
        """Create a minimal project structure for pipeline testing.

        Returns:
            Path to the tmp repo root with projects/<name>/ structure.
        """
        repo = tmp_path / "repo"
        repo.mkdir()

        # Create project structure at projects/test_project/
        project = repo / "projects" / "test_project"
        project.mkdir(parents=True)

        # Manuscript
        manuscript = project / "manuscript"
        manuscript.mkdir()
        (manuscript / "01_abstract.md").write_text(
            "# Abstract\n\nMinimal test abstract for pipeline validation.\n"
        )
        (manuscript / "config.yaml").write_text(
            "paper:\n  title: Pipeline Integration Test\n"
            "authors:\n  - name: Test Author\n"
            "testing:\n  infra_coverage_threshold: 0\n  project_coverage_threshold: 0\n"
        )

        # Source code
        src = project / "src"
        src.mkdir()
        (src / "__init__.py").write_text("")
        (src / "core.py").write_text(
            'def compute(x: int) -> int:\n    """Compute double of x."""\n    return x * 2\n'
        )

        # Tests
        tests = project / "tests"
        tests.mkdir()
        (tests / "__init__.py").write_text("")
        (tests / "test_core.py").write_text(
            "from src.core import compute\n\ndef test_compute():\n    assert compute(5) == 10\n"
        )

        # Output directories
        output = project / "output"
        for subdir in ["pdf", "figures", "data", "web", "slides", "reports", "logs"]:
            (output / subdir).mkdir(parents=True)

        return repo

    def test_pipeline_produces_structured_logs(self, minimal_project: Path):
        """Test that pipeline emits parseable structured JSON logs."""
        env = os.environ.copy()
        env["STRUCTURED_LOGGING"] = "true"
        env["LOG_LEVEL"] = "0"  # DEBUG for maximum visibility
        env["PYTHONPATH"] = str(ROOT)

        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "execute_pipeline.py"),
                "--project",
                "test_project",
                "--skip-infra",
                "--core-only",
            ],
            cwd=str(minimal_project),
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )

        # Parse structured logs from combined output
        all_output = result.stdout + "\n" + result.stderr
        logs = parse_structured_logs(all_output)

        # Should have at least some log entries
        assert len(logs) > 0, (
            f"No structured log entries found. stdout={result.stdout[:500]}, "
            f"stderr={result.stderr[:500]}"
        )

        # All entries should have valid structure
        for entry in logs:
            assert entry.timestamp, f"Missing timestamp in {entry}"
            assert entry.level, f"Missing level in {entry}"
            assert entry.logger, f"Missing logger in {entry}"

    def test_pipeline_logs_contain_expected_levels(self, minimal_project: Path):
        """Test that pipeline produces logs at INFO level or above."""
        env = os.environ.copy()
        env["STRUCTURED_LOGGING"] = "true"
        env["LOG_LEVEL"] = "1"
        env["PYTHONPATH"] = str(ROOT)

        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "execute_pipeline.py"),
                "--project",
                "test_project",
                "--skip-infra",
                "--core-only",
            ],
            cwd=str(minimal_project),
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )

        logs = parse_structured_logs(result.stdout + "\n" + result.stderr)
        info_logs = filter_by_level(logs, "INFO")

        # Pipeline should produce INFO-level logs
        assert len(info_logs) > 0, "Pipeline produced no INFO-level logs"


class TestLogParserUnit:
    """Unit tests for the log parser helper itself."""

    def test_parse_valid_json_lines(self):
        """Test parsing valid JSON log lines."""
        output = (
            '{"timestamp": "2026-01-01T00:00:00", "level": "INFO", '
            '"logger": "test", "message": "hello"}\n'
            '{"timestamp": "2026-01-01T00:00:01", "level": "ERROR", '
            '"logger": "test", "message": "oops"}\n'
        )
        logs = parse_structured_logs(output)
        assert len(logs) == 2
        assert logs[0].level == "INFO"
        assert logs[0].message == "hello"
        assert logs[1].level == "ERROR"

    def test_parse_skips_non_json_lines(self):
        """Test that non-JSON lines are silently skipped."""
        output = (
            "Plain text line\n"
            '{"timestamp": "2026-01-01", "level": "INFO", '
            '"logger": "t", "message": "ok"}\n'
            "Another plain line\n"
        )
        logs = parse_structured_logs(output)
        assert len(logs) == 1
        assert logs[0].message == "ok"

    def test_parse_empty_output(self):
        """Test parsing empty output."""
        assert parse_structured_logs("") == []
        assert parse_structured_logs("\n\n") == []

    def test_filter_by_level(self):
        """Test filtering entries by level."""
        entries = [
            LogEntry("t1", "INFO", "a", "msg1"),
            LogEntry("t2", "ERROR", "b", "msg2"),
            LogEntry("t3", "INFO", "c", "msg3"),
        ]
        info = filter_by_level(entries, "INFO")
        assert len(info) == 2
        error = filter_by_level(entries, "ERROR")
        assert len(error) == 1

    def test_contains_message(self):
        """Test message substring search."""
        entries = [
            LogEntry("t1", "INFO", "a", "Pipeline started"),
            LogEntry("t2", "INFO", "a", "All stages complete"),
        ]
        assert contains_message(entries, "Pipeline")
        assert contains_message(entries, "complete")
        assert not contains_message(entries, "missing")

    def test_log_entry_is_frozen(self):
        """Test that LogEntry is immutable."""
        entry = LogEntry("t", "INFO", "logger", "msg")
        with pytest.raises(AttributeError):
            entry.message = "changed"  # type: ignore
