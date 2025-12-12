"""Tests for infrastructure.core.logging_helpers module.

Comprehensive tests for logging helper functions including
error formatting and duration formatting.
"""

import pytest
from pathlib import Path

from infrastructure.core.logging_helpers import (
    format_error_with_suggestions,
    format_duration,
)
from infrastructure.core.exceptions import TemplateError


class TestFormatErrorWithSuggestions:
    """Test format_error_with_suggestions function."""

    def test_format_template_error_with_all_fields(self):
        """Test formatting TemplateError with all fields."""
        error = TemplateError(
            "File not found",
            context={"file": "test.txt", "line": 10},
            suggestions=["Check file path", "Verify permissions"],
            recovery_commands=["ls -la test.txt", "cat test.txt"]
        )
        
        result = format_error_with_suggestions(error)
        
        assert "❌ File not found" in result
        assert "📋 Context:" in result
        assert "file: test.txt" in result
        assert "line: 10" in result
        assert "🔧 Recovery Options:" in result
        assert "1. Check file path" in result
        assert "2. Verify permissions" in result
        assert "💻 Quick Fix Commands:" in result
        assert "ls -la test.txt" in result
        assert "cat test.txt" in result

    def test_format_template_error_without_context(self):
        """Test formatting TemplateError without context."""
        error = TemplateError(
            "File not found",
            suggestions=["Check file path"]
        )
        
        result = format_error_with_suggestions(error)
        
        assert "❌ File not found" in result
        assert "📋 Context:" not in result
        assert "🔧 Recovery Options:" in result

    def test_format_template_error_without_suggestions(self):
        """Test formatting TemplateError without suggestions."""
        error = TemplateError(
            "File not found",
            context={"file": "test.txt"}
        )
        
        result = format_error_with_suggestions(error)
        
        assert "❌ File not found" in result
        assert "📋 Context:" in result
        assert "🔧 Recovery Options:" not in result

    def test_format_template_error_without_recovery_commands(self):
        """Test formatting TemplateError without recovery commands."""
        error = TemplateError(
            "File not found",
            suggestions=["Check file path"]
        )
        
        result = format_error_with_suggestions(error)
        
        assert "❌ File not found" in result
        assert "🔧 Recovery Options:" in result
        assert "💻 Quick Fix Commands:" not in result

    def test_format_template_error_empty_fields(self):
        """Test formatting TemplateError with empty fields."""
        error = TemplateError("File not found")
        
        result = format_error_with_suggestions(error)
        
        assert "❌ File not found" in result
        assert "📋 Context:" not in result
        assert "🔧 Recovery Options:" not in result

    def test_format_non_template_error(self):
        """Test formatting non-TemplateError exception."""
        error = ValueError("Invalid value")
        
        result = format_error_with_suggestions(error)
        
        assert result == "Invalid value"

    def test_format_template_error_with_path_context(self):
        """Test formatting TemplateError with Path object in context."""
        error = TemplateError(
            "File not found",
            context={"file": Path("/path/to/file.txt"), "line": 10}
        )
        
        result = format_error_with_suggestions(error)
        
        assert "❌ File not found" in result
        assert "/path/to/file.txt" in result
        assert "line: 10" in result

    def test_format_template_error_with_string_path(self):
        """Test formatting TemplateError with string path in context."""
        error = TemplateError(
            "File not found",
            context={"file": "/path/to/file.txt", "line": 10}
        )
        
        result = format_error_with_suggestions(error)
        
        assert "❌ File not found" in result
        assert "/path/to/file.txt" in result
        assert "line: 10" in result

    def test_format_template_error_multiple_suggestions(self):
        """Test formatting TemplateError with multiple suggestions."""
        error = TemplateError(
            "Build failed",
            suggestions=[
                "Check dependencies",
                "Verify configuration",
                "Review logs",
                "Contact support"
            ]
        )
        
        result = format_error_with_suggestions(error)
        
        assert "1. Check dependencies" in result
        assert "2. Verify configuration" in result
        assert "3. Review logs" in result
        assert "4. Contact support" in result

    def test_format_template_error_multiple_commands(self):
        """Test formatting TemplateError with multiple recovery commands."""
        error = TemplateError(
            "Build failed",
            recovery_commands=[
                "pip install -r requirements.txt",
                "python setup.py build",
                "python -m pytest"
            ]
        )
        
        result = format_error_with_suggestions(error)
        
        assert "pip install -r requirements.txt" in result
        assert "python setup.py build" in result
        assert "python -m pytest" in result


class TestFormatDuration:
    """Test format_duration function."""

    def test_format_seconds_less_than_minute(self):
        """Test formatting duration less than 60 seconds."""
        assert format_duration(0) == "0s"
        assert format_duration(30) == "30s"
        assert format_duration(59) == "59s"
        assert format_duration(45.5) == "45s"  # Should truncate

    def test_format_minutes_less_than_hour(self):
        """Test formatting duration less than 60 minutes."""
        assert format_duration(60) == "1m 0s"
        assert format_duration(90) == "1m 30s"
        assert format_duration(125) == "2m 5s"
        assert format_duration(3599) == "59m 59s"

    def test_format_hours_less_than_day(self):
        """Test formatting duration less than 24 hours."""
        assert format_duration(3600) == "1h 0m"
        assert format_duration(3660) == "1h 1m"
        assert format_duration(7200) == "2h 0m"
        assert format_duration(86399) == "23h 59m"

    def test_format_days(self):
        """Test formatting duration of days or more."""
        assert format_duration(86400) == "1d 0h"
        assert format_duration(90000) == "1d 1h"
        assert format_duration(172800) == "2d 0h"
        assert format_duration(259200) == "3d 0h"

    def test_format_fractional_seconds(self):
        """Test formatting fractional seconds."""
        assert format_duration(0.5) == "0s"
        assert format_duration(30.9) == "30s"
        assert format_duration(60.5) == "1m 0s"

    def test_format_large_durations(self):
        """Test formatting very large durations."""
        # 10 days
        assert format_duration(864000) == "10d 0h"
        # 100 days
        assert format_duration(8640000) == "100d 0h"

    def test_format_edge_cases(self):
        """Test formatting edge case durations."""
        # Exactly 1 minute
        assert format_duration(60) == "1m 0s"
        # Exactly 1 hour
        assert format_duration(3600) == "1h 0m"
        # Exactly 1 day
        assert format_duration(86400) == "1d 0h"
        # Between minute and hour
        assert format_duration(3661) == "1h 1m"  # 1h 1m 1s -> 1h 1m


