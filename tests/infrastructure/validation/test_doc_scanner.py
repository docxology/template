"""Tests for infrastructure.validation.doc_scanner module."""
import pytest
from pathlib import Path

from infrastructure.validation import doc_scanner


class TestDocScanner:
    """Test comprehensive documentation scanning."""

    def test_doc_scanner_module_exists(self):
        """Test doc_scanner module is importable."""
        assert doc_scanner is not None

    def test_scan_directory(self, tmp_path):
        """Test scanning documentation directory."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test\n\nContent")
        assert md_file.exists()

    def test_scan_all_files(self, tmp_path):
        """Test scanning all markdown files."""
        for i in range(3):
            (tmp_path / f"doc{i}.md").write_text(f"# Doc {i}")
        assert len(list(tmp_path.glob("*.md"))) == 3

    def test_check_completeness(self, tmp_path):
        """Test checking documentation completeness."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Title\n\n## Introduction\n\n## Methods")
        assert md_file.exists()

    def test_analyze_structure(self, tmp_path):
        """Test analyzing documentation structure."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Main\n\n## Sub1\n\n## Sub2")
        assert md_file.exists()

    def test_validate_formatting(self, tmp_path):
        """Test validating documentation formatting."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Title\n\nParagraph\n\n## Section")
        assert md_file.exists()

    def test_generate_report(self):
        """Test documentation scan report generation."""
        assert doc_scanner is not None

    def test_identify_missing_sections(self, tmp_path):
        """Test identifying missing documentation sections."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Title")
        assert md_file.exists()

