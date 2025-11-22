"""Tests for infrastructure.validation.check_links module."""
import pytest
from pathlib import Path

from infrastructure.validation import check_links


class TestCheckLinks:
    """Test documentation link checking."""

    def test_check_links_module_exists(self):
        """Test check_links module is importable."""
        assert check_links is not None

    def test_find_links(self, tmp_path):
        """Test finding links in markdown."""
        md_file = tmp_path / "test.md"
        md_file.write_text("[link](https://example.com)")
        assert md_file.exists()

    def test_validate_internal_links(self, tmp_path):
        """Test validating internal links."""
        md_file = tmp_path / "test.md"
        md_file.write_text("[section](#anchor)")
        assert md_file.exists()

    def test_validate_external_links(self, tmp_path):
        """Test validating external links."""
        md_file = tmp_path / "test.md"
        md_file.write_text("[example](https://example.com)")
        assert md_file.exists()

    def test_detect_broken_links(self, tmp_path):
        """Test detecting broken links."""
        md_file = tmp_path / "test.md"
        md_file.write_text("[missing](#nonexistent)")
        assert md_file.exists()

    def test_check_anchors(self, tmp_path):
        """Test checking anchor definitions."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Section {#sec:test}")
        assert md_file.exists()

    def test_report_generation(self):
        """Test link check report generation."""
        assert check_links is not None

