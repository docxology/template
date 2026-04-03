"""Tests for infrastructure/rendering/_pdf_pandoc_engine.py.

Covers: build_pandoc_render_error with real CalledProcessError objects
and real temporary files.

No mocks used — all tests use real exceptions, real files, and real data.
"""

from __future__ import annotations

import subprocess


from infrastructure.rendering._pdf_pandoc_engine import build_pandoc_render_error
from infrastructure.core.exceptions import RenderingError


class TestBuildPandocRenderError:
    """Test build_pandoc_render_error with real CalledProcessError data."""

    def _make_error(
        self,
        returncode: int = 1,
        stderr: str = "",
        stdout: str = "",
        cmd: list[str] | None = None,
    ) -> subprocess.CalledProcessError:
        """Create a real CalledProcessError."""
        e = subprocess.CalledProcessError(
            returncode=returncode,
            cmd=cmd or ["pandoc", "--to=latex"],
        )
        e.stderr = stderr
        e.stdout = stdout
        return e

    def test_basic_error_no_output(self, tmp_path):
        """Test error construction with no stderr/stdout."""
        combined_md = tmp_path / "combined.md"
        combined_md.write_text("# Hello\n\nSome content", encoding="utf-8")

        e = self._make_error(returncode=1, stderr="", stdout="")
        result = build_pandoc_render_error(
            e, combined_md, [combined_md], "", ["pandoc", "--to=latex"]
        )
        assert isinstance(result, RenderingError)
        assert "Failed to convert markdown to LaTeX" in result.message
        assert "no output captured" in result.message

    def test_error_with_stderr(self, tmp_path):
        """Test error construction with stderr output."""
        combined_md = tmp_path / "combined.md"
        combined_md.write_text("# Test\n\nContent here", encoding="utf-8")

        e = self._make_error(
            stderr="Error at line 5: unbalanced parenthesis at position 42\n"
        )
        result = build_pandoc_render_error(
            e, combined_md, [combined_md], "", ["pandoc", "--to=latex"]
        )
        assert isinstance(result, RenderingError)
        assert "unbalanced" in result.message.lower()

    def test_error_with_position_info(self, tmp_path):
        """Test error parsing extracts position information."""
        content = "A" * 50 + "(" + "B" * 50
        combined_md = tmp_path / "combined.md"
        combined_md.write_text(content, encoding="utf-8")

        e = self._make_error(
            stderr="error: unbalanced parenthesis at position 50\n"
        )
        result = build_pandoc_render_error(
            e, combined_md, [combined_md], content, ["pandoc", "--to=latex"]
        )
        assert isinstance(result, RenderingError)
        assert result.context.get("error_position") == 50

    def test_error_with_multiple_source_files(self, tmp_path):
        """Test error attribution across multiple source files."""
        file1 = tmp_path / "01_intro.md"
        file1.write_text("# Introduction\n\nSome text here.\n", encoding="utf-8")
        file2 = tmp_path / "02_methods.md"
        file2.write_text("# Methods\n\nMore text (with unmatched.\n", encoding="utf-8")

        combined_content = file1.read_text().rstrip() + "\n" + file2.read_text().rstrip() + "\n"
        combined_md = tmp_path / "_combined.md"
        combined_md.write_text(combined_content, encoding="utf-8")

        # Position 40 should be in file2
        e = self._make_error(
            stderr="error: unbalanced parenthesis at position 40\n"
        )
        result = build_pandoc_render_error(
            e, combined_md, [file1, file2], combined_content, ["pandoc", "--to=latex"]
        )
        assert isinstance(result, RenderingError)

    def test_error_nonexistent_combined_md(self, tmp_path):
        """Test error when combined_md doesn't exist."""
        combined_md = tmp_path / "nonexistent.md"
        e = self._make_error(stderr="some error\n")
        result = build_pandoc_render_error(
            e, combined_md, [], "", ["pandoc", "--to=latex"]
        )
        assert isinstance(result, RenderingError)
        assert len(result.suggestions) > 0

    def test_error_with_stdout_error(self, tmp_path):
        """Test error construction from stdout (not just stderr)."""
        combined_md = tmp_path / "combined.md"
        combined_md.write_text("content", encoding="utf-8")

        e = self._make_error(
            stdout="Pandoc Error (stdout): error at position 10\n",
            stderr="",
        )
        result = build_pandoc_render_error(
            e, combined_md, [combined_md], "content", ["pandoc", "--to=latex"]
        )
        assert isinstance(result, RenderingError)

    def test_error_suggestions_include_pandoc_command(self, tmp_path):
        """Test that suggestions include the pandoc command."""
        combined_md = tmp_path / "combined.md"
        combined_md.write_text("x", encoding="utf-8")

        pandoc_cmd = ["pandoc", "--to=latex", "--standalone"]
        e = self._make_error(stderr="error\n")
        result = build_pandoc_render_error(
            e, combined_md, [combined_md], "x", pandoc_cmd
        )
        assert any("pandoc" in s.lower() for s in result.suggestions)

    def test_error_with_unbalanced_parenthesis_suggestions(self, tmp_path):
        """Test suggestions for unbalanced parenthesis errors."""
        combined_md = tmp_path / "combined.md"
        combined_md.write_text("test (unbalanced content", encoding="utf-8")

        e = self._make_error(
            stderr="Error: unbalanced parenthesis at position 5\n"
        )
        result = build_pandoc_render_error(
            e, combined_md, [combined_md], "test (unbalanced content", ["pandoc"]
        )
        assert any("unmatched" in s.lower() or "parenthes" in s.lower() for s in result.suggestions)

    def test_error_context_includes_source_and_target(self, tmp_path):
        """Test context dict includes source and target paths."""
        combined_md = tmp_path / "combined.md"
        combined_md.write_text("test", encoding="utf-8")

        e = self._make_error(stderr="")
        result = build_pandoc_render_error(
            e, combined_md, [], "", ["pandoc"]
        )
        assert str(combined_md) == result.context["source"]
        assert str(combined_md.with_suffix(".tex")) == result.context["target"]

    def test_error_md_content_passed_as_empty(self, tmp_path):
        """Test error with md_content as empty string (reads from file)."""
        combined_md = tmp_path / "combined.md"
        combined_md.write_text("# File content\nLine two\n", encoding="utf-8")

        e = self._make_error(
            stderr="error at position 5\n"
        )
        result = build_pandoc_render_error(
            e, combined_md, [combined_md], "", ["pandoc"]
        )
        # Should have read from file and populated total_size
        assert result.context.get("total_size") is not None

    def test_error_with_both_stderr_and_stdout(self, tmp_path):
        """Test error with both stderr and stdout."""
        combined_md = tmp_path / "combined.md"
        combined_md.write_text("content", encoding="utf-8")

        e = self._make_error(
            stderr="Error: something failed\n",
            stdout="Additional error info\n",
        )
        result = build_pandoc_render_error(
            e, combined_md, [combined_md], "content", ["pandoc"]
        )
        assert "STDERR" in result.message
        assert "STDOUT" in result.message

    def test_error_position_near_file_boundary(self, tmp_path):
        """Test position info when position is near start of content."""
        content = "AB"
        combined_md = tmp_path / "combined.md"
        combined_md.write_text(content, encoding="utf-8")

        e = self._make_error(
            stderr="error: unbalanced parenthesis at position 1\n"
        )
        result = build_pandoc_render_error(
            e, combined_md, [combined_md], content, ["pandoc"]
        )
        assert result.context.get("error_position") == 1

    def test_error_line_number_computation(self, tmp_path):
        """Test that line number is computed from position."""
        content = "line1\nline2\nline3\n"
        combined_md = tmp_path / "combined.md"
        combined_md.write_text(content, encoding="utf-8")

        # Position 12 is in line 3
        e = self._make_error(
            stderr="error: unbalanced parenthesis at position 12\n"
        )
        result = build_pandoc_render_error(
            e, combined_md, [combined_md], content, ["pandoc"]
        )
        assert result.context.get("error_line") == 3
