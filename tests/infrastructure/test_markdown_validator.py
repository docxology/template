#!/usr/bin/env python3
"""Tests for infrastructure/markdown_validator.py"""

import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add infrastructure to path for imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, ROOT)

from infrastructure.markdown_validator import (
    find_markdown_files,
    collect_symbols,
    validate_images,
    validate_refs,
    validate_math,
    validate_markdown,
    find_manuscript_directory,
)


class TestFindMarkdownFiles:
    """Test find_markdown_files function."""
    
    def test_finds_and_sorts_markdown_files(self, tmp_path):
        """Test find_markdown_files finds and sorts markdown files."""
        # Create test markdown files
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "02_second.md").write_text("content")
        (manuscript / "01_first.md").write_text("content")
        (manuscript / "not_md.txt").write_text("content")
        
        files = find_markdown_files(manuscript)
        
        assert len(files) == 2
        assert "01_first.md" in files[0]
        assert "02_second.md" in files[1]
    
    def test_nonexistent_directory_raises(self, tmp_path):
        """Test find_markdown_files raises on nonexistent directory."""
        with pytest.raises(FileNotFoundError):
            find_markdown_files(tmp_path / "nonexistent")
    
    def test_file_instead_of_directory_raises(self, tmp_path):
        """Test find_markdown_files raises when given a file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        with pytest.raises(NotADirectoryError):
            find_markdown_files(test_file)
    
    def test_empty_directory(self, tmp_path):
        """Test find_markdown_files with empty directory."""
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        
        files = find_markdown_files(manuscript)
        
        assert files == []


class TestCollectSymbols:
    """Test collect_symbols function."""
    
    def test_extracts_labels_and_anchors(self, tmp_path):
        """Test collect_symbols extracts labels and anchors."""
        # Create test markdown files
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test1.md").write_text(
            "\\begin{equation}\\label{eq:test1}\\end{equation}\n"
            "# Section {#sec:test1}\n"
        )
        (manuscript / "test2.md").write_text(
            "\\begin{equation}\\label{eq:test2}\\end{equation}\n"
            "## Subsection {#subsec:test2}\n"
        )
        
        labels, anchors = collect_symbols([
            str(manuscript / "test1.md"),
            str(manuscript / "test2.md")
        ])
        
        assert labels == {"eq:test1", "eq:test2"}
        assert anchors == {"sec:test1", "subsec:test2"}
    
    def test_empty_file_list(self):
        """Test collect_symbols with empty file list."""
        labels, anchors = collect_symbols([])
        
        assert labels == set()
        assert anchors == set()


class TestValidateImages:
    """Test validate_images function."""
    
    def test_detects_missing_image(self, tmp_path):
        """Test validate_images detects missing images."""
        # Create test markdown file
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text(
            "![alt text](../output/figures/missing.png)"
        )
        
        problems = validate_images([str(manuscript / "test.md")], tmp_path)
        
        assert len(problems) == 1
        assert "Missing image: ../output/figures/missing.png" in problems[0]
    
    def test_validates_existing_image(self, tmp_path):
        """Test validate_images doesn't flag existing images."""
        # Create test markdown file and image
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text(
            "![alt text](../output/figures/existing.png)"
        )
        (tmp_path / "output" / "figures").mkdir(parents=True)
        (tmp_path / "output" / "figures" / "existing.png").write_text("fake image")
        
        problems = validate_images([str(manuscript / "test.md")], tmp_path)
        
        assert len(problems) == 0
    
    def test_absolute_path(self, tmp_path):
        """Test validate_images with absolute image paths."""
        # Create test markdown file with absolute path
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        abs_image_path = str(tmp_path / "absolute_image.png")
        (manuscript / "test.md").write_text(
            f"![alt text]({abs_image_path})"
        )
        
        # Don't create the image file so it will be missing
        problems = validate_images([str(manuscript / "test.md")], tmp_path)
        
        assert len(problems) == 1
        assert abs_image_path in problems[0]


class TestValidateRefs:
    """Test validate_refs function."""
    
    def test_detects_missing_equation_label(self, tmp_path):
        """Test validate_refs detects missing equation labels."""
        # Create test markdown file
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text(
            "Reference to \\eqref{eq:missing}"
        )
        
        problems = validate_refs([str(manuscript / "test.md")], set(), set(), tmp_path)
        
        assert len(problems) == 1
        assert "Missing equation label for \\eqref{eq:missing}" in problems[0]
    
    def test_detects_missing_anchor(self, tmp_path):
        """Test validate_refs detects missing anchors."""
        # Create test markdown file
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text(
            "Link to [section](#missing_anchor)"
        )
        
        problems = validate_refs([str(manuscript / "test.md")], set(), set(), tmp_path)
        
        assert len(problems) == 1
        assert "Missing anchor/label for link (#missing_anchor)" in problems[0]
    
    def test_detects_bare_url(self, tmp_path):
        """Test validate_refs detects bare URLs."""
        # Create test markdown file
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text(
            "Visit https://example.com for more info"
        )
        
        problems = validate_refs([str(manuscript / "test.md")], set(), set(), tmp_path)
        
        assert len(problems) == 1
        assert "Bare URL found" in problems[0]
    
    def test_detects_non_informative_link(self, tmp_path):
        """Test validate_refs detects non-informative link text."""
        # Create test markdown file
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text(
            "[https://example.com](https://example.com)"
        )
        
        problems = validate_refs([str(manuscript / "test.md")], set(), set(), tmp_path)
        
        # The regex patterns can detect multiple issues with the same text
        assert len(problems) >= 1
        assert any("Non-informative link text" in p for p in problems)


class TestValidateMath:
    """Test validate_math function."""
    
    def test_detects_dollar_math(self, tmp_path):
        """Test validate_math detects dollar math notation."""
        # Create test markdown file with $$ math
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text(
            "Math: $$x^2 + y^2 = z^2$$"
        )
        
        problems = validate_math([str(manuscript / "test.md")], tmp_path)
        
        assert len(problems) == 1
        assert "Use equation environment instead of $$" in problems[0]
    
    def test_detects_bracket_math(self, tmp_path):
        """Test validate_math detects bracket math notation."""
        # Create test markdown file
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text(
            "Math: \\[x^2 + y^2 = z^2\\]"
        )
        
        problems = validate_math([str(manuscript / "test.md")], tmp_path)
        
        assert len(problems) == 1
        assert "Use equation environment instead of \\[ \\]" in problems[0]
    
    def test_detects_missing_label(self, tmp_path):
        """Test validate_math detects equations without labels."""
        # Create test markdown file
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text(
            r"\begin{equation}x^2 + y^2 = z^2\end{equation}"
        )
        
        problems = validate_math([str(manuscript / "test.md")], tmp_path)
        
        assert len(problems) == 1
        assert "Equation missing \\label{...}" in problems[0]
    
    def test_detects_duplicate_label(self, tmp_path):
        """Test validate_math detects duplicate equation labels."""
        # Create test markdown file
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text(
            r"\begin{equation}\label{eq:duplicate}x^2\end{equation}" + "\n"
            r"\begin{equation}\label{eq:duplicate}y^2\end{equation}"
        )
        
        problems = validate_math([str(manuscript / "test.md")], tmp_path)
        
        assert len(problems) == 1
        assert "Duplicate equation label '{eq:duplicate}'" in problems[0]
    
    def test_accepts_valid_equations(self, tmp_path):
        """Test validate_math accepts valid labeled equations."""
        # Create test markdown file
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text(
            "\\begin{equation}\\label{eq:valid1}x^2 + y^2 = z^2\\end{equation}\n"
            "\\begin{equation}\\label{eq:valid2}a^2 + b^2 = c^2\\end{equation}"
        )
        
        problems = validate_math([str(manuscript / "test.md")], tmp_path)
        
        assert len(problems) == 0


class TestValidateMarkdown:
    """Test validate_markdown function."""
    
    def test_no_problems_returns_zero(self, tmp_path):
        """Test validate_markdown returns 0 when no problems found."""
        # Create test markdown directory with valid content
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text("# Test\n\nNo problems here.")
        
        problems, exit_code = validate_markdown(manuscript, tmp_path, strict=False)
        
        assert exit_code == 0
        assert problems == []
    
    def test_problems_non_strict_returns_zero(self, tmp_path):
        """Test validate_markdown returns 0 with problems in non-strict mode."""
        # Create test markdown directory with problems
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text("\\begin{equation}x^2\\end{equation}")
        
        problems, exit_code = validate_markdown(manuscript, tmp_path, strict=False)
        
        assert exit_code == 0
        assert len(problems) > 0
    
    def test_problems_strict_returns_one(self, tmp_path):
        """Test validate_markdown returns 1 with problems in strict mode."""
        # Create test markdown directory with problems
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text("\\begin{equation}x^2\\end{equation}")
        
        problems, exit_code = validate_markdown(manuscript, tmp_path, strict=True)
        
        assert exit_code == 1
        assert len(problems) > 0
    
    def test_nonexistent_directory_raises(self, tmp_path):
        """Test validate_markdown raises on nonexistent directory."""
        with pytest.raises(FileNotFoundError):
            validate_markdown(tmp_path / "nonexistent", tmp_path)
    
    def test_empty_directory_returns_zero(self, tmp_path):
        """Test validate_markdown with empty directory."""
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        
        problems, exit_code = validate_markdown(manuscript, tmp_path)
        
        assert exit_code == 0
        assert problems == []


class TestFindManuscriptDirectory:
    """Test find_manuscript_directory function."""
    
    def test_finds_project_manuscript(self, tmp_path):
        """Test find_manuscript_directory finds project/manuscript."""
        manuscript = tmp_path / "project" / "manuscript"
        manuscript.mkdir(parents=True)
        
        result = find_manuscript_directory(tmp_path)
        
        assert result == manuscript
    
    def test_finds_legacy_manuscript(self, tmp_path):
        """Test find_manuscript_directory finds legacy manuscript."""
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        
        result = find_manuscript_directory(tmp_path)
        
        assert result == manuscript
    
    def test_prefers_project_over_legacy(self, tmp_path):
        """Test find_manuscript_directory prefers project/manuscript."""
        project_manuscript = tmp_path / "project" / "manuscript"
        project_manuscript.mkdir(parents=True)
        legacy_manuscript = tmp_path / "manuscript"
        legacy_manuscript.mkdir()
        
        result = find_manuscript_directory(tmp_path)
        
        assert result == project_manuscript
    
    def test_raises_when_not_found(self, tmp_path):
        """Test find_manuscript_directory raises when not found."""
        with pytest.raises(FileNotFoundError):
            find_manuscript_directory(tmp_path)


class TestIntegration:
    """Integration tests for the complete validation flow."""
    
    def test_full_validation_flow(self, tmp_path):
        """Test complete validation with images, refs, and math."""
        # Create test project structure
        output_dir = tmp_path / "output" / "figures"
        output_dir.mkdir(parents=True)
        (output_dir / "test_figure.png").write_text("fake image")
        
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text(r"""
# Test Section {#sec:test}

Valid content with image:

![Test Figure](../output/figures/test_figure.png)

Valid equation:

\begin{equation}\label{eq:test}
x^2 + y^2 = z^2
\end{equation}

Valid reference: \eqref{eq:test}

Valid link: [See section](#sec:test)
""")
        
        problems, exit_code = validate_markdown(manuscript, tmp_path)
        
        assert exit_code == 0
        assert problems == []
    
    def test_multiple_problems_detected(self, tmp_path):
        """Test detection of multiple types of problems."""
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text(r"""
# Test Section

Missing image: ![Missing](../output/figures/missing.png)

Dollar math: $$x^2$$

Unlabeled equation: \begin{equation}x^2\end{equation}

Missing ref: \eqref{eq:missing}

Bare URL: https://example.com
""")
        
        problems, exit_code = validate_markdown(manuscript, tmp_path, strict=False)
        
        assert exit_code == 0  # Non-strict mode
        assert len(problems) >= 5  # At least 5 different types of problems

