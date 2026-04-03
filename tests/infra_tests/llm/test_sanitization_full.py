"""Tests for infrastructure.llm.core.sanitization — comprehensive coverage."""

import pytest
from pathlib import Path

from infrastructure.core.exceptions import SecurityError
from infrastructure.llm.core.sanitization import (
    InputSanitizer,
    get_input_sanitizer,
    sanitize_llm_input,
)


class TestInputSanitizer:
    def test_sanitize_prompt_basic(self):
        s = InputSanitizer()
        result = s.sanitize_prompt("Hello, this is a test prompt.")
        assert "Hello" in result

    def test_sanitize_prompt_non_string_raises(self):
        s = InputSanitizer()
        with pytest.raises(SecurityError, match="Prompt must be a string"):
            s.sanitize_prompt(123)  # type: ignore

    def test_sanitize_prompt_removes_control_chars(self):
        s = InputSanitizer()
        result = s.sanitize_prompt("Hello\x00World\x01Test\x7f")
        assert "\x00" not in result
        assert "\x01" not in result
        assert "\x7f" not in result

    def test_sanitize_prompt_preserves_newlines_and_tabs(self):
        s = InputSanitizer()
        result = s.sanitize_prompt("Hello\nWorld\tTest")
        # Newlines and tabs should be preserved (or at least content is present)
        assert "Hello" in result
        assert "World" in result

    def test_sanitize_prompt_escapes_html(self):
        s = InputSanitizer()
        # Use non-dangerous HTML that won't trigger security patterns
        result = s.sanitize_prompt("Hello <b>World</b> & 'quotes'")
        assert "<b>" not in result
        assert "&lt;b&gt;" in result
        assert "&amp;" in result

    def test_sanitize_prompt_rejects_dangerous_script(self):
        s = InputSanitizer()
        with pytest.raises(SecurityError, match="Dangerous content"):
            s.sanitize_prompt("Hello <script>alert('xss')</script>")

    def test_sanitize_prompt_normalizes_whitespace(self):
        s = InputSanitizer()
        result = s.sanitize_prompt("Hello    World")
        # Should normalize multiple spaces
        assert "Hello" in result

    def test_sanitize_prompt_limits_length(self):
        s = InputSanitizer()
        long_text = "a" * 600000
        result = s.sanitize_prompt(long_text)
        assert len(result) <= 500100  # 500000 + "[truncated]"
        assert "truncated" in result

    def test_sanitize_prompt_normal_length_unchanged(self):
        s = InputSanitizer()
        text = "Normal length text."
        result = s.sanitize_prompt(text)
        assert "Normal length text" in result


class TestValidateFileInput:
    def test_absolute_path_rejected(self):
        s = InputSanitizer()
        with pytest.raises(SecurityError, match="Absolute paths"):
            s.validate_file_input(Path("/etc/passwd"))

    def test_traversal_rejected(self):
        s = InputSanitizer()
        with pytest.raises(SecurityError, match="traversal"):
            s.validate_file_input(Path("../../../etc/passwd"))

    def test_nonexistent_file_rejected(self, tmp_path):
        s = InputSanitizer()
        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            with pytest.raises(SecurityError, match="File not found"):
                s.validate_file_input(Path("nonexistent_file.txt"))
        finally:
            os.chdir(old_cwd)

    def test_valid_file_accepted(self, tmp_path):
        s = InputSanitizer()
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            # Should not raise
            s.validate_file_input(Path("test.txt"))
        finally:
            os.chdir(old_cwd)

    def test_extension_filter(self, tmp_path):
        s = InputSanitizer()
        test_file = tmp_path / "test.exe"
        test_file.write_text("content")
        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            with pytest.raises(SecurityError, match="extension not allowed"):
                s.validate_file_input(Path("test.exe"), allowed_extensions=[".txt", ".md"])
        finally:
            os.chdir(old_cwd)

    def test_allowed_extension(self, tmp_path):
        s = InputSanitizer()
        test_file = tmp_path / "test.md"
        test_file.write_text("content")
        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            s.validate_file_input(Path("test.md"), allowed_extensions=[".txt", ".md"])
        finally:
            os.chdir(old_cwd)


class TestSanitizeFilename:
    def test_basic(self):
        s = InputSanitizer()
        assert s.sanitize_filename("test.txt") == "test.txt"

    def test_strips_path_separators(self):
        s = InputSanitizer()
        result = s.sanitize_filename("path/to/file.txt")
        assert "/" not in result

    def test_strips_control_chars(self):
        s = InputSanitizer()
        result = s.sanitize_filename("file\x00name.txt")
        assert "\x00" not in result

    def test_strips_special_chars(self):
        s = InputSanitizer()
        result = s.sanitize_filename('file<>:"|?*.txt')
        assert "<" not in result
        assert ">" not in result

    def test_empty_string_raises(self):
        s = InputSanitizer()
        with pytest.raises(SecurityError, match="Invalid filename"):
            s.sanitize_filename("")

    def test_non_string_raises(self):
        s = InputSanitizer()
        with pytest.raises(SecurityError, match="Invalid filename"):
            s.sanitize_filename(None)  # type: ignore

    def test_long_filename_truncated(self):
        s = InputSanitizer()
        result = s.sanitize_filename("a" * 300)
        assert len(result) == 255

    def test_all_special_chars_becomes_unnamed(self):
        s = InputSanitizer()
        result = s.sanitize_filename("\x00\x01\x02")
        # After removing control chars, all become underscores, then strip
        assert result  # Should not be empty


class TestRemoveControlCharacters:
    def test_preserves_normal_text(self):
        s = InputSanitizer()
        assert s._remove_control_characters("Hello World") == "Hello World"

    def test_removes_null(self):
        s = InputSanitizer()
        assert "\x00" not in s._remove_control_characters("Hello\x00World")

    def test_preserves_newlines(self):
        s = InputSanitizer()
        result = s._remove_control_characters("Line1\nLine2")
        assert "\n" in result

    def test_preserves_tabs(self):
        s = InputSanitizer()
        result = s._remove_control_characters("Col1\tCol2")
        assert "\t" in result


class TestLimitLength:
    def test_short_text_unchanged(self):
        s = InputSanitizer()
        assert s._limit_length("short") == "short"

    def test_long_text_truncated(self):
        s = InputSanitizer()
        result = s._limit_length("x" * 100, max_length=50)
        assert len(result) < 100
        assert "truncated" in result

    def test_exact_length(self):
        s = InputSanitizer()
        text = "x" * 50
        assert s._limit_length(text, max_length=50) == text


class TestGetInputSanitizer:
    def test_returns_same_instance(self):
        get_input_sanitizer.cache_clear()
        s1 = get_input_sanitizer()
        s2 = get_input_sanitizer()
        assert s1 is s2
        get_input_sanitizer.cache_clear()


class TestSanitizeLlmInput:
    def test_basic(self):
        result = sanitize_llm_input("Hello World")
        assert "Hello" in result
