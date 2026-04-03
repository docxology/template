"""Tests for infrastructure.publishing.platforms — comprehensive coverage."""

import tarfile

from pytest_httpserver import HTTPServer

from infrastructure.publishing.models import PublicationMetadata
from infrastructure.publishing.platforms import (
    prepare_arxiv_submission,
    create_github_release,
    publish_to_zenodo,
)


def _make_metadata(**overrides):
    defaults = {
        "title": "Test Paper",
        "authors": ["Alice", "Bob"],
        "abstract": "A test abstract.",
        "keywords": ["test", "paper"],
        "license": "CC-BY-4.0",
    }
    defaults.update(overrides)
    return PublicationMetadata(**defaults)


class TestPrepareArxivSubmission:
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

        meta = _make_metadata()
        result = prepare_arxiv_submission(output, meta)
        assert result.exists()
        assert not (sub / "old_file.txt").exists()

    def test_no_manuscript_dir(self, tmp_path):
        output = tmp_path / "output"
        output.mkdir()
        meta = _make_metadata()
        result = prepare_arxiv_submission(output, meta)
        assert result.exists()

    def test_bbl_file_copied(self, tmp_path):
        project = tmp_path / "project"
        output = project / "output"
        pdf_dir = output / "pdf"
        pdf_dir.mkdir(parents=True)
        (pdf_dir / "Test_Paper.bbl").write_text("\\begin{thebibliography}{}")

        meta = _make_metadata()
        result = prepare_arxiv_submission(output, meta)
        assert result.exists()


class TestCreateGithubRelease:
    def test_successful_release(self, httpserver: HTTPServer):
        httpserver.expect_request(
            "/repos/owner/repo/releases", method="POST"
        ).respond_with_json(
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
        httpserver.expect_request(
            "/repos/owner/repo/releases", method="POST"
        ).respond_with_json(
            {
                "id": 1,
                "upload_url": httpserver.url_for("/uploads") + "{?name,label}",
                "html_url": "https://github.com/owner/repo/releases/1",
            }
        )
        httpserver.expect_request("/uploads", method="POST").respond_with_json(
            {"id": 1, "name": "paper.pdf"}
        )

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
        httpserver.expect_request(
            "/repos/owner/repo/releases", method="POST"
        ).respond_with_json(
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
    def test_callable(self):
        assert callable(publish_to_zenodo)
