"""Markdown validation: file discovery, symbol collection, and manuscript directory resolution."""

import os
import sys
import pytest
from infrastructure.validation.content.discovery import discover_markdown_files
from infrastructure.validation.content.markdown_validator import (
    collect_symbols,
    find_manuscript_directory,
)
from infrastructure.core.exceptions import NotADirectoryError

# Add infrastructure to path for imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, ROOT)


class TestDiscoverMarkdownFilesTree:
    """Test discover_markdown_files with scope=\"tree\"."""

    def test_finds_and_sorts_markdown_files(self, tmp_path):
        """Test discover_markdown_files finds and sorts markdown files."""
        # Create test markdown files
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "02_second.md").write_text("content")
        (manuscript / "01_first.md").write_text("content")
        (manuscript / "not_md.txt").write_text("content")

        files = discover_markdown_files(manuscript, scope="tree")

        assert len(files) == 2
        assert files[0].name == "01_first.md"
        assert files[1].name == "02_second.md"

    def test_nonexistent_directory_raises(self, tmp_path):
        """Test discover_markdown_files raises on nonexistent directory."""
        with pytest.raises(FileNotFoundError):
            discover_markdown_files(tmp_path / "nonexistent", scope="tree")

    def test_file_instead_of_directory_raises(self, tmp_path):
        """Test discover_markdown_files raises when given a file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        with pytest.raises(NotADirectoryError):
            discover_markdown_files(test_file, scope="tree")

    def test_empty_directory(self, tmp_path):
        """Test discover_markdown_files with empty directory."""
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()

        files = discover_markdown_files(manuscript, scope="tree")

        assert files == []


class TestCollectSymbols:
    """Test collect_symbols function."""

    def test_extracts_labels_and_anchors(self, tmp_path):
        """Test collect_symbols extracts labels and anchors."""
        # Create test markdown files
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test1.md").write_text(
            "\\begin{equation}\\label{eq:test1}\\end{equation}\n# Section {#sec:test1}\n"
        )
        (manuscript / "test2.md").write_text(
            "\\begin{equation}\\label{eq:test2}\\end{equation}\n## Subsection {#subsec:test2}\n"
        )

        labels, anchors = collect_symbols([str(manuscript / "test1.md"), str(manuscript / "test2.md")])

        assert labels == {"eq:test1", "eq:test2"}
        # Explicit ``{#anchor}`` attributes are always valid targets...
        assert {"sec:test1", "subsec:test2"} <= anchors
        # ...and GitHub/MkDocs-slugified plain heading text is now ALSO
        # accepted so that table-of-contents self-links resolve in the
        # rendered doc: ``# Section`` / ``## Subsection`` also contribute
        # ``section`` / ``subsection``.
        assert {"section", "subsection"} <= anchors

    def test_empty_file_list(self):
        """Test collect_symbols with empty file list."""
        labels, anchors = collect_symbols([])

        assert labels == set()
        assert anchors == set()


class TestFindManuscriptDirectory:
    """Test find_manuscript_directory function."""

    def test_finds_project_manuscript(self, tmp_path):
        """Test find_manuscript_directory finds projects/project/manuscript."""
        manuscript = tmp_path / "projects" / "project" / "manuscript"
        manuscript.mkdir(parents=True)

        result = find_manuscript_directory(tmp_path, "project")

        assert result == manuscript

    def test_finds_docs_manuscript(self, tmp_path):
        """A populated docs/manuscript tree is a supported source layout."""
        manuscript = tmp_path / "projects" / "project" / "docs" / "manuscript"
        manuscript.mkdir(parents=True)
        (manuscript / "01_intro.md").write_text("# Intro\n", encoding="utf-8")

        result = find_manuscript_directory(tmp_path, "project")

        assert result == manuscript

    def test_raises_when_not_found(self, tmp_path):
        """Test find_manuscript_directory raises when not found."""
        with pytest.raises(FileNotFoundError):
            find_manuscript_directory(tmp_path, "project")
