"""Comprehensive tests for infrastructure/literature/logging.py StructuredLogger.

Tests the structured logging functionality including LogEntry, StructuredLogger,
and all their methods.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from infrastructure.literature.logging import (
    LogFormat,
    LogEntry,
    StructuredLogger,
)


class TestLogFormat:
    """Test LogFormat enum."""

    def test_log_format_values(self):
        """Test LogFormat enum values."""
        assert LogFormat.TEXT.value == "text"
        assert LogFormat.JSON.value == "json"


class TestLogEntry:
    """Test LogEntry dataclass."""

    def test_log_entry_creation(self):
        """Test LogEntry creation with required fields."""
        entry = LogEntry(
            timestamp="2024-01-01T00:00:00",
            level="INFO",
            operation="test",
            message="Test message"
        )
        
        assert entry.timestamp == "2024-01-01T00:00:00"
        assert entry.level == "INFO"
        assert entry.operation == "test"
        assert entry.message == "Test message"
        assert entry.source is None
        assert entry.paper_id is None
        assert entry.metrics is None
        assert entry.error is None
        assert entry.context is None

    def test_log_entry_with_optional_fields(self):
        """Test LogEntry creation with optional fields."""
        entry = LogEntry(
            timestamp="2024-01-01T00:00:00",
            level="ERROR",
            operation="download",
            message="Download failed",
            source="arxiv",
            paper_id="paper123",
            metrics={"duration": 1.5},
            error={"type": "NetworkError", "message": "Connection timeout"},
            context={"url": "https://example.com"}
        )
        
        assert entry.source == "arxiv"
        assert entry.paper_id == "paper123"
        assert entry.metrics == {"duration": 1.5}
        assert entry.error == {"type": "NetworkError", "message": "Connection timeout"}
        assert entry.context == {"url": "https://example.com"}

    def test_log_entry_to_dict(self):
        """Test LogEntry.to_dict() method."""
        entry = LogEntry(
            timestamp="2024-01-01T00:00:00",
            level="INFO",
            operation="test",
            message="Test message",
            source="arxiv",
            metrics={"count": 5}
        )
        
        result = entry.to_dict()
        
        assert isinstance(result, dict)
        assert result["timestamp"] == "2024-01-01T00:00:00"
        assert result["level"] == "INFO"
        assert result["operation"] == "test"
        assert result["message"] == "Test message"
        assert result["source"] == "arxiv"
        assert result["metrics"] == {"count": 5}
        assert result["paper_id"] is None

    def test_log_entry_to_text_basic(self):
        """Test LogEntry.to_text() with basic fields."""
        entry = LogEntry(
            timestamp="2024-01-01T00:00:00",
            level="INFO",
            operation="test",
            message="Test message"
        )
        
        result = entry.to_text()
        
        assert "[2024-01-01T00:00:00]" in result
        assert "[INFO]" in result
        assert "test: Test message" in result

    def test_log_entry_to_text_with_source(self):
        """Test LogEntry.to_text() with source."""
        entry = LogEntry(
            timestamp="2024-01-01T00:00:00",
            level="INFO",
            operation="download",
            message="Downloading paper",
            source="arxiv"
        )
        
        result = entry.to_text()
        
        assert "[arxiv]" in result
        assert "download: Downloading paper" in result

    def test_log_entry_to_text_with_paper_id(self):
        """Test LogEntry.to_text() with paper_id."""
        entry = LogEntry(
            timestamp="2024-01-01T00:00:00",
            level="INFO",
            operation="summarize",
            message="Summarizing",
            paper_id="paper123"
        )
        
        result = entry.to_text()
        
        assert "[paper123]" in result

    def test_log_entry_to_text_with_metrics(self):
        """Test LogEntry.to_text() with metrics."""
        entry = LogEntry(
            timestamp="2024-01-01T00:00:00",
            level="INFO",
            operation="process",
            message="Processing",
            metrics={"duration": 1.5, "items": 10}
        )
        
        result = entry.to_text()
        
        assert "duration=1.5" in result
        assert "items=10" in result
        assert "(" in result  # Metrics should be in parentheses

    def test_log_entry_to_text_with_error(self):
        """Test LogEntry.to_text() with error."""
        entry = LogEntry(
            timestamp="2024-01-01T00:00:00",
            level="ERROR",
            operation="download",
            message="Failed",
            error={"message": "Connection timeout"}
        )
        
        result = entry.to_text()
        
        assert "ERROR: Connection timeout" in result

    def test_log_entry_to_text_with_all_fields(self):
        """Test LogEntry.to_text() with all fields."""
        entry = LogEntry(
            timestamp="2024-01-01T00:00:00",
            level="ERROR",
            operation="download",
            message="Download failed",
            source="arxiv",
            paper_id="paper123",
            metrics={"duration": 1.5},
            error={"message": "Timeout"}
        )
        
        result = entry.to_text()
        
        assert "[2024-01-01T00:00:00]" in result
        assert "[ERROR]" in result
        assert "[arxiv]" in result
        assert "[paper123]" in result
        assert "download: Download failed" in result
        assert "duration=1.5" in result
        assert "ERROR: Timeout" in result


class TestStructuredLoggerInitialization:
    """Test StructuredLogger initialization."""

    def test_initialization_defaults(self):
        """Test StructuredLogger with default parameters."""
        logger = StructuredLogger()
        
        assert logger.format == LogFormat.TEXT
        assert logger.output_file is None
        assert logger.enable_progress is True
        assert logger.entries == []
        assert logger._operation_start_times == {}
        assert logger._progress_counters == {}

    def test_initialization_text_format(self):
        """Test StructuredLogger with TEXT format."""
        logger = StructuredLogger(format=LogFormat.TEXT)
        
        assert logger.format == LogFormat.TEXT

    def test_initialization_json_format(self):
        """Test StructuredLogger with JSON format."""
        logger = StructuredLogger(format=LogFormat.JSON)
        
        assert logger.format == LogFormat.JSON

    def test_initialization_with_output_file(self, tmp_path):
        """Test StructuredLogger with output file."""
        output_file = tmp_path / "test.log"
        logger = StructuredLogger(output_file=output_file)
        
        assert logger.output_file == output_file

    def test_initialization_disable_progress(self):
        """Test StructuredLogger with progress disabled."""
        logger = StructuredLogger(enable_progress=False)
        
        assert logger.enable_progress is False


class TestStructuredLoggerLog:
    """Test StructuredLogger.log() method."""

    def test_log_basic(self):
        """Test basic logging."""
        logger = StructuredLogger()
        
        logger.log("INFO", "test", "Test message")
        
        assert len(logger.entries) == 1
        entry = logger.entries[0]
        assert entry.level == "INFO"
        assert entry.operation == "test"
        assert entry.message == "Test message"

    def test_log_with_source(self):
        """Test logging with source."""
        logger = StructuredLogger()
        
        logger.log("INFO", "download", "Downloading", source="arxiv")
        
        assert logger.entries[0].source == "arxiv"

    def test_log_with_paper_id(self):
        """Test logging with paper_id."""
        logger = StructuredLogger()
        
        logger.log("INFO", "summarize", "Summarizing", paper_id="paper123")
        
        assert logger.entries[0].paper_id == "paper123"

    def test_log_with_metrics(self):
        """Test logging with metrics."""
        logger = StructuredLogger()
        
        logger.log("INFO", "process", "Processing", metrics={"count": 5, "duration": 1.5})
        
        assert logger.entries[0].metrics == {"count": 5, "duration": 1.5}

    def test_log_with_error(self):
        """Test logging with error."""
        logger = StructuredLogger()
        
        error_info = {"type": "NetworkError", "message": "Connection failed"}
        logger.log("ERROR", "download", "Failed", error=error_info)
        
        assert logger.entries[0].error == error_info

    def test_log_with_context(self):
        """Test logging with context."""
        logger = StructuredLogger()
        
        context = {"url": "https://example.com", "retry": 3}
        logger.log("INFO", "download", "Downloading", context=context)
        
        assert logger.entries[0].context == context

    def test_log_multiple_entries(self):
        """Test logging multiple entries."""
        logger = StructuredLogger()
        
        logger.log("INFO", "op1", "Message 1")
        logger.log("WARNING", "op2", "Message 2")
        logger.log("ERROR", "op3", "Message 3")
        
        assert len(logger.entries) == 3
        assert logger.entries[0].level == "INFO"
        assert logger.entries[1].level == "WARNING"
        assert logger.entries[2].level == "ERROR"

    @patch('infrastructure.literature.logging.logger')
    def test_log_writes_to_standard_logger(self, mock_logger):
        """Test that log() writes to standard logger."""
        logger = StructuredLogger()
        
        logger.log("INFO", "test", "Test message")
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert "test: Test message" in call_args

    @patch('infrastructure.literature.logging.logger')
    def test_log_json_format(self, mock_logger):
        """Test logging with JSON format."""
        logger = StructuredLogger(format=LogFormat.JSON)
        
        logger.log("INFO", "test", "Test message")
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        # Should be JSON format
        parsed = json.loads(call_args)
        assert parsed["level"] == "INFO"
        assert parsed["operation"] == "test"
        assert parsed["message"] == "Test message"

    def test_log_writes_to_file(self, tmp_path):
        """Test that log() writes to file when output_file is set."""
        output_file = tmp_path / "test.log"
        logger = StructuredLogger(output_file=output_file)
        
        logger.log("INFO", "test", "Test message")
        
        assert output_file.exists()
        content = output_file.read_text()
        assert "test: Test message" in content

    def test_log_append_to_file(self, tmp_path):
        """Test that log() appends to existing file."""
        output_file = tmp_path / "test.log"
        logger = StructuredLogger(output_file=output_file)
        
        logger.log("INFO", "test", "Message 1")
        logger.log("INFO", "test", "Message 2")
        
        content = output_file.read_text()
        assert content.count("Message 1") == 1
        assert content.count("Message 2") == 1


class TestStructuredLoggerOperations:
    """Test StructuredLogger operation timing methods."""

    def test_start_operation(self):
        """Test start_operation() method."""
        logger = StructuredLogger()
        
        logger.start_operation("download")
        
        assert "download" in logger._operation_start_times
        assert isinstance(logger._operation_start_times["download"], float)

    def test_start_operation_with_message(self):
        """Test start_operation() with message."""
        logger = StructuredLogger()
        
        logger.start_operation("download", "Starting download")
        
        assert len(logger.entries) == 1
        assert logger.entries[0].operation == "download"
        assert "Starting download" in logger.entries[0].message

    def test_end_operation_success(self):
        """Test end_operation() with success."""
        logger = StructuredLogger()
        
        logger.start_operation("download")
        time.sleep(0.01)  # Small delay to ensure duration > 0
        logger.end_operation("download", "Completed", success=True)
        
        assert "download" not in logger._operation_start_times
        assert len(logger.entries) == 1
        entry = logger.entries[0]
        assert entry.level == "INFO"
        assert "Completed" in entry.message
        assert entry.metrics is not None
        assert "duration_seconds" in entry.metrics
        assert entry.metrics["duration_seconds"] > 0

    def test_end_operation_failure(self):
        """Test end_operation() with failure."""
        logger = StructuredLogger()
        
        logger.start_operation("download")
        logger.end_operation("download", "Failed", success=False)
        
        entry = logger.entries[0]
        assert entry.level == "ERROR"
        assert "Failed" in entry.message

    def test_end_operation_without_start(self):
        """Test end_operation() without start_operation()."""
        logger = StructuredLogger()
        
        logger.end_operation("download", "Completed")
        
        entry = logger.entries[0]
        assert entry.level == "INFO"
        assert entry.metrics is not None
        # Duration should be None if operation wasn't started
        assert "duration_seconds" not in entry.metrics

    def test_end_operation_with_metrics(self):
        """Test end_operation() with additional metrics."""
        logger = StructuredLogger()
        
        logger.start_operation("download")
        logger.end_operation("download", "Completed", metrics={"items": 5, "size": 1024})
        
        entry = logger.entries[0]
        assert entry.metrics["items"] == 5
        assert entry.metrics["size"] == 1024
        assert "duration_seconds" in entry.metrics


class TestStructuredLoggerProgress:
    """Test StructuredLogger progress logging."""

    def test_log_progress_basic(self):
        """Test basic progress logging."""
        logger = StructuredLogger()
        
        logger.log_progress("download", current=5, total=10)
        
        assert len(logger.entries) == 1
        entry = logger.entries[0]
        assert entry.operation == "download"
        assert "Progress: 5/10" in entry.message
        assert entry.metrics["current"] == 5
        assert entry.metrics["total"] == 10
        assert entry.metrics["percentage"] == "50.0%"

    def test_log_progress_with_item_name(self):
        """Test progress logging with item name."""
        logger = StructuredLogger()
        
        logger.log_progress("download", current=3, total=10, item_name="paper.pdf")
        
        entry = logger.entries[0]
        assert "paper.pdf" in entry.message

    def test_log_progress_with_metrics(self):
        """Test progress logging with additional metrics."""
        logger = StructuredLogger()
        
        logger.log_progress("download", current=5, total=10, metrics={"speed": 1.5})
        
        entry = logger.entries[0]
        assert entry.metrics["speed"] == 1.5
        assert entry.metrics["current"] == 5

    def test_log_progress_zero_total(self):
        """Test progress logging with zero total."""
        logger = StructuredLogger()
        
        logger.log_progress("download", current=0, total=0)
        
        entry = logger.entries[0]
        assert entry.metrics["percentage"] == "0.0%"

    def test_log_progress_with_eta(self):
        """Test progress logging with ETA calculation."""
        logger = StructuredLogger()
        
        logger.start_operation("download")
        time.sleep(0.1)  # Small delay
        logger.log_progress("download", current=5, total=10)
        
        entry = logger.entries[0]
        # Should have ETA and items_per_second if operation was started
        assert "eta_seconds" in entry.metrics
        assert "items_per_second" in entry.metrics
        assert entry.metrics["eta_seconds"] >= 0

    def test_log_progress_disabled(self):
        """Test that progress logging is skipped when disabled."""
        logger = StructuredLogger(enable_progress=False)
        
        logger.log_progress("download", current=5, total=10)
        
        assert len(logger.entries) == 0

    def test_log_progress_multiple_calls(self):
        """Test multiple progress log calls."""
        logger = StructuredLogger()
        
        logger.log_progress("download", current=1, total=10)
        logger.log_progress("download", current=5, total=10)
        logger.log_progress("download", current=10, total=10)
        
        assert len(logger.entries) == 3
        assert logger.entries[0].metrics["current"] == 1
        assert logger.entries[1].metrics["current"] == 5
        assert logger.entries[2].metrics["current"] == 10


class TestStructuredLoggerError:
    """Test StructuredLogger error logging."""

    def test_log_error_basic(self):
        """Test basic error logging."""
        logger = StructuredLogger()
        error = ValueError("Test error")
        
        logger.log_error("download", error)
        
        assert len(logger.entries) == 1
        entry = logger.entries[0]
        assert entry.level == "ERROR"
        assert entry.operation == "download"
        assert entry.error is not None
        assert entry.error["type"] == "ValueError"
        assert entry.error["message"] == "Test error"

    def test_log_error_with_source(self):
        """Test error logging with source."""
        logger = StructuredLogger()
        error = ValueError("Test error")
        
        logger.log_error("download", error, source="arxiv")
        
        assert logger.entries[0].source == "arxiv"

    def test_log_error_with_paper_id(self):
        """Test error logging with paper_id."""
        logger = StructuredLogger()
        error = ValueError("Test error")
        
        logger.log_error("download", error, paper_id="paper123")
        
        assert logger.entries[0].paper_id == "paper123"

    def test_log_error_with_context(self):
        """Test error logging with context."""
        logger = StructuredLogger()
        error = ValueError("Test error")
        context = {"url": "https://example.com"}
        
        logger.log_error("download", error, context=context)
        
        assert logger.entries[0].context == context

    def test_log_error_with_cause(self):
        """Test error logging with exception cause."""
        logger = StructuredLogger()
        cause = ValueError("Root cause")
        error = RuntimeError("Wrapper error")
        error.__cause__ = cause
        
        logger.log_error("download", error)
        
        entry = logger.entries[0]
        assert entry.error["cause"]["type"] == "ValueError"
        assert entry.error["cause"]["message"] == "Root cause"

    def test_log_error_with_context_attribute(self):
        """Test error logging with error.context attribute."""
        logger = StructuredLogger()
        
        class CustomError(Exception):
            def __init__(self, message, context):
                super().__init__(message)
                self.context = context
        
        error = CustomError("Test error", {"key": "value"})
        logger.log_error("download", error)
        
        entry = logger.entries[0]
        assert entry.error["context"] == {"key": "value"}

    def test_log_error_with_non_dict_context(self):
        """Test error logging with non-dict context attribute."""
        logger = StructuredLogger()
        
        class CustomError(Exception):
            def __init__(self, message, context):
                super().__init__(message)
                self.context = context
        
        error = CustomError("Test error", "not a dict")
        logger.log_error("download", error)
        
        entry = logger.entries[0]
        # Should handle non-dict context gracefully
        assert "context" not in entry.error or entry.error.get("context") == {}


class TestStructuredLoggerExport:
    """Test StructuredLogger export functionality."""

    def test_export_logs_text_format(self, tmp_path):
        """Test exporting logs in TEXT format."""
        logger = StructuredLogger()
        logger.log("INFO", "test", "Message 1")
        logger.log("WARNING", "test", "Message 2")
        
        output_path = tmp_path / "export.log"
        logger.export_logs(output_path, format=LogFormat.TEXT)
        
        assert output_path.exists()
        content = output_path.read_text()
        assert "Message 1" in content
        assert "Message 2" in content

    def test_export_logs_json_format(self, tmp_path):
        """Test exporting logs in JSON format."""
        logger = StructuredLogger()
        logger.log("INFO", "test", "Message 1")
        logger.log("WARNING", "test", "Message 2")
        
        output_path = tmp_path / "export.json"
        logger.export_logs(output_path, format=LogFormat.JSON)
        
        assert output_path.exists()
        content = json.loads(output_path.read_text())
        assert isinstance(content, list)
        assert len(content) == 2
        assert content[0]["message"] == "Message 1"
        assert content[1]["message"] == "Message 2"

    def test_export_logs_uses_instance_format(self, tmp_path):
        """Test that export uses instance format when format not specified."""
        logger = StructuredLogger(format=LogFormat.JSON)
        logger.log("INFO", "test", "Message 1")
        
        output_path = tmp_path / "export.json"
        logger.export_logs(output_path)
        
        content = json.loads(output_path.read_text())
        assert isinstance(content, list)

    def test_export_logs_creates_parent_directories(self, tmp_path):
        """Test that export creates parent directories."""
        logger = StructuredLogger()
        logger.log("INFO", "test", "Message")
        
        output_path = tmp_path / "nested" / "deep" / "export.log"
        logger.export_logs(output_path)
        
        assert output_path.exists()
        assert output_path.parent.exists()

    def test_export_logs_empty(self, tmp_path):
        """Test exporting empty logs."""
        logger = StructuredLogger()
        
        output_path = tmp_path / "export.log"
        logger.export_logs(output_path)
        
        assert output_path.exists()
        content = output_path.read_text()
        assert content == ""  # Empty file for text format


class TestStructuredLoggerStatistics:
    """Test StructuredLogger statistics generation."""

    def test_get_statistics_empty(self):
        """Test statistics with no entries."""
        logger = StructuredLogger()
        
        stats = logger.get_statistics()
        
        assert stats["total_entries"] == 0
        assert stats["by_level"] == {}
        assert stats["by_operation"] == {}
        assert stats["errors"] == []

    def test_get_statistics_by_level(self):
        """Test statistics counting by level."""
        logger = StructuredLogger()
        logger.log("INFO", "op1", "Message 1")
        logger.log("WARNING", "op2", "Message 2")
        logger.log("ERROR", "op3", "Message 3")
        logger.log("INFO", "op1", "Message 4")
        
        stats = logger.get_statistics()
        
        assert stats["total_entries"] == 4
        assert stats["by_level"]["INFO"] == 2
        assert stats["by_level"]["WARNING"] == 1
        assert stats["by_level"]["ERROR"] == 1

    def test_get_statistics_by_operation(self):
        """Test statistics counting by operation."""
        logger = StructuredLogger()
        logger.log("INFO", "download", "Message 1")
        logger.log("INFO", "download", "Message 2")
        logger.log("INFO", "summarize", "Message 3")
        
        stats = logger.get_statistics()
        
        assert "download" in stats["by_operation"]
        assert "summarize" in stats["by_operation"]
        assert stats["by_operation"]["download"]["count"] == 2
        assert stats["by_operation"]["summarize"]["count"] == 1

    def test_get_statistics_error_counting(self):
        """Test statistics error counting."""
        logger = StructuredLogger()
        logger.log("ERROR", "download", "Failed", error={"message": "Error 1"})
        logger.log("ERROR", "download", "Failed", error={"message": "Error 2"})
        logger.log("INFO", "download", "Success")
        
        stats = logger.get_statistics()
        
        assert stats["by_operation"]["download"]["errors"] == 2
        assert len(stats["errors"]) == 2

    def test_get_statistics_duration_tracking(self):
        """Test statistics duration tracking."""
        logger = StructuredLogger()
        
        logger.start_operation("download")
        time.sleep(0.01)
        logger.end_operation("download", "Completed")
        
        logger.start_operation("download")
        time.sleep(0.01)
        logger.end_operation("download", "Completed")
        
        stats = logger.get_statistics()
        
        assert stats["by_operation"]["download"]["total_duration"] > 0
        assert stats["by_operation"]["download"]["count"] == 2

    def test_get_statistics_comprehensive(self):
        """Test comprehensive statistics."""
        logger = StructuredLogger()
        
        # Add various log entries
        logger.log("INFO", "download", "Starting")
        logger.log("ERROR", "download", "Failed", error={"message": "Error"})
        logger.log("INFO", "summarize", "Starting")
        logger.log("WARNING", "summarize", "Warning")
        
        logger.start_operation("process")
        time.sleep(0.01)
        logger.end_operation("process", "Done")
        
        stats = logger.get_statistics()
        
        assert stats["total_entries"] == 5
        assert len(stats["by_level"]) == 3  # INFO, ERROR, WARNING
        assert len(stats["by_operation"]) == 3  # download, summarize, process
        assert len(stats["errors"]) == 1
        assert stats["by_operation"]["process"]["total_duration"] > 0

