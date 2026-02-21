"""Dedicated tests for core/markdown_integration.py module.

Covers: MarkdownIntegration (init, detect_sections, insert_figure_in_section),
ImageManager (init, register_image, get_image_info).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from core.markdown_integration import ImageManager, MarkdownIntegration


class TestMarkdownIntegration:
    """Test MarkdownIntegration class."""

    def test_init_stores_directory(self, tmp_path):
        """Test initialization stores manuscript directory."""
        integration = MarkdownIntegration(tmp_path)
        assert integration.manuscript_dir == tmp_path

    def test_init_with_path_object(self, tmp_path):
        """Test initialization with Path object."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        integration = MarkdownIntegration(manuscript_dir)
        assert isinstance(integration.manuscript_dir, Path)

    def test_detect_sections_returns_empty_list(self, tmp_path):
        """Test detect_sections returns empty list (stub)."""
        integration = MarkdownIntegration(tmp_path)
        md_file = tmp_path / "test.md"
        md_file.write_text("# Section 1\nContent\n## Section 2\nMore content")
        result = integration.detect_sections(md_file)
        assert result == []
        assert isinstance(result, list)

    def test_detect_sections_nonexistent_file(self, tmp_path):
        """Test detect_sections with nonexistent file."""
        integration = MarkdownIntegration(tmp_path)
        result = integration.detect_sections(tmp_path / "nonexistent.md")
        assert result == []

    def test_insert_figure_returns_false(self, tmp_path):
        """Test insert_figure_in_section returns False (stub)."""
        integration = MarkdownIntegration(tmp_path)
        md_file = tmp_path / "test.md"
        md_file.write_text("# Introduction\nSome content here.")
        result = integration.insert_figure_in_section(
            md_file, "fig:test", "Introduction"
        )
        assert result is False

    def test_insert_figure_position_before(self, tmp_path):
        """Test insert_figure_in_section with position='before'."""
        integration = MarkdownIntegration(tmp_path)
        md_file = tmp_path / "test.md"
        md_file.write_text("# Methods\nContent")
        result = integration.insert_figure_in_section(
            md_file, "fig:methods", "Methods", position="before"
        )
        assert result is False

    def test_insert_figure_position_after(self, tmp_path):
        """Test insert_figure_in_section with default position='after'."""
        integration = MarkdownIntegration(tmp_path)
        md_file = tmp_path / "test.md"
        md_file.write_text("# Results\nContent")
        result = integration.insert_figure_in_section(
            md_file, "fig:results", "Results", position="after"
        )
        assert result is False


class TestImageManager:
    """Test ImageManager class."""

    def test_init_empty_images(self):
        """Test initialization creates empty images dict."""
        manager = ImageManager()
        assert manager.images == {}

    def test_register_image_basic(self):
        """Test registering an image with caption only."""
        manager = ImageManager()
        manager.register_image("figure1.png", "Colony foraging patterns")
        assert "figure1.png" in manager.images
        assert manager.images["figure1.png"]["caption"] == "Colony foraging patterns"
        assert manager.images["figure1.png"]["alt_text"] is None

    def test_register_image_with_alt_text(self):
        """Test registering an image with alt text."""
        manager = ImageManager()
        manager.register_image("figure2.png", "Ant trails", alt_text="Trail network diagram")
        info = manager.images["figure2.png"]
        assert info["caption"] == "Ant trails"
        assert info["alt_text"] == "Trail network diagram"

    def test_register_multiple_images(self):
        """Test registering multiple images."""
        manager = ImageManager()
        manager.register_image("fig1.png", "First figure")
        manager.register_image("fig2.png", "Second figure")
        manager.register_image("fig3.png", "Third figure")
        assert len(manager.images) == 3

    def test_register_overwrites_existing(self):
        """Test that registering same filename overwrites."""
        manager = ImageManager()
        manager.register_image("fig.png", "Original caption")
        manager.register_image("fig.png", "Updated caption")
        assert manager.images["fig.png"]["caption"] == "Updated caption"

    def test_get_image_info_existing(self):
        """Test getting info for registered image."""
        manager = ImageManager()
        manager.register_image("test.png", "Test", alt_text="Alt")
        info = manager.get_image_info("test.png")
        assert info is not None
        assert info["caption"] == "Test"
        assert info["alt_text"] == "Alt"

    def test_get_image_info_nonexistent(self):
        """Test getting info for unregistered image."""
        manager = ImageManager()
        info = manager.get_image_info("missing.png")
        assert info is None

    def test_get_image_info_after_overwrite(self):
        """Test info reflects latest registration."""
        manager = ImageManager()
        manager.register_image("fig.png", "Old", alt_text="Old alt")
        manager.register_image("fig.png", "New", alt_text="New alt")
        info = manager.get_image_info("fig.png")
        assert info["caption"] == "New"
        assert info["alt_text"] == "New alt"
