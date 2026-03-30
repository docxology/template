"""Tests for infrastructure/core/logging_formatters.py.

Tests JSONFormatter and TemplateFormatter with real log records.
No mocks — uses actual logging.LogRecord objects.
"""

from __future__ import annotations

import json
import logging

from infrastructure.core.logging.formatters import (
    JSONFormatter,
    TemplateFormatter,
    EMOJIS,
)


def make_record(
    message: str,
    level: int = logging.INFO,
    name: str = "test.logger",
    exc_info=None,
) -> logging.LogRecord:
    """Create a real LogRecord for testing."""
    record = logging.LogRecord(
        name=name,
        level=level,
        pathname="test_file.py",
        lineno=42,
        msg=message,
        args=(),
        exc_info=exc_info,
    )
    return record


class TestJSONFormatter:
    """Test JSONFormatter produces valid, structured JSON output."""

    def setup_method(self):
        self.formatter = JSONFormatter()

    def test_basic_output_is_valid_json(self):
        """Format produces parseable JSON."""
        record = make_record("Hello world")
        output = self.formatter.format(record)
        data = json.loads(output)
        assert isinstance(data, dict)

    def test_json_has_required_fields(self):
        """JSON output contains timestamp, level, logger, message."""
        record = make_record("Test message", level=logging.WARNING, name="my.module")
        data = json.loads(self.formatter.format(record))
        assert "timestamp" in data
        assert "level" in data
        assert "logger" in data
        assert "message" in data

    def test_json_level_is_correct(self):
        """Level field reflects the actual log level name."""
        for level, name in [(logging.DEBUG, "DEBUG"), (logging.ERROR, "ERROR"), (logging.INFO, "INFO")]:
            record = make_record("msg", level=level)
            data = json.loads(self.formatter.format(record))
            assert data["level"] == name

    def test_json_message_matches(self):
        """Message field matches the log message."""
        record = make_record("My specific message")
        data = json.loads(self.formatter.format(record))
        assert data["message"] == "My specific message"

    def test_json_logger_name(self):
        """Logger field matches the record's logger name."""
        record = make_record("msg", name="infrastructure.core.pipeline")
        data = json.loads(self.formatter.format(record))
        assert data["logger"] == "infrastructure.core.pipeline"

    def test_json_no_exception_field_when_none(self):
        """No 'exception' key when record has no exception info."""
        record = make_record("Normal message")
        data = json.loads(self.formatter.format(record))
        assert "exception" not in data

    def test_json_exception_field_when_present(self):
        """'exception' key present when record carries exception info."""
        try:
            raise ValueError("test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()

        record = make_record("Error occurred", exc_info=exc_info)
        data = json.loads(self.formatter.format(record))
        assert "exception" in data
        assert "ValueError" in data["exception"]

    def test_json_extra_fields_included(self):
        """Extra fields on record are included in JSON output."""
        record = make_record("msg")
        record.extra_fields = {"request_id": "abc123", "user": "daniel"}
        data = json.loads(self.formatter.format(record))
        assert data["request_id"] == "abc123"
        assert data["user"] == "daniel"

    def test_json_timestamp_is_iso_format(self):
        """Timestamp is an ISO 8601 formatted string."""
        record = make_record("msg")
        data = json.loads(self.formatter.format(record))
        # Should be parseable as ISO datetime
        from datetime import datetime
        dt = datetime.fromisoformat(data["timestamp"])
        assert dt.year >= 2024


class TestTemplateFormatter:
    """Test TemplateFormatter produces correct timestamp/level format."""

    def setup_method(self):
        self.formatter = TemplateFormatter()

    def test_output_contains_level_name(self):
        """Formatted output contains the level name."""
        record = make_record("Test", level=logging.INFO)
        output = self.formatter.format(record)
        assert "INFO" in output

    def test_output_contains_message(self):
        """Formatted output contains the log message."""
        record = make_record("My log message")
        output = self.formatter.format(record)
        assert "My log message" in output

    def test_output_contains_timestamp(self):
        """Formatted output contains a timestamp bracket."""
        record = make_record("msg")
        output = self.formatter.format(record)
        # Timestamp format: [YYYY-MM-DD HH:MM:SS]
        assert "[" in output
        assert "-" in output

    def test_warning_level(self):
        """WARNING level is reflected in output."""
        record = make_record("Watch out", level=logging.WARNING)
        output = self.formatter.format(record)
        assert "WARNING" in output

    def test_error_level(self):
        """ERROR level is reflected in output."""
        record = make_record("Something broke", level=logging.ERROR)
        output = self.formatter.format(record)
        assert "ERROR" in output

    def test_debug_level(self):
        """DEBUG level is reflected in output."""
        record = make_record("Debug info", level=logging.DEBUG)
        output = self.formatter.format(record)
        assert "DEBUG" in output


class TestEmojis:
    """Test EMOJIS constant dict."""

    def test_emojis_dict_has_expected_keys(self):
        """EMOJIS dict contains expected keys."""
        expected_keys = {"info", "success", "warning", "error", "rocket"}
        assert expected_keys.issubset(EMOJIS.keys())

    def test_emojis_values_are_strings(self):
        """All emoji values are non-empty strings."""
        for key, value in EMOJIS.items():
            assert isinstance(value, str), f"EMOJIS[{key!r}] is not a string"
            assert len(value) > 0, f"EMOJIS[{key!r}] is empty"
