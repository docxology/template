"""Tests for infrastructure.rendering._pdf_latex_helpers module.

Tests using real temp files (No Mocks Policy).
"""

from __future__ import annotations

import yaml

from infrastructure.rendering._pdf_latex_helpers import (
    check_latex_log_for_graphics_errors,
    extract_preamble,
    generate_title_page_body,
    generate_title_page_preamble,
)


class TestExtractPreamble:
    """Tests for extract_preamble."""

    def test_extracts_latex_block(self, tmp_path):
        """Extracts content from ```latex ... ``` block."""
        preamble_file = tmp_path / "preamble.md"
        preamble_file.write_text("```latex\n\\usepackage{geometry}\n```\n")
        result = extract_preamble(preamble_file)
        assert "\\usepackage{geometry}" in result

    def test_returns_empty_for_missing_file(self, tmp_path):
        """Missing file returns empty string."""
        result = extract_preamble(tmp_path / "nonexistent.md")
        assert result == ""

    def test_returns_empty_for_no_latex_block(self, tmp_path):
        """File with no latex block returns empty string."""
        preamble_file = tmp_path / "preamble.md"
        preamble_file.write_text("# Just markdown\nNo LaTeX here.\n")
        result = extract_preamble(preamble_file)
        assert result == ""

    def test_extracts_multiple_blocks(self, tmp_path):
        """Combines multiple ```latex blocks."""
        preamble_file = tmp_path / "preamble.md"
        preamble_file.write_text(
            "```latex\n\\usepackage{geometry}\n```\n\n```latex\n\\usepackage{amsmath}\n```\n"
        )
        result = extract_preamble(preamble_file)
        assert "\\usepackage{geometry}" in result
        assert "\\usepackage{amsmath}" in result

    def test_strips_whitespace(self, tmp_path):
        """Strips leading/trailing whitespace from extracted content."""
        preamble_file = tmp_path / "preamble.md"
        preamble_file.write_text("```latex\n  \\usepackage{geometry}  \n```\n")
        result = extract_preamble(preamble_file)
        assert result.strip() == "\\usepackage{geometry}"


class TestCheckLatexLogForGraphicsErrors:
    """Tests for check_latex_log_for_graphics_errors."""

    def test_returns_empty_for_missing_log(self, tmp_path):
        """Missing log file returns empty lists."""
        result = check_latex_log_for_graphics_errors(tmp_path / "missing.log")
        assert result == {"graphics_errors": [], "graphics_warnings": [], "missing_files": []}

    def test_detects_missing_file(self, tmp_path):
        """Detects 'File not found' error pattern."""
        log_file = tmp_path / "test.log"
        log_file.write_text("File `figure.png` not found\n")
        result = check_latex_log_for_graphics_errors(log_file)
        assert "figure.png" in result["missing_files"]

    def test_detects_includegraphics_undefined(self, tmp_path):
        """Detects undefined includegraphics control sequence."""
        log_file = tmp_path / "test.log"
        log_file.write_text(r"! Undefined control sequence \includegraphics" + "\n")
        result = check_latex_log_for_graphics_errors(log_file)
        assert len(result["graphics_errors"]) > 0

    def test_clean_log_returns_empty(self, tmp_path):
        """Log with no graphics errors returns empty lists."""
        log_file = tmp_path / "test.log"
        log_file.write_text("This is a clean LaTeX compile log.\nNo errors.\n")
        result = check_latex_log_for_graphics_errors(log_file)
        assert result["missing_files"] == []
        assert result["graphics_errors"] == []


class TestGenerateTitlePagePreamble:
    """Tests for generate_title_page_preamble."""

    def _write_config(self, tmp_path, config: dict) -> None:
        (tmp_path / "config.yaml").write_text(yaml.dump(config))

    def test_returns_empty_for_missing_config(self, tmp_path):
        """Returns empty string when config.yaml doesn't exist."""
        result = generate_title_page_preamble(tmp_path)
        assert result == ""

    def test_includes_title_command(self, tmp_path):
        """\\title{} command appears in preamble."""
        self._write_config(tmp_path, {"paper": {"title": "My Research"}})
        result = generate_title_page_preamble(tmp_path)
        assert "\\title{My Research}" in result

    def test_includes_author_command(self, tmp_path):
        """\\author{} appears when authors defined."""
        self._write_config(
            tmp_path,
            {"paper": {"title": "Test"}, "authors": [{"name": "Alice Smith"}]},
        )
        result = generate_title_page_preamble(tmp_path)
        assert "\\author{" in result
        assert "Alice Smith" in result

    def test_uses_today_when_no_date(self, tmp_path):
        """\\date{\\today} used when config has no date field."""
        self._write_config(tmp_path, {"paper": {"title": "Test"}})
        result = generate_title_page_preamble(tmp_path)
        assert "\\date{\\today}" in result

    def test_includes_provided_date(self, tmp_path):
        """Explicit date used when config has date field."""
        self._write_config(tmp_path, {"paper": {"title": "T", "date": "March 2026"}})
        result = generate_title_page_preamble(tmp_path)
        assert "\\date{March 2026}" in result

    def test_returns_string(self, tmp_path):
        """Always returns a string."""
        self._write_config(tmp_path, {"paper": {"title": "Test"}})
        result = generate_title_page_preamble(tmp_path)
        assert isinstance(result, str)


class TestGenerateTitlePageBody:
    """Tests for generate_title_page_body."""

    def test_returns_maketitle_when_config_exists(self, tmp_path):
        """Returns \\maketitle when config.yaml is present."""
        (tmp_path / "config.yaml").write_text(yaml.dump({"paper": {"title": "Test"}}))
        result = generate_title_page_body(tmp_path)
        assert "\\maketitle" in result

    def test_returns_string(self, tmp_path):
        """Always returns a string."""
        result = generate_title_page_body(tmp_path)
        assert isinstance(result, str)
