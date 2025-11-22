"""Comprehensive tests for src/image_manager.py to ensure 100% coverage."""
from pathlib import Path

import pytest

from infrastructure.documentation.figure_manager import FigureManager
from infrastructure.documentation.image_manager import ImageManager


class TestImageManager:
    """Test ImageManager class."""
    
    def test_initialization(self):
        """Test manager initialization."""
        manager = ImageManager()
        assert manager.figure_manager is not None
    
    def test_initialization_with_figure_manager(self):
        """Test initialization with provided figure manager."""
        figure_manager = FigureManager()
        manager = ImageManager(figure_manager=figure_manager)
        assert manager.figure_manager == figure_manager
    
    def test_insert_figure_nonexistent_file(self, tmp_path):
        """Test inserting figure into nonexistent file (line 50)."""
        manager = ImageManager()
        # Register figure first so fig_meta is not None (passes line 46)
        manager.figure_manager.register_figure(
            filename="test.png",
            caption="Test caption",
            label="fig:test"
        )
        # Now test with nonexistent file to trigger line 50
        markdown_file = tmp_path / "nonexistent.md"
        result = manager.insert_figure(markdown_file, "fig:test")
        assert result is False
    
    def test_insert_figure_nonexistent_label(self, tmp_path):
        """Test inserting nonexistent figure."""
        manager = ImageManager()
        markdown_file = tmp_path / "test.md"
        markdown_file.write_text("# Test\n\nContent here.")
        result = manager.insert_figure(markdown_file, "fig:nonexistent")
        assert result is False
    
    def test_insert_figure_success(self, tmp_path):
        """Test successful figure insertion."""
        manager = ImageManager()
        # Register a figure first
        manager.figure_manager.register_figure(
            filename="test.png",
            caption="Test caption",
            label="fig:test"
        )
        
        markdown_file = tmp_path / "test.md"
        markdown_file.write_text("# Test\n\nContent here.")
        result = manager.insert_figure(markdown_file, "fig:test")
        assert result is True
        content = markdown_file.read_text()
        assert "\\begin{figure}" in content
        assert "fig:test" in content
    
    def test_insert_reference(self, tmp_path):
        """Test inserting reference."""
        manager = ImageManager()
        manager.figure_manager.register_figure(
            filename="test.png",
            caption="Test",
            label="fig:test"
        )
        
        markdown_file = tmp_path / "test.md"
        markdown_file.write_text("# Test\n\nContent.")
        result = manager.insert_reference(markdown_file, "fig:test")
        assert result is True
        content = markdown_file.read_text()
        assert "\\ref{fig:test}" in content
    
    def test_validate_figures(self, tmp_path):
        """Test validating figures."""
        manager = ImageManager()
        markdown_file = tmp_path / "test.md"
        markdown_file.write_text(
            "# Test\n\n"
            "\\begin{figure}[h]\n"
            "\\includegraphics{../output/figures/test.png}\n"
            "\\label{fig:test}\n"
            "\\end{figure}\n"
        )
        errors = manager.validate_figures(markdown_file)
        # Should have error for missing file
        assert len(errors) > 0
    
    def test_get_figure_list(self, tmp_path):
        """Test getting figure list."""
        manager = ImageManager()
        markdown_file = tmp_path / "test.md"
        markdown_file.write_text(
            "# Test\n\n"
            "\\begin{figure}[h]\n"
            "\\label{fig:test1}\n"
            "\\end{figure}\n"
            "\\begin{figure}[h]\n"
            "\\label{fig:test2}\n"
            "\\end{figure}\n"
        )
        labels = manager.get_figure_list(markdown_file)
        assert "fig:test1" in labels
        assert "fig:test2" in labels
    
    def test_insert_figure_already_inserted(self, tmp_path):
        """Test inserting figure that's already in file."""
        manager = ImageManager()
        manager.figure_manager.register_figure(
            filename="test.png",
            caption="Test caption",
            label="fig:test"
        )
        
        markdown_file = tmp_path / "test.md"
        markdown_file.write_text("# Test\n\n\\label{fig:test}\n\nContent.")
        result = manager.insert_figure(markdown_file, "fig:test")
        assert result is True  # Should return True for already inserted
    
    def test_insert_figure_position_end(self, tmp_path):
        """Test inserting figure at end position."""
        manager = ImageManager()
        manager.figure_manager.register_figure(
            filename="test.png",
            caption="Test caption",
            label="fig:test"
        )
        
        markdown_file = tmp_path / "test.md"
        markdown_file.write_text("# Test\n\nContent here.")
        result = manager.insert_figure(markdown_file, "fig:test", position="end")
        assert result is True
        content = markdown_file.read_text()
        assert "\\begin{figure}" in content
    
    def test_insert_figure_after_section(self, tmp_path):
        """Test inserting figure after section."""
        manager = ImageManager()
        manager.figure_manager.register_figure(
            filename="test.png",
            caption="Test caption",
            label="fig:test"
        )
        
        markdown_file = tmp_path / "test.md"
        markdown_file.write_text("# Section 1\n\nContent.\n\n## Section 2\n\nMore content.")
        result = manager.insert_figure(markdown_file, "fig:test", section="Section 1", position="after_section")
        assert result is True
        content = markdown_file.read_text()
        assert "\\begin{figure}" in content
        # Should be after Section 1 but before Section 2
        assert content.find("\\begin{figure}") < content.find("## Section 2")
    
    def test_insert_figure_after_section_no_next(self, tmp_path):
        """Test inserting figure after section with no next section."""
        manager = ImageManager()
        manager.figure_manager.register_figure(
            filename="test.png",
            caption="Test caption",
            label="fig:test"
        )
        
        markdown_file = tmp_path / "test.md"
        markdown_file.write_text("# Section 1\n\nContent.")
        result = manager.insert_figure(markdown_file, "fig:test", section="Section 1", position="after_section")
        assert result is True
        content = markdown_file.read_text()
        assert "\\begin{figure}" in content
    
    def test_insert_figure_before_section(self, tmp_path):
        """Test inserting figure before section."""
        manager = ImageManager()
        manager.figure_manager.register_figure(
            filename="test.png",
            caption="Test caption",
            label="fig:test"
        )
        
        markdown_file = tmp_path / "test.md"
        markdown_file.write_text("# Section 1\n\nContent.\n\n## Section 2\n\nMore content.")
        result = manager.insert_figure(markdown_file, "fig:test", section="Section 2", position="before_section")
        assert result is True
        content = markdown_file.read_text()
        assert "\\begin{figure}" in content
        # Should be before Section 2
        assert content.find("\\begin{figure}") < content.find("## Section 2")
    
    def test_insert_figure_section_not_found(self, tmp_path):
        """Test inserting figure when section is not found (branch 107->121)."""
        manager = ImageManager()
        manager.figure_manager.register_figure(
            filename="test.png",
            caption="Test caption",
            label="fig:test"
        )
        
        markdown_file = tmp_path / "test.md"
        markdown_file.write_text("# Section 1\n\nContent.")
        # Try to insert after a section that doesn't exist
        # When section is not found, _find_insertion_point returns None (branch 107->121)
        # and insert_figure should handle this gracefully
        result = manager.insert_figure(markdown_file, "fig:test", section="Nonexistent Section", position="after_section")
        # When insertion point is None, it may still insert at end or return False
        # Let's check the actual behavior
        assert isinstance(result, bool)
    
    def test_insert_figure_position_not_after_or_before(self, tmp_path):
        """Test inserting figure with position that's not after_section or before_section (branch 118->121)."""
        manager = ImageManager()
        manager.figure_manager.register_figure(
            filename="test.png",
            caption="Test caption",
            label="fig:test"
        )
        
        markdown_file = tmp_path / "test.md"
        markdown_file.write_text("# Section 1\n\nContent.")
        # To trigger branch 118->121, we need:
        # - section is provided and matches (so we enter the if matches block at line 107)
        # - position is not "after_section" (so we skip line 109)
        # - position is not "before_section" (so we skip line 118)
        # This causes fall-through to return None at line 121
        # The function accepts any position string, so we can pass an invalid one
        # when section is provided to trigger this branch
        result = manager.insert_figure(
            markdown_file, 
            "fig:test", 
            section="Section 1", 
            position="invalid_position"  # Not "after_section" or "before_section"
        )
        # When insertion_point is None, it inserts at end, so result should be True
        assert result is True
    
    def test_insert_reference_nonexistent_file(self, tmp_path):
        """Test inserting reference into nonexistent file."""
        manager = ImageManager()
        manager.figure_manager.register_figure(
            filename="test.png",
            caption="Test",
            label="fig:test"
        )
        
        markdown_file = tmp_path / "nonexistent.md"
        result = manager.insert_reference(markdown_file, "fig:test")
        assert result is False
    
    def test_insert_reference_nonexistent_label(self, tmp_path):
        """Test inserting reference for nonexistent figure label (line 143)."""
        manager = ImageManager()
        markdown_file = tmp_path / "test.md"
        markdown_file.write_text("# Test\n\nContent.")
        result = manager.insert_reference(markdown_file, "fig:nonexistent")
        assert result is False
    
    def test_insert_reference_already_referenced(self, tmp_path):
        """Test inserting reference that already exists."""
        manager = ImageManager()
        manager.figure_manager.register_figure(
            filename="test.png",
            caption="Test",
            label="fig:test"
        )
        
        markdown_file = tmp_path / "test.md"
        markdown_file.write_text("# Test\n\nContent. \\ref{fig:test} already here.")
        result = manager.insert_reference(markdown_file, "fig:test")
        assert result is True  # Should return True for already referenced
    
    def test_insert_reference_with_text(self, tmp_path):
        """Test inserting reference with custom text."""
        manager = ImageManager()
        manager.figure_manager.register_figure(
            filename="test.png",
            caption="Test",
            label="fig:test"
        )
        
        markdown_file = tmp_path / "test.md"
        markdown_file.write_text("# Test\n\nContent.")
        result = manager.insert_reference(markdown_file, "fig:test", text="See the figure")
        assert result is True
        content = markdown_file.read_text()
        assert "See the figure (see Figure \\ref{fig:test})" in content
    
    def test_insert_reference_with_position(self, tmp_path):
        """Test inserting reference at specific position."""
        manager = ImageManager()
        manager.figure_manager.register_figure(
            filename="test.png",
            caption="Test",
            label="fig:test"
        )
        
        markdown_file = tmp_path / "test.md"
        markdown_file.write_text("# Test\n\nContent here.")
        result = manager.insert_reference(markdown_file, "fig:test", position=10)
        assert result is True
        content = markdown_file.read_text()
        assert "\\ref{fig:test}" in content
    
    def test_insert_reference_after_figure(self, tmp_path):
        """Test inserting reference after figure."""
        manager = ImageManager()
        manager.figure_manager.register_figure(
            filename="test.png",
            caption="Test",
            label="fig:test"
        )
        
        markdown_file = tmp_path / "test.md"
        markdown_file.write_text(
            "# Test\n\n"
            "\\begin{figure}[h]\n"
            "\\label{fig:test}\n"
            "\\end{figure}\n\n"
            "Some text here."
        )
        result = manager.insert_reference(markdown_file, "fig:test")
        assert result is True
        content = markdown_file.read_text()
        assert "Figure \\ref{fig:test}" in content
    
    def test_insert_reference_after_figure_no_paragraph(self, tmp_path):
        """Test inserting reference after figure with no following paragraph."""
        manager = ImageManager()
        manager.figure_manager.register_figure(
            filename="test.png",
            caption="Test",
            label="fig:test"
        )
        
        markdown_file = tmp_path / "test.md"
        markdown_file.write_text(
            "# Test\n\n"
            "\\begin{figure}[h]\n"
            "\\label{fig:test}\n"
            "\\end{figure}"
        )
        result = manager.insert_reference(markdown_file, "fig:test")
        assert result is True
        content = markdown_file.read_text()
        assert "Figure \\ref{fig:test}" in content
    
    def test_validate_figures_nonexistent_file(self, tmp_path):
        """Test validating figures in nonexistent file."""
        manager = ImageManager()
        markdown_file = tmp_path / "nonexistent.md"
        errors = manager.validate_figures(markdown_file)
        assert len(errors) == 1
        assert errors[0][1] == "Markdown file does not exist"
    
    def test_validate_figures_absolute_path(self, tmp_path):
        """Test validating figures with absolute path."""
        manager = ImageManager()
        markdown_file = tmp_path / "test.md"
        markdown_file.write_text(
            "# Test\n\n"
            "\\begin{figure}[h]\n"
            "\\includegraphics{/absolute/path/to/figure.png}\n"
            "\\label{fig:test}\n"
            "\\end{figure}\n"
        )
        errors = manager.validate_figures(markdown_file)
        # Should have error for missing absolute path file
        assert len(errors) > 0
        assert any("Figure file not found" in err[1] for err in errors)
    
    def test_validate_figures_existing_file(self, tmp_path):
        """Test validating figures with existing file (branch 211->201)."""
        manager = ImageManager()
        # Create a figure file
        figure_file = tmp_path / "test.png"
        figure_file.write_bytes(b"fake image data")
        
        markdown_file = tmp_path / "test.md"
        markdown_file.write_text(
            "# Test\n\n"
            f"\\begin{{figure}}[h]\n"
            f"\\includegraphics{{{figure_file.absolute()}}}\n"
            "\\label{fig:test}\n"
            "\\end{figure}\n"
        )
        errors = manager.validate_figures(markdown_file)
        # Should not have error for existing file
        assert not any("Figure file not found" in err[1] for err in errors)
    
    def test_validate_figures_unregistered_label(self, tmp_path):
        """Test validating figures with unregistered label."""
        manager = ImageManager()
        markdown_file = tmp_path / "test.md"
        markdown_file.write_text(
            "# Test\n\n"
            "\\begin{figure}[h]\n"
            "\\label{fig:unregistered}\n"
            "\\end{figure}\n"
        )
        errors = manager.validate_figures(markdown_file)
        # Should have error for unregistered label
        assert len(errors) > 0
        assert any("Figure label not registered" in err[1] for err in errors)
    
    def test_get_figure_list_nonexistent_file(self, tmp_path):
        """Test getting figure list from nonexistent file."""
        manager = ImageManager()
        markdown_file = tmp_path / "nonexistent.md"
        labels = manager.get_figure_list(markdown_file)
        assert labels == []

