"""Tests for infrastructure.rendering._pdf_latex_validation module.

Tests PDF structure validation and aux file repair functionality.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.rendering._pdf_latex_validation import (
    repair_truncated_aux,
    validate_pdf_structure,
)


class TestValidatePdfStructure:
    """Tests for validate_pdf_structure."""

    def test_valid_pdf_structure(self, tmp_path: Path):
        """A file with both %%EOF and startxref should validate."""
        pdf_file = tmp_path / "valid.pdf"
        # Minimal valid PDF-like content with required markers
        content = b"%PDF-1.4\nsome content\nstartxref\n12345\n%%EOF\n"
        pdf_file.write_bytes(content)
        assert validate_pdf_structure(pdf_file) is True

    def test_missing_eof_marker(self, tmp_path: Path):
        """A file without %%EOF should fail validation."""
        pdf_file = tmp_path / "no_eof.pdf"
        content = b"%PDF-1.4\nsome content\nstartxref\n12345\n"
        pdf_file.write_bytes(content)
        assert validate_pdf_structure(pdf_file) is False

    def test_missing_startxref(self, tmp_path: Path):
        """A file without startxref should fail validation."""
        pdf_file = tmp_path / "no_xref.pdf"
        content = b"%PDF-1.4\nsome content\n%%EOF\n"
        pdf_file.write_bytes(content)
        assert validate_pdf_structure(pdf_file) is False

    def test_missing_both_markers(self, tmp_path: Path):
        """A file without either marker should fail validation."""
        pdf_file = tmp_path / "truncated.pdf"
        content = b"%PDF-1.4\nsome content only\n"
        pdf_file.write_bytes(content)
        assert validate_pdf_structure(pdf_file) is False

    def test_nonexistent_file(self, tmp_path: Path):
        """A non-existent file should return False."""
        pdf_file = tmp_path / "doesnt_exist.pdf"
        assert validate_pdf_structure(pdf_file) is False

    def test_empty_file(self, tmp_path: Path):
        """An empty file should fail validation."""
        pdf_file = tmp_path / "empty.pdf"
        pdf_file.write_bytes(b"")
        assert validate_pdf_structure(pdf_file) is False

    def test_large_file_with_markers_at_end(self, tmp_path: Path):
        """Markers at end of large file should be found in last 4KB."""
        pdf_file = tmp_path / "large.pdf"
        # Content larger than 4KB with markers at end
        padding = b"x" * 8192
        content = padding + b"\nstartxref\n99999\n%%EOF\n"
        pdf_file.write_bytes(content)
        assert validate_pdf_structure(pdf_file) is True

    def test_markers_not_in_last_4kb(self, tmp_path: Path):
        """Markers before the last 4KB should not be found."""
        pdf_file = tmp_path / "markers_early.pdf"
        content = b"startxref\n1\n%%EOF\n" + b"x" * 8192
        pdf_file.write_bytes(content)
        assert validate_pdf_structure(pdf_file) is False


class TestRepairTruncatedAux:
    """Tests for repair_truncated_aux."""

    def test_nonexistent_file_noop(self, tmp_path: Path):
        """Non-existent file should do nothing."""
        aux_file = tmp_path / "missing.aux"
        repair_truncated_aux(aux_file)  # Should not raise

    def test_empty_file_noop(self, tmp_path: Path):
        """Empty file should remain unchanged."""
        aux_file = tmp_path / "empty.aux"
        aux_file.write_text("", encoding="utf-8")
        repair_truncated_aux(aux_file)
        assert aux_file.read_text() == ""

    def test_balanced_braces_no_repair(self, tmp_path: Path):
        """File with balanced braces should not be modified."""
        aux_file = tmp_path / "balanced.aux"
        content = "\\relax\n\\newlabel{sec:intro}{{1}{1}}\n"
        aux_file.write_text(content, encoding="utf-8")
        repair_truncated_aux(aux_file)
        assert aux_file.read_text(encoding="utf-8") == content

    def test_unbalanced_last_line_removed(self, tmp_path: Path):
        """File with unbalanced last line should have it removed."""
        aux_file = tmp_path / "truncated.aux"
        content = "\\relax\n\\newlabel{sec:intro}{{1}{1}}\n\\newlabel{sec:result}{{2"
        aux_file.write_text(content, encoding="utf-8")
        repair_truncated_aux(aux_file)
        repaired = aux_file.read_text(encoding="utf-8")
        assert "\\newlabel{sec:result}" not in repaired
        assert "\\newlabel{sec:intro}" in repaired

    def test_multiple_truncated_lines(self, tmp_path: Path):
        """Multiple consecutive unbalanced lines should all be removed."""
        aux_file = tmp_path / "multi_truncated.aux"
        content = "\\relax\n\\good{{ok}}\n\\bad1{{x}\n\\bad2{{y"
        aux_file.write_text(content, encoding="utf-8")
        repair_truncated_aux(aux_file)
        repaired = aux_file.read_text(encoding="utf-8")
        assert "\\bad1" not in repaired
        assert "\\bad2" not in repaired
        assert "\\good" in repaired

    def test_only_empty_lines_at_end(self, tmp_path: Path):
        """Trailing blank lines should be stripped without error."""
        aux_file = tmp_path / "trailing.aux"
        content = "\\relax\n\\newlabel{x}{{1}{1}}\n\n\n"
        aux_file.write_text(content, encoding="utf-8")
        repair_truncated_aux(aux_file)
        # Should not raise, file should be unchanged in substance
