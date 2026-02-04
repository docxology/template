"""Comprehensive tests for infrastructure/rendering/manuscript_discovery.py.

Tests manuscript file discovery and figure verification functionality.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.rendering.manuscript_discovery import (
    discover_manuscript_files, verify_figures_exist)


class TestVerifyFiguresExist:
    """Test verify_figures_exist() function."""

    def test_verify_figures_missing_directory(self, tmp_path):
        """Test when figures directory doesn't exist."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        manuscript_dir = project_root / "manuscript"
        manuscript_dir.mkdir()

        result = verify_figures_exist(project_root, manuscript_dir)

        assert result["figures_dir_exists"] is False
        assert result["found_figures"] == []
        assert result["missing_figures"] == []
        assert result["total_expected"] == 0

    def test_verify_figures_empty_directory(self, tmp_path):
        """Test when figures directory exists but is empty."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        figures_dir = project_root / "output" / "figures"
        figures_dir.mkdir(parents=True)
        manuscript_dir = project_root / "manuscript"
        manuscript_dir.mkdir()

        result = verify_figures_exist(project_root, manuscript_dir)

        assert result["figures_dir_exists"] is True
        assert result["found_figures"] == []
        assert result["missing_figures"] == []
        assert result["total_expected"] == 0

    def test_verify_figures_with_png_files(self, tmp_path):
        """Test when figures directory contains PNG files."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        figures_dir = project_root / "output" / "figures"
        figures_dir.mkdir(parents=True)

        # Create PNG files
        (figures_dir / "figure1.png").write_bytes(b"PNG data")
        (figures_dir / "figure2.png").write_bytes(b"PNG data")
        (figures_dir / "other.txt").write_text("Not a PNG")

        manuscript_dir = project_root / "manuscript"
        manuscript_dir.mkdir()

        result = verify_figures_exist(project_root, manuscript_dir)

        assert result["figures_dir_exists"] is True
        assert len(result["found_figures"]) == 2
        assert "figure1.png" in result["found_figures"]
        assert "figure2.png" in result["found_figures"]
        assert "other.txt" not in result["found_figures"]

    def test_verify_figures_sorted(self, tmp_path):
        """Test that found figures are sorted."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        figures_dir = project_root / "output" / "figures"
        figures_dir.mkdir(parents=True)

        # Create PNG files in non-sorted order
        (figures_dir / "z_figure.png").write_bytes(b"PNG data")
        (figures_dir / "a_figure.png").write_bytes(b"PNG data")
        (figures_dir / "m_figure.png").write_bytes(b"PNG data")

        manuscript_dir = project_root / "manuscript"
        manuscript_dir.mkdir()

        result = verify_figures_exist(project_root, manuscript_dir)

        assert result["found_figures"] == [
            "a_figure.png",
            "m_figure.png",
            "z_figure.png",
        ]

    def test_verify_figures_ignores_non_png(self, tmp_path):
        """Test that non-PNG files are ignored."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        figures_dir = project_root / "output" / "figures"
        figures_dir.mkdir(parents=True)

        # Create various file types
        (figures_dir / "figure.png").write_bytes(b"PNG data")
        (figures_dir / "figure.jpg").write_bytes(b"JPG data")
        (figures_dir / "figure.pdf").write_bytes(b"PDF data")
        (figures_dir / "figure.svg").write_text("SVG data")

        manuscript_dir = project_root / "manuscript"
        manuscript_dir.mkdir()

        result = verify_figures_exist(project_root, manuscript_dir)

        assert len(result["found_figures"]) == 1
        assert "figure.png" in result["found_figures"]


class TestDiscoverManuscriptFiles:
    """Test discover_manuscript_files() function."""

    def test_discover_nonexistent_directory(self, tmp_path):
        """Test when manuscript directory doesn't exist."""
        manuscript_dir = tmp_path / "nonexistent"

        result = discover_manuscript_files(manuscript_dir)

        assert result == []

    def test_discover_empty_directory(self, tmp_path):
        """Test when manuscript directory is empty."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        result = discover_manuscript_files(manuscript_dir)

        assert result == []

    def test_discover_main_sections(self, tmp_path):
        """Test discovery of main section files (01_*.md through 09_*.md)."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        # Create main section files
        (manuscript_dir / "01_abstract.md").write_text("# Abstract")
        (manuscript_dir / "02_introduction.md").write_text("# Introduction")
        (manuscript_dir / "03_methodology.md").write_text("# Methodology")

        result = discover_manuscript_files(manuscript_dir)

        assert len(result) == 3
        assert result[0].name == "01_abstract.md"
        assert result[1].name == "02_introduction.md"
        assert result[2].name == "03_methodology.md"

    def test_discover_main_sections_ordering(self, tmp_path):
        """Test that main sections are properly ordered."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        # Create files in non-sequential order
        (manuscript_dir / "03_methodology.md").write_text("# Methodology")
        (manuscript_dir / "01_abstract.md").write_text("# Abstract")
        (manuscript_dir / "02_introduction.md").write_text("# Introduction")

        result = discover_manuscript_files(manuscript_dir)

        assert result[0].name == "01_abstract.md"
        assert result[1].name == "02_introduction.md"
        assert result[2].name == "03_methodology.md"

    def test_discover_supplemental_sections(self, tmp_path):
        """Test discovery of supplemental sections (S01_*.md)."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        (manuscript_dir / "01_abstract.md").write_text("# Abstract")
        (manuscript_dir / "S01_supplement.md").write_text("# Supplement")
        (manuscript_dir / "S02_additional.md").write_text("# Additional")

        result = discover_manuscript_files(manuscript_dir)

        # Main sections should come first, then supplemental
        assert result[0].name == "01_abstract.md"
        assert result[1].name == "S01_supplement.md"
        assert result[2].name == "S02_additional.md"

    def test_discover_glossary_sections(self, tmp_path):
        """Test discovery of glossary sections (98_*.md)."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        (manuscript_dir / "01_abstract.md").write_text("# Abstract")
        (manuscript_dir / "98_glossary.md").write_text("# Glossary")

        result = discover_manuscript_files(manuscript_dir)

        # Glossary should come after main sections
        assert result[0].name == "01_abstract.md"
        assert result[1].name == "98_glossary.md"

    def test_discover_references_sections(self, tmp_path):
        """Test discovery of references sections (99_*.md)."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        (manuscript_dir / "01_abstract.md").write_text("# Abstract")
        (manuscript_dir / "99_references.md").write_text("# References")

        result = discover_manuscript_files(manuscript_dir)

        # References should be last
        assert result[0].name == "01_abstract.md"
        assert result[1].name == "99_references.md"
        assert result[-1].name == "99_references.md"

    def test_discover_references_always_last(self, tmp_path):
        """Test that references are always last, even with other files."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        (manuscript_dir / "01_abstract.md").write_text("# Abstract")
        (manuscript_dir / "99_references.md").write_text("# References")
        (manuscript_dir / "other_file.md").write_text("# Other")

        result = discover_manuscript_files(manuscript_dir)

        # References should be last
        assert result[-1].name == "99_references.md"

    def test_discover_excludes_metadata_files(self, tmp_path):
        """Test that metadata files are excluded."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        # Create manuscript files
        (manuscript_dir / "01_abstract.md").write_text("# Abstract")

        # Create metadata files that should be excluded
        (manuscript_dir / "preamble.md").write_text("Preamble")
        (manuscript_dir / "AGENTS.md").write_text("Agents")
        (manuscript_dir / "README.md").write_text("Readme")
        (manuscript_dir / "config.yaml").write_text("config: value")
        (manuscript_dir / "config.yaml.example").write_text("config: example")
        (manuscript_dir / "references.bib").write_text("@article{test}")

        result = discover_manuscript_files(manuscript_dir)

        # Only manuscript file should be included
        assert len(result) == 1
        assert result[0].name == "01_abstract.md"
        assert not any(
            f.name
            in [
                "preamble.md",
                "AGENTS.md",
                "README.md",
                "config.yaml",
                "config.yaml.example",
                "references.bib",
            ]
            for f in result
        )

    def test_discover_latex_files(self, tmp_path):
        """Test discovery of LaTeX files."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        (manuscript_dir / "01_abstract.md").write_text("# Abstract")
        (manuscript_dir / "main.tex").write_text("\\documentclass{article}")
        (manuscript_dir / "preamble.tex").write_text("\\usepackage{amsmath}")

        result = discover_manuscript_files(manuscript_dir)

        # Should include both markdown and LaTeX files
        assert len(result) == 3
        assert result[0].name == "01_abstract.md"
        assert "main.tex" in [f.name for f in result]
        assert "preamble.tex" in [f.name for f in result]

    def test_discover_latex_files_sorted(self, tmp_path):
        """Test that LaTeX files are sorted."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        (manuscript_dir / "01_abstract.md").write_text("# Abstract")
        (manuscript_dir / "z_file.tex").write_text("Z")
        (manuscript_dir / "a_file.tex").write_text("A")
        (manuscript_dir / "m_file.tex").write_text("M")

        result = discover_manuscript_files(manuscript_dir)

        # LaTeX files should be sorted
        tex_files = [f for f in result if f.suffix == ".tex"]
        assert tex_files[0].name == "a_file.tex"
        assert tex_files[1].name == "m_file.tex"
        assert tex_files[2].name == "z_file.tex"

    def test_discover_complete_structure(self, tmp_path):
        """Test discovery with complete manuscript structure."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        # Create complete structure
        (manuscript_dir / "01_abstract.md").write_text("# Abstract")
        (manuscript_dir / "02_introduction.md").write_text("# Introduction")
        (manuscript_dir / "03_methodology.md").write_text("# Methodology")
        (manuscript_dir / "S01_supplement.md").write_text("# Supplement")
        (manuscript_dir / "98_glossary.md").write_text("# Glossary")
        (manuscript_dir / "99_references.md").write_text("# References")

        result = discover_manuscript_files(manuscript_dir)

        # Verify ordering: main -> supplemental -> glossary -> references
        assert len(result) == 6
        assert result[0].name == "01_abstract.md"
        assert result[1].name == "02_introduction.md"
        assert result[2].name == "03_methodology.md"
        assert result[3].name == "S01_supplement.md"
        assert result[4].name == "98_glossary.md"
        assert result[5].name == "99_references.md"

    def test_discover_other_files(self, tmp_path):
        """Test discovery of other markdown files."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        (manuscript_dir / "01_abstract.md").write_text("# Abstract")
        (manuscript_dir / "custom_section.md").write_text("# Custom")
        (manuscript_dir / "another_file.md").write_text("# Another")

        result = discover_manuscript_files(manuscript_dir)

        # Should include all non-excluded markdown files
        assert len(result) == 3
        assert result[0].name == "01_abstract.md"
        # Other files should come after main sections but before references
        other_files = [f.name for f in result[1:]]
        assert "custom_section.md" in other_files
        assert "another_file.md" in other_files

    def test_discover_numeric_prefix_ordering(self, tmp_path):
        """Test that files with numeric prefixes are properly ordered."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        # Create files with various numeric prefixes
        (manuscript_dir / "10_appendix.md").write_text("# Appendix")
        (manuscript_dir / "01_abstract.md").write_text("# Abstract")
        (manuscript_dir / "20_conclusion.md").write_text("# Conclusion")

        result = discover_manuscript_files(manuscript_dir)

        # Should be sorted by stem (string sort)
        assert result[0].name == "01_abstract.md"
        assert result[1].name == "10_appendix.md"
        assert result[2].name == "20_conclusion.md"

    def test_discover_multiple_references(self, tmp_path):
        """Test discovery when multiple reference files exist."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        (manuscript_dir / "01_abstract.md").write_text("# Abstract")
        (manuscript_dir / "99_references.md").write_text("# References")
        (manuscript_dir / "99_bibliography.md").write_text("# Bibliography")

        result = discover_manuscript_files(manuscript_dir)

        # All reference files should be at the end
        assert result[0].name == "01_abstract.md"
        assert result[-2].name in ["99_references.md", "99_bibliography.md"]
        assert result[-1].name in ["99_references.md", "99_bibliography.md"]
        assert result[-1] != result[-2]

    def test_discover_supplemental_ordering(self, tmp_path):
        """Test that supplemental files are properly ordered."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        (manuscript_dir / "01_abstract.md").write_text("# Abstract")
        (manuscript_dir / "S03_third.md").write_text("# Third")
        (manuscript_dir / "S01_first.md").write_text("# First")
        (manuscript_dir / "S02_second.md").write_text("# Second")

        result = discover_manuscript_files(manuscript_dir)

        # Supplemental should be sorted
        assert result[0].name == "01_abstract.md"
        assert result[1].name == "S01_first.md"
        assert result[2].name == "S02_second.md"
        assert result[3].name == "S03_third.md"

    def test_discover_only_latex_files(self, tmp_path):
        """Test discovery when only LaTeX files exist."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        (manuscript_dir / "main.tex").write_text("\\documentclass{article}")
        (manuscript_dir / "preamble.tex").write_text("\\usepackage{amsmath}")

        result = discover_manuscript_files(manuscript_dir)

        # Should return LaTeX files
        assert len(result) == 2
        assert all(f.suffix == ".tex" for f in result)

    def test_discover_mixed_case_exclusions(self, tmp_path):
        """Test that exclusions are case-sensitive."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        (manuscript_dir / "01_abstract.md").write_text("# Abstract")
        # These should NOT be excluded (different case from 'README.md' in exclude list)
        (manuscript_dir / "readme.md").write_text("Readme")
        (manuscript_dir / "agents.md").write_text("Agents")
        # On case-insensitive filesystems, README.MD and readme.md are the same file
        # So we only check that readme.md (different case) is included
        (manuscript_dir / "README.MD").write_text("Readme uppercase")

        result = discover_manuscript_files(manuscript_dir)

        # Should include files with different case (not exact matches to exclude list)
        assert len(result) >= 3
        assert "readme.md" in [f.name for f in result] or "README.MD" in [
            f.name for f in result
        ]
        assert "agents.md" in [f.name for f in result]
        # On case-insensitive filesystems, readme.md and README.MD are the same file
        # so we check that at least one variant is present (not excluded)
        result_names = [f.name for f in result]
        assert any(name.lower() == "readme.md" for name in result_names)
