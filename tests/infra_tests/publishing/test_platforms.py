"""Tests for infrastructure.publishing.platforms module.

Tests arXiv submission preparation (pure file operations).
Network-dependent functions (Zenodo, GitHub) are tested with pytest-httpserver.
"""

from __future__ import annotations

import tarfile
from pathlib import Path

import pytest
from pytest_httpserver import HTTPServer

from infrastructure.core.exceptions import PublishingError
from infrastructure.publishing.models import PublicationMetadata
from infrastructure.publishing.platforms import (
    create_github_release,
    prepare_arxiv_submission,
    publish_to_zenodo,
)


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
        (manuscript_dir / "main.tex").write_text(r"\includegraphics{figures/fig1.png}")
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
        (manuscript_dir / "main.tex").write_text(r"\documentclass{article}")

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

    def test_no_manuscript_dir_fails_closed(self, tmp_path: Path):
        """A source-free request must not masquerade as an uploadable package."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        stale = output_dir / "arxiv_submission_19990101.tar.gz"
        stale.write_bytes(b"stale")

        metadata = _make_metadata()
        with pytest.raises(PublishingError, match="No LaTeX root found"):
            prepare_arxiv_submission(output_dir, metadata)
        assert not stale.exists()
        assert not (output_dir / "arxiv_submission").exists()

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
        (manuscript_dir / "main.tex").write_text(r"\documentclass{custom}")
        (manuscript_dir / "custom.cls").write_text("\\NeedsTeXFormat{LaTeX2e}")
        (manuscript_dir / "style.bst").write_text("FUNCTION {format.names}")

        metadata = _make_metadata()
        result = prepare_arxiv_submission(output_dir, metadata)

        with tarfile.open(result, "r:gz") as tar:
            names = tar.getnames()
            assert any(n.endswith(".cls") for n in names)
            assert any(n.endswith(".bst") for n in names)

    def test_rendered_tex_from_output_included(self, tmp_path: Path):
        """A .tex rendered under output/ (Markdown manuscripts) is picked up into the tarball."""
        output_dir = tmp_path / "output"
        (output_dir / "pdf").mkdir(parents=True)
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        # Markdown-only manuscript: no .tex in manuscript/, only a rendered one under output/pdf/.
        (manuscript_dir / "01_intro.md").write_text("# Intro")
        (manuscript_dir / "references.bib").write_text("@article{x, title={X}}")
        (output_dir / "pdf" / "Test_Paper.tex").write_text("\\documentclass{article}")

        metadata = _make_metadata()
        result = prepare_arxiv_submission(output_dir, metadata)

        with tarfile.open(result, "r:gz") as tar:
            names = tar.getnames()
        assert any(n.endswith("Test_Paper.tex") for n in names)
        assert any(n.endswith("references.bib") for n in names)

    def test_markdown_only_manuscript_fails_closed(self, tmp_path: Path):
        """References without a TeX root are not emitted as a submission."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        (manuscript_dir / "01_intro.md").write_text("# Intro")
        (manuscript_dir / "references.bib").write_text("@article{x, title={X}}")

        metadata = _make_metadata()
        with pytest.raises(PublishingError, match="No LaTeX root found"):
            prepare_arxiv_submission(output_dir, metadata)
        assert not list(output_dir.glob("arxiv_submission_*.tar.gz"))

    def test_canonical_rendered_tree_includes_matching_bbl_references_and_figures(self, tmp_path: Path):
        """Renderer-owned names and paths become one compilable arXiv root."""
        output_dir = tmp_path / "output"
        pdf_dir = output_dir / "pdf"
        figures_dir = output_dir / "figures"
        manuscript_dir = tmp_path / "manuscript"
        pdf_dir.mkdir(parents=True)
        figures_dir.mkdir()
        manuscript_dir.mkdir()
        rendered_tex = "\\includegraphics{../figures/result.png}\n\\bibliography{references}\n"
        (pdf_dir / "_combined_manuscript.tex").write_text(rendered_tex)
        (pdf_dir / "_combined_manuscript.bbl").write_text(r"\begin{thebibliography}{1}")
        (pdf_dir / "references.bib").write_text("@article{x, title={X}}")
        (pdf_dir / "Test_Paper.bbl").write_text("wrong title-derived companion")
        (figures_dir / "result.png").write_bytes(b"PNG")
        (figures_dir / "runtime.json").write_text("{}")
        (figures_dir / "animation.gif").write_bytes(b"GIF")

        result = prepare_arxiv_submission(output_dir, _make_metadata())

        with tarfile.open(result, "r:gz") as tar:
            names = tar.getnames()
            packaged_tex = tar.extractfile("_combined_manuscript.tex")
            assert packaged_tex is not None
            tex_text = packaged_tex.read().decode("utf-8")
        assert names == sorted(names)
        assert "_combined_manuscript.tex" in names
        assert "_combined_manuscript.bbl" in names
        assert "references.bib" in names
        assert "figures/result.png" in names
        assert "figures/runtime.json" not in names
        assert "figures/animation.gif" not in names
        assert "Test_Paper.bbl" not in names
        assert r"\includegraphics{figures/result.png}" in tex_text

    def test_canonical_rendered_root_excludes_other_stale_tex(self, tmp_path: Path):
        """A stale output TeX file cannot collide with the canonical renderer root."""
        output_dir = tmp_path / "output"
        pdf_dir = output_dir / "pdf"
        pdf_dir.mkdir(parents=True)
        (pdf_dir / "_combined_manuscript.tex").write_text(r"\documentclass{article}")
        (pdf_dir / "stale.tex").write_text(r"\documentclass{book}")

        result = prepare_arxiv_submission(output_dir, _make_metadata())

        with tarfile.open(result, "r:gz") as tar:
            names = tar.getnames()
        assert "_combined_manuscript.tex" in names
        assert "stale.tex" not in names

    def test_ambiguous_noncanonical_rendered_roots_fail(self, tmp_path: Path):
        output_dir = tmp_path / "output"
        pdf_dir = output_dir / "pdf"
        pdf_dir.mkdir(parents=True)
        (pdf_dir / "one.tex").write_text(r"\documentclass{article}")
        (pdf_dir / "two.tex").write_text(r"\documentclass{article}")

        with pytest.raises(PublishingError, match="Multiple rendered TeX roots"):
            prepare_arxiv_submission(output_dir, _make_metadata())
        assert not list(output_dir.glob("arxiv_submission_*.tar.gz"))

    def test_manuscript_relative_paths_do_not_flatten_or_collide(self, tmp_path: Path):
        output_dir = tmp_path / "output"
        manuscript_dir = tmp_path / "manuscript"
        output_dir.mkdir()
        (manuscript_dir / "chapters").mkdir(parents=True)
        (manuscript_dir / "main.tex").write_text(r"\input{chapters/main}")
        (manuscript_dir / "chapters" / "main.tex").write_text("chapter")

        result = prepare_arxiv_submission(output_dir, _make_metadata())

        with tarfile.open(result, "r:gz") as tar:
            assert tar.getnames() == ["chapters/main.tex", "main.tex"]

    def test_source_date_epoch_makes_name_and_bytes_stable(self, tmp_path: Path, monkeypatch) -> None:
        output_dir = tmp_path / "output"
        manuscript_dir = tmp_path / "manuscript"
        output_dir.mkdir()
        manuscript_dir.mkdir()
        source = manuscript_dir / "main.tex"
        source.write_text(r"\documentclass{article}")
        epoch = 1_704_067_200  # 2024-01-01T00:00:00Z
        monkeypatch.setenv("SOURCE_DATE_EPOCH", str(epoch))

        first = prepare_arxiv_submission(output_dir, _make_metadata())
        first_bytes = first.read_bytes()
        source.touch()
        second = prepare_arxiv_submission(output_dir, _make_metadata())

        assert first.name == "arxiv_submission_20240101.tar.gz"
        assert second == first
        assert second.read_bytes() == first_bytes
        with tarfile.open(second, "r:gz") as tar:
            members = tar.getmembers()
        assert [member.name for member in members] == sorted(member.name for member in members)
        assert all(member.mtime == epoch for member in members)
        assert all((member.uid, member.gid, member.uname, member.gname) == (0, 0, "", "") for member in members)

    def test_old_date_named_archives_are_removed(self, tmp_path: Path, monkeypatch) -> None:
        output_dir = tmp_path / "output"
        manuscript_dir = tmp_path / "manuscript"
        output_dir.mkdir()
        manuscript_dir.mkdir()
        (manuscript_dir / "main.tex").write_text(r"\documentclass{article}")
        (output_dir / "arxiv_submission_19990101.tar.gz").write_bytes(b"old")
        (output_dir / "arxiv_submission_20000101.tar.gz").write_bytes(b"old")
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "1704067200")

        result = prepare_arxiv_submission(output_dir, _make_metadata())

        assert list(output_dir.glob("arxiv_submission_*.tar.gz")) == [result]

    @pytest.mark.parametrize("invalid_epoch", ["", "   ", "not-an-epoch", "-1"])
    def test_invalid_source_date_epoch_fails_closed(
        self,
        tmp_path: Path,
        monkeypatch,
        invalid_epoch: str,
    ) -> None:
        output_dir = tmp_path / "output"
        manuscript_dir = tmp_path / "manuscript"
        output_dir.mkdir()
        manuscript_dir.mkdir()
        (manuscript_dir / "main.tex").write_text(r"\documentclass{article}")
        monkeypatch.setenv("SOURCE_DATE_EPOCH", invalid_epoch)

        with pytest.raises(PublishingError, match="SOURCE_DATE_EPOCH must be a non-negative integer"):
            prepare_arxiv_submission(output_dir, _make_metadata())

        assert not list(output_dir.glob("arxiv_submission_*.tar.gz"))
        assert not (output_dir / "arxiv_submission").exists()


class TestPrepareArxivSubmissionFromPlatforms:
    def test_basic_submission(self, tmp_path):
        project = tmp_path / "project"
        output = project / "output"
        manuscript = project / "manuscript"
        output.mkdir(parents=True)
        manuscript.mkdir()

        (manuscript / "main.tex").write_text(r"\documentclass{article}")
        (manuscript / "references.bib").write_text("@article{test,}")
        (manuscript / "notes.md").write_text("# Notes")

        figs = manuscript / "figures"
        figs.mkdir()
        (figs / "plot.png").write_bytes(b"fake png")

        meta = _make_metadata()
        result = prepare_arxiv_submission(output, meta)
        assert result.exists()
        assert result.name.startswith("arxiv_submission_")
        assert result.name.endswith(".tar.gz")

        with tarfile.open(result, "r:gz") as tar:
            names = tar.getnames()
            assert any("main.tex" in n for n in names)
            assert any("references.bib" in n for n in names)
            assert not any("notes.md" in n for n in names)

    def test_cleans_existing_dir(self, tmp_path):
        project = tmp_path / "project"
        output = project / "output"
        output.mkdir(parents=True)
        sub = output / "arxiv_submission"
        sub.mkdir()
        (sub / "old_file.txt").write_text("old")
        manuscript = project / "manuscript"
        manuscript.mkdir()
        (manuscript / "main.tex").write_text(r"\documentclass{article}")

        meta = _make_metadata()
        result = prepare_arxiv_submission(output, meta)
        assert result.exists()
        assert not (sub / "old_file.txt").exists()

    def test_no_manuscript_dir(self, tmp_path):
        output = tmp_path / "output"
        output.mkdir()
        meta = _make_metadata()
        with pytest.raises(PublishingError, match="No LaTeX root found"):
            prepare_arxiv_submission(output, meta)

    def test_bbl_file_copied(self, tmp_path):
        project = tmp_path / "project"
        output = project / "output"
        pdf_dir = output / "pdf"
        pdf_dir.mkdir(parents=True)
        (pdf_dir / "_combined_manuscript.tex").write_text(r"\documentclass{article}")
        (pdf_dir / "_combined_manuscript.bbl").write_text("\\begin{thebibliography}{}")

        meta = _make_metadata()
        result = prepare_arxiv_submission(output, meta)
        assert result.exists()
        with tarfile.open(result, "r:gz") as tar:
            assert "_combined_manuscript.bbl" in tar.getnames()


class TestCreateGithubRelease:
    def test_successful_release(self, httpserver: HTTPServer):
        httpserver.expect_request("/repos/owner/repo/releases", method="POST").respond_with_json(
            {
                "id": 1,
                "upload_url": httpserver.url_for("/uploads{?name,label}"),
                "html_url": "https://github.com/owner/repo/releases/1",
            }
        )

        result = create_github_release(
            tag_name="v1.0",
            release_name="Release 1.0",
            description="First release",
            assets=[],
            token="fake-token",
            repo="owner/repo",
            base_url=httpserver.url_for(""),
        )
        assert "github.com" in result

    def test_with_assets(self, httpserver: HTTPServer, tmp_path):
        httpserver.expect_request("/repos/owner/repo/releases", method="POST").respond_with_json(
            {
                "id": 1,
                "upload_url": httpserver.url_for("/uploads") + "{?name,label}",
                "html_url": "https://github.com/owner/repo/releases/1",
            }
        )
        httpserver.expect_request("/uploads", method="POST").respond_with_json({"id": 1, "name": "paper.pdf"})

        asset = tmp_path / "paper.pdf"
        asset.write_bytes(b"fake pdf content")

        result = create_github_release(
            tag_name="v1.0",
            release_name="Release 1.0",
            description="Test",
            assets=[asset],
            token="fake-token",
            repo="owner/repo",
            base_url=httpserver.url_for(""),
        )
        assert result == "https://github.com/owner/repo/releases/1"

    def test_missing_asset_skipped(self, httpserver: HTTPServer, tmp_path):
        httpserver.expect_request("/repos/owner/repo/releases", method="POST").respond_with_json(
            {
                "id": 1,
                "upload_url": httpserver.url_for("/uploads") + "{?name}",
                "html_url": "https://github.com/owner/repo/releases/1",
            }
        )

        missing = tmp_path / "nonexistent.pdf"
        result = create_github_release(
            tag_name="v1.0",
            release_name="Release",
            description="Test",
            assets=[missing],
            token="fake-token",
            repo="owner/repo",
            base_url=httpserver.url_for(""),
        )
        assert "github.com" in result


class TestPublishToZenodo:
    def test_end_to_end_via_platforms_shim(
        self,
        tmp_path: Path,
        zenodo_test_server,
    ) -> None:
        paper = tmp_path / "paper.pdf"
        paper.write_bytes(b"%PDF")

        metadata = _make_metadata()
        doi = publish_to_zenodo(
            metadata,
            [paper],
            access_token="test-token",
            sandbox=True,
            base_url=zenodo_test_server.url_for(""),
        )
        assert doi.doi == "10.5281/zenodo.12345"


class TestCreateGithubReleaseImportGuard:
    def test_requires_requests_package(self) -> None:
        with pytest.raises(PublishingError, match="requests package is required"):
            create_github_release(
                tag_name="v1.0",
                release_name="Release",
                description="Test",
                assets=[],
                token="token",
                repo="owner/repo",
                requests_available=False,
            )

    def test_http_failure_raises_publishing_error(self, httpserver: HTTPServer) -> None:
        httpserver.expect_request("/repos/owner/repo/releases", method="POST").respond_with_data(
            "error",
            status=500,
        )
        with pytest.raises(PublishingError, match="GitHub release failed"):
            create_github_release(
                tag_name="v1.0",
                release_name="Release",
                description="Test",
                assets=[],
                token="token",
                repo="owner/repo",
                base_url=httpserver.url_for(""),
            )
