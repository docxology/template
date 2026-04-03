"""Tests for infrastructure.core._validation — comprehensive coverage."""

import pytest
from pathlib import Path

from infrastructure.core._validation import (
    SecurityValidator,
    normalize_whitespace,
)
from infrastructure.core.exceptions import SecurityViolation


class TestSecurityValidator:
    def setup_method(self):
        self.v = SecurityValidator()

    # -- validate_file_path --

    def test_validate_normal_path(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hi")
        result = self.v.validate_file_path(str(f))
        assert result == f.resolve()

    def test_validate_path_traversal(self):
        with pytest.raises(SecurityViolation, match="traversal"):
            self.v.validate_file_path("../../../etc/passwd")

    def test_validate_path_too_long(self):
        long_path = "a" * 5000
        with pytest.raises(SecurityViolation, match="too long"):
            self.v.validate_file_path(long_path)

    def test_validate_path_accepts_pathlib(self, tmp_path):
        result = self.v.validate_file_path(tmp_path)
        assert isinstance(result, Path)

    # -- validate_filename --

    def test_validate_normal_filename(self):
        assert self.v.validate_filename("report.pdf") == "report.pdf"

    def test_validate_empty_filename(self):
        with pytest.raises(SecurityViolation, match="Invalid"):
            self.v.validate_filename("")

    def test_validate_none_filename(self):
        with pytest.raises(SecurityViolation, match="Invalid"):
            self.v.validate_filename(None)

    def test_validate_filename_too_long(self):
        with pytest.raises(SecurityViolation, match="too long"):
            self.v.validate_filename("x" * 300)

    def test_sanitizes_special_chars(self):
        result = self.v.validate_filename('file<name>"test|.pdf')
        assert "<" not in result
        assert '"' not in result
        assert "|" not in result

    def test_sanitizes_path_separators(self):
        result = self.v.validate_filename("path/to\\file.pdf")
        assert "/" not in result
        assert "\\" not in result

    def test_whitespace_only_becomes_unnamed(self):
        result = self.v.validate_filename("   ")
        assert result == "unnamed_file"

    # -- validate_content_size --

    def test_validate_small_content(self):
        content = b"hello"
        assert self.v.validate_content_size(content) == content

    def test_validate_large_content(self):
        content = b"x" * (51 * 1024 * 1024)  # 51MB
        with pytest.raises(SecurityViolation, match="too large"):
            self.v.validate_content_size(content)

    # -- _sanitize_html --

    def test_sanitize_html(self):
        result = self.v._sanitize_html('<script>alert("xss")</script>')
        assert "<script>" not in result
        assert "&lt;" in result

    # -- _normalize_whitespace --

    def test_normalize_whitespace_method(self):
        result = self.v._normalize_whitespace("  hello   world  ")
        assert result == "hello world"

    # -- dangerous_patterns --

    def test_has_dangerous_patterns(self):
        assert len(self.v.dangerous_patterns) > 0


class TestNormalizeWhitespace:
    def test_basic(self):
        assert normalize_whitespace("  hello   world  ") == "hello world"

    def test_multiple_blank_lines(self):
        result = normalize_whitespace("a\n\n\n\n\nb")
        assert result == "a\n\nb"

    def test_already_clean(self):
        assert normalize_whitespace("hello world") == "hello world"

    def test_empty_string(self):
        assert normalize_whitespace("") == ""

    def test_strips_edges(self):
        assert normalize_whitespace("  \n  hello  \n  ") == "hello"
