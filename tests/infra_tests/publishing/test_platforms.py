"""Tests for infrastructure.publishing.platforms module.

Tests arXiv submission preparation (pure file operations).
Network-dependent functions (Zenodo, GitHub) are tested with pytest-httpserver.
"""

from __future__ import annotations

import tarfile
from pathlib import Path


from infrastructure.publishing.models import PublicationMetadata
from infrastructure.publishing.platforms import prepare_arxiv_submission


def _make_metadata(**kwargs) -> PublicationMetadata:
    """Create test PublicationMetadata with defaults."""
    defaults = {
        "title": "Test Paper",
        "authors": ["Smith, J.", "Doe, A."],
        "abstract": "A test abstract.",
        "keywords": ["test", "paper"],
        "license": "CC-BY-4.0",
    }
    defaults.update(kwargs)
    return PublicationMetadata(**defaults)


class TestPrepareArxivSubmission:
    """Tests for prepare_arxiv_submission."""

    def test_basic_submission_creates_tarball(self, tmp_path: Path):
        """Should create a .tar.gz file."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        # Create a .tex file
        (manuscript_dir / "main.tex").write_text("\\documentclass{article}")
        (manuscript_dir / "refs.bib").write_text("@article{test, title={Test}}")

        metadata = _make_metadata()
        result = prepare_arxiv_submission(output_dir, metadata)
        assert result.exists()
        assert result.suffix == ".gz"
        assert "arxiv_submission" in result.name

    def test_tarball_contains_tex_and_bib(self, tmp_path: Path):
        """Tarball should include .tex and .bib files."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        (manuscript_dir / "paper.tex").write_text("\\documentclass{article}")
        (manuscript_dir / "refs.bib").write_text("@article{x, title={X}}")

        metadata = _make_metadata()
        result = prepare_arxiv_submission(output_dir, metadata)

        with tarfile.open(result, "r:gz") as tar:
            names = tar.getnames()
            assert any(n.endswith(".tex") for n in names)
            assert any(n.endswith(".bib") for n in names)

    def test_figures_directory_included(self, tmp_path: Path):
        """figures/ directory should be copied into submission."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        figures_dir = manuscript_dir / "figures"
        figures_dir.mkdir()
        (figures_dir / "fig1.png").write_bytes(b"\x89PNG")

        metadata = _make_metadata()
        result = prepare_arxiv_submission(output_dir, metadata)

        with tarfile.open(result, "r:gz") as tar:
            names = tar.getnames()
            assert any("figures" in n for n in names)

    def test_existing_submission_dir_replaced(self, tmp_path: Path):
        """Pre-existing arxiv_submission dir should be removed first."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        # Create pre-existing submission dir with stale content
        old_dir = output_dir / "arxiv_submission"
        old_dir.mkdir()
        (old_dir / "old_file.txt").write_text("stale")

        metadata = _make_metadata()
        result = prepare_arxiv_submission(output_dir, metadata)
        assert result.exists()
        # Old file should not be in the tarball
        with tarfile.open(result, "r:gz") as tar:
            names = tar.getnames()
            assert not any("old_file" in n for n in names)

    def test_no_manuscript_dir(self, tmp_path: Path):
        """If no manuscript dir exists, tarball should still be created."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        metadata = _make_metadata()
        result = prepare_arxiv_submission(output_dir, metadata)
        assert result.exists()

    def test_non_tex_files_excluded(self, tmp_path: Path):
        """Non-tex/bib/cls/bst files should not be included."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        (manuscript_dir / "main.tex").write_text("\\documentclass{article}")
        (manuscript_dir / "notes.txt").write_text("personal notes")
        (manuscript_dir / "data.csv").write_text("1,2,3")

        metadata = _make_metadata()
        result = prepare_arxiv_submission(output_dir, metadata)

        with tarfile.open(result, "r:gz") as tar:
            names = tar.getnames()
            assert not any(n.endswith(".txt") for n in names)
            assert not any(n.endswith(".csv") for n in names)

    def test_cls_and_bst_files_included(self, tmp_path: Path):
        """Style files (.cls, .bst) should be included."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        (manuscript_dir / "custom.cls").write_text("\\NeedsTeXFormat{LaTeX2e}")
        (manuscript_dir / "style.bst").write_text("FUNCTION {format.names}")

        metadata = _make_metadata()
        result = prepare_arxiv_submission(output_dir, metadata)

        with tarfile.open(result, "r:gz") as tar:
            names = tar.getnames()
            assert any(n.endswith(".cls") for n in names)
            assert any(n.endswith(".bst") for n in names)
