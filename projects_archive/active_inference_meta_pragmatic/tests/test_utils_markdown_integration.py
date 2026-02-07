"""Tests for utils/markdown_integration.py module.

Tests for the MarkdownIntegration class, verifying section detection
and figure insertion into markdown files.
"""

from pathlib import Path

import pytest
from src.utils.markdown_integration import MarkdownIntegration


class TestMarkdownIntegration:
    """Test MarkdownIntegration class functionality."""

    def test_initialization(self, tmp_path):
        """Test MarkdownIntegration initialization."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        integration = MarkdownIntegration(manuscript_dir)

        assert integration.manuscript_dir == manuscript_dir

    def test_initialization_with_path_string(self, tmp_path):
        """Test initialization with string path."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        integration = MarkdownIntegration(str(manuscript_dir))

        # Path should be converted to Path object
        assert integration.manuscript_dir == manuscript_dir or str(
            integration.manuscript_dir
        ) == str(manuscript_dir)

    def test_detect_sections_finds_headings(self, tmp_path):
        """Test that detect_sections finds markdown headings."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        markdown_file = manuscript_dir / "test.md"
        markdown_file.write_text("# Section 1\n\nContent\n\n## Subsection")

        integration = MarkdownIntegration(manuscript_dir)

        result = integration.detect_sections(markdown_file)

        assert isinstance(result, list)
        assert len(result) == 2
        assert "Section 1" in result
        assert "Subsection" in result

    def test_detect_sections_nonexistent_file(self, tmp_path):
        """Test detect_sections with non-existent file."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        nonexistent_file = manuscript_dir / "nonexistent.md"

        integration = MarkdownIntegration(manuscript_dir)

        result = integration.detect_sections(nonexistent_file)

        assert isinstance(result, list)
        assert len(result) == 0

    def test_detect_sections_empty_file(self, tmp_path):
        """Test detect_sections with empty file."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        empty_file = manuscript_dir / "empty.md"
        empty_file.write_text("")

        integration = MarkdownIntegration(manuscript_dir)

        result = integration.detect_sections(empty_file)

        assert isinstance(result, list)
        assert len(result) == 0

    def test_insert_figure_in_section_success(self, tmp_path):
        """Test that insert_figure_in_section inserts a figure block."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        markdown_file = manuscript_dir / "test.md"
        markdown_file.write_text(
            "# Section 1\n\nContent paragraph.\n\n## Next Section\n\nMore content."
        )

        integration = MarkdownIntegration(manuscript_dir)

        result = integration.insert_figure_in_section(
            markdown_file,
            "fig:test",
            "Section 1",
            caption="Test figure caption",
            filename="test_figure.png",
        )

        assert result is True
        content = markdown_file.read_text()
        assert "\\label{fig:test}" in content
        assert "\\caption{Test figure caption}" in content
        assert "test_figure.png" in content

    def test_insert_figure_in_section_default_width(self, tmp_path):
        """Test insert_figure_in_section with default width parameter."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        markdown_file = manuscript_dir / "test.md"
        markdown_file.write_text("# Section 1\n\nContent")

        integration = MarkdownIntegration(manuscript_dir)

        result = integration.insert_figure_in_section(
            markdown_file,
            "fig:test",
            "Section 1",
            caption="Test",
            filename="test.png",
        )

        assert result is True
        content = markdown_file.read_text()
        assert "width=0.8\\textwidth" in content

    def test_insert_figure_in_section_custom_width(self, tmp_path):
        """Test insert_figure_in_section with custom width."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        markdown_file = manuscript_dir / "test.md"
        markdown_file.write_text("# Section 1\n\nContent")

        integration = MarkdownIntegration(manuscript_dir)

        result = integration.insert_figure_in_section(
            markdown_file,
            "fig:test",
            "Section 1",
            width=0.9,
            caption="Test",
            filename="test.png",
        )

        assert result is True
        content = markdown_file.read_text()
        assert "width=0.9\\textwidth" in content

    def test_insert_figure_in_section_nonexistent_file(self, tmp_path):
        """Test insert_figure_in_section with non-existent file."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        nonexistent_file = manuscript_dir / "nonexistent.md"

        integration = MarkdownIntegration(manuscript_dir)

        result = integration.insert_figure_in_section(
            nonexistent_file, "fig:test", "Section 1"
        )

        assert result is False

    def test_insert_figure_in_section_nonexistent_section(self, tmp_path):
        """Test insert_figure_in_section with non-existent section."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        markdown_file = manuscript_dir / "test.md"
        markdown_file.write_text("# Section 1\n\nContent")

        integration = MarkdownIntegration(manuscript_dir)

        result = integration.insert_figure_in_section(
            markdown_file, "fig:test", "Nonexistent Section"
        )

        assert result is False

    def test_insert_figure_duplicate_skip(self, tmp_path):
        """Test that duplicate figure insertion is skipped."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        markdown_file = manuscript_dir / "test.md"
        markdown_file.write_text("# Section 1\n\nContent")

        integration = MarkdownIntegration(manuscript_dir)

        # First insertion
        result1 = integration.insert_figure_in_section(
            markdown_file,
            "fig:test",
            "Section 1",
            caption="Test",
            filename="test.png",
        )
        # Second insertion of same figure — should skip
        result2 = integration.insert_figure_in_section(
            markdown_file,
            "fig:test",
            "Section 1",
            caption="Test",
            filename="test.png",
        )

        assert result1 is True
        assert result2 is True  # Returns True (already exists)
        # But only one instance should exist
        content = markdown_file.read_text()
        assert content.count("\\label{fig:test}") == 1

    def test_multiple_operations(self, tmp_path):
        """Test multiple operations on same instance."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        markdown_file = manuscript_dir / "test.md"
        markdown_file.write_text("# Section 1\n\nContent\n\n## Section 2\n\nMore")

        integration = MarkdownIntegration(manuscript_dir)

        # Multiple detect_sections calls
        result1 = integration.detect_sections(markdown_file)
        result2 = integration.detect_sections(markdown_file)

        # Multiple insert_figure calls
        result3 = integration.insert_figure_in_section(
            markdown_file,
            "fig:1",
            "Section 1",
            caption="First figure",
            filename="fig1.png",
        )
        result4 = integration.insert_figure_in_section(
            markdown_file,
            "fig:2",
            "Section 2",
            caption="Second figure",
            filename="fig2.png",
        )

        assert isinstance(result1, list)
        assert isinstance(result2, list)
        assert result3 is True
        assert result4 is True
        content = markdown_file.read_text()
        assert "\\label{fig:1}" in content
        assert "\\label{fig:2}" in content
