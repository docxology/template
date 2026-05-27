"""Tests for unified release workflow and config/metadata helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from infrastructure.core.exceptions import MetadataError, PublishingError
from infrastructure.publishing.config_doi import read_publication_doi, update_publication_doi
from infrastructure.publishing.metadata_from_config import (
    load_publication_release_context,
    publication_metadata_from_config,
)
from infrastructure.publishing import release_workflow as release_workflow_module
from infrastructure.publishing.release_workflow import (
    ReleaseRequest,
    prepare_release_bundle,
    resolve_combined_pdf,
    run_release_workflow,
    validate_release_tag,
)


def _write_minimal_project(
    repo_root: Path,
    project_name: str = "test_release",
    *,
    doi: str | None = None,
    transmission_bookends: bool = False,
) -> Path:
    manuscript = repo_root / "projects" / project_name / "manuscript"
    manuscript.mkdir(parents=True, exist_ok=True)
    (manuscript / "00_abstract.md").write_text("# Abstract\n\nTest abstract for release workflow.\n", encoding="utf-8")

    doi_line = f'  doi: "{doi}"\n' if doi else ""
    bookend_block = ""
    if transmission_bookends:
        bookend_block = """
  transmission_bookends:
    enabled: true
    max_prior_releases: 3
"""
    config = f"""paper:
  title: "Release Test Paper"
  version: "1.0"

authors:
  - name: "Test Author"
    email: "test@example.com"

publication:
{doi_line}  journal: "Zenodo"
{bookend_block}
keywords:
  - "testing"

metadata:
  license: "CC-BY-4.0"
"""
    config_path = manuscript / "config.yaml"
    config_path.write_text(config, encoding="utf-8")

    pdf_dir = repo_root / "output" / project_name / "pdf"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = pdf_dir / f"{project_name}_combined.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 release test")
    return config_path


class TestConfigDoi:
    def test_update_and_read_round_trip(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            "paper:\n  title: T\npublication:\n  journal: Zenodo\n",
            encoding="utf-8",
        )
        assert update_publication_doi(config_path, "10.5281/zenodo.99999") is True
        assert read_publication_doi(config_path) == "10.5281/zenodo.99999"
        assert update_publication_doi(config_path, "10.5281/zenodo.99999") is False

    def test_preserves_inline_comments_on_replace(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.yaml"
        original = (
            "publication:\n"
            '  doi: "10.5281/zenodo.11111"  # checked by gates\n'
        )
        config_path.write_text(original, encoding="utf-8")
        update_publication_doi(config_path, "10.5281/zenodo.22222")
        text = config_path.read_text(encoding="utf-8")
        assert 'doi: "10.5281/zenodo.22222"' in text
        assert "# checked by gates" in text
        assert read_publication_doi(config_path) == "10.5281/zenodo.22222"

    def test_preserves_header_comments(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.yaml"
        original = (
            "# header comment\n"
            "paper:\n  title: T\n"
            "publication:\n"
            '  doi: "10.5281/zenodo.11111"  # existing\n'
        )
        config_path.write_text(original, encoding="utf-8")
        update_publication_doi(config_path, "10.5281/zenodo.22222")
        text = config_path.read_text(encoding="utf-8")
        assert "# header comment" in text
        assert 'doi: "10.5281/zenodo.22222"' in text
        assert "# existing" in text

    def test_invalid_doi_raises(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.yaml"
        config_path.write_text("publication:\n  journal: x\n", encoding="utf-8")
        with pytest.raises(MetadataError):
            update_publication_doi(config_path, "not-a-doi")


class TestMetadataFromConfig:
    def test_loads_from_config_and_abstract(self, tmp_path: Path) -> None:
        config_path = _write_minimal_project(tmp_path)
        metadata = publication_metadata_from_config(config_path)
        assert metadata.title == "Release Test Paper"
        assert metadata.authors == ["Test Author"]
        assert "Test abstract" in metadata.abstract
        assert "testing" in metadata.keywords

    def test_requires_abstract_by_default(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        config_path = manuscript / "config.yaml"
        config_path.write_text(
            "paper:\n  title: T\nauthors:\n  - name: A\nkeywords: []\n",
            encoding="utf-8",
        )
        with pytest.raises(MetadataError):
            publication_metadata_from_config(config_path)

    def test_load_publication_release_context_single_parse(self, tmp_path: Path) -> None:
        config_path = _write_minimal_project(tmp_path, doi="10.5281/zenodo.11111")
        context = load_publication_release_context(config_path)
        assert context.metadata.title == "Release Test Paper"
        assert context.prior_doi == "10.5281/zenodo.11111"
        assert isinstance(context.deposit_context.authors_config, list)


class TestReleaseWorkflow:
    def test_resolve_combined_pdf_prefers_output_tree(self, tmp_path: Path) -> None:
        _write_minimal_project(tmp_path)
        found = resolve_combined_pdf(tmp_path, "test_release")
        assert found is not None
        assert found.name == "test_release_combined.pdf"

    def test_validate_release_tag_rejects_spaces(self) -> None:
        with pytest.raises(PublishingError):
            validate_release_tag("bad tag")

    def test_dry_run_writes_receipt_without_network(self, tmp_path: Path) -> None:
        _write_minimal_project(tmp_path)
        request = ReleaseRequest(
            repo_root=tmp_path,
            project_name="test_release",
            tag="v1.0.0",
            github_repo="testuser/testrepo",
            dry_run=True,
            allow_draft_abstract=False,
        )
        result = run_release_workflow(request, render_fn=lambda _r, _p: 0)
        assert result.receipt_path.exists()
        assert result.dry_run is True
        payload = json.loads(result.receipt_path.read_text(encoding="utf-8"))
        assert payload["dry_run"] is True
        assert payload["tag"] == "v1.0.0"
        assert payload["pdf_sha256"]
        assert result.pdf_sha256 == payload["pdf_sha256"]

    def test_prepare_release_bundle_includes_deposit_metadata(self, tmp_path: Path) -> None:
        _write_minimal_project(tmp_path)
        request = ReleaseRequest(
            repo_root=tmp_path,
            project_name="test_release",
            tag="v1.0.0",
            github_repo="testuser/testrepo",
        )
        bundle = prepare_release_bundle(request)
        assert bundle.pdf_sha256
        assert bundle.pdf_path.name != "test_release_combined.pdf"
        assert bundle.pdf_path.name.endswith(".pdf")
        metadata_payload = json.loads(
            (bundle.bundle_dir / "publication_metadata.json").read_text(encoding="utf-8")
        )
        assert metadata_payload["pdf_sha256"] == bundle.pdf_sha256
        assert metadata_payload["deposit_description"]
        assert "PDF SHA-256:" in metadata_payload["deposit_description"]
        manifest = json.loads((bundle.bundle_dir / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["pdf_sha256"] == bundle.pdf_sha256
        assert manifest["deposit_filename"] == bundle.pdf_path.name
        assert manifest["source_pdf_name"] == "test_release_combined.pdf"

    def test_full_workflow_with_http_servers(
        self,
        tmp_path: Path,
        zenodo_release_test_server,
        github_test_server,
        monkeypatch,
    ) -> None:
        _write_minimal_project(tmp_path)
        render_calls: list[str] = []
        stage_order: list[str] = []

        def fake_render(_repo_root: Path, project_name: str) -> int:
            render_calls.append(project_name)
            return 0

        original_zenodo = release_workflow_module.run_zenodo_publish
        original_github = release_workflow_module.run_github_release

        def track_zenodo(*args, **kwargs):
            stage_order.append("zenodo")
            return original_zenodo(*args, **kwargs)

        def track_github(*args, **kwargs):
            stage_order.append("github")
            return original_github(*args, **kwargs)

        monkeypatch.setattr(release_workflow_module, "run_zenodo_publish", track_zenodo)
        monkeypatch.setattr(release_workflow_module, "run_github_release", track_github)

        request = ReleaseRequest(
            repo_root=tmp_path,
            project_name="test_release",
            tag="v1.0.0",
            github_repo="testuser/testrepo",
            github_token="gh-test",
            zenodo_token="zen-test",
            github_api_base_url=github_test_server.url_for(""),
            zenodo_base_url=zenodo_release_test_server.url_for(""),
            allow_draft_abstract=False,
        )
        result = run_release_workflow(request, render_fn=fake_render)
        assert stage_order == ["zenodo", "github"]
        assert result.github_release_url is not None
        assert result.doi == "10.5281/zenodo.12345"
        assert result.config_updated is True
        assert result.pdf_sha256
        assert read_publication_doi(
            tmp_path / "projects" / "test_release" / "manuscript" / "config.yaml"
        ) == "10.5281/zenodo.12345"
        assert render_calls == ["test_release"]
        assert (result.bundle_dir / "manifest.json").exists()
        receipt = json.loads(result.receipt_path.read_text(encoding="utf-8"))
        assert receipt["pdf_sha256"] == result.pdf_sha256

        metadata_payload = json.loads(
            (result.bundle_dir / "publication_metadata.json").read_text(encoding="utf-8")
        )
        deposit_description = metadata_payload["deposit_description"]
        assert result.doi in deposit_description
        assert result.pdf_sha256 in deposit_description

        from infrastructure.publishing.abstract_plaintext import build_github_release_body

        expected_body = build_github_release_body(
            project_name=request.project_name,
            tag=request.tag,
            abstract_plaintext=metadata_payload["abstract"],
            doi=result.doi,
            pdf_sha256=result.pdf_sha256,
            zenodo_record_url=f"https://zenodo.org/records/{result.doi.rsplit('.', 1)[-1]}",
            github_release_url=f"https://github.com/{request.github_repo}/releases/tag/{request.tag}",
            version="1.0",
        )
        assert result.doi in expected_body
        assert result.pdf_sha256 in expected_body

    def test_transmission_bookends_updated_on_dry_run(self, tmp_path: Path) -> None:
        _write_minimal_project(tmp_path, transmission_bookends=True)
        request = ReleaseRequest(
            repo_root=tmp_path,
            project_name="test_release",
            tag="v1.0.0",
            github_repo="testuser/testrepo",
            dry_run=True,
        )
        result = run_release_workflow(request, render_fn=lambda _r, _p: 0)
        project_root = tmp_path / "projects" / "test_release"
        ledger_path = project_root / "output" / "data" / "publication_ledger.json"
        assert ledger_path.is_file()
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        assert len(ledger["releases"]) == 1
        begin_path = project_root / "output" / "manuscript" / "00_00_transmission_begin.md"
        end_path = project_root / "output" / "manuscript" / "99_zz_transmission_end.md"
        assert begin_path.is_file()
        assert end_path.is_file()
        assert result.receipt_path.is_file()

    def test_new_version_branch(
        self,
        tmp_path: Path,
        zenodo_version_test_server,
        github_test_server,
    ) -> None:
        _write_minimal_project(tmp_path, doi="10.5281/zenodo.11111")
        request = ReleaseRequest(
            repo_root=tmp_path,
            project_name="test_release",
            tag="v2.0.0",
            github_repo="testuser/testrepo",
            github_token="gh-test",
            zenodo_token="zen-test",
            skip_github=True,
            github_api_base_url=github_test_server.url_for(""),
            zenodo_base_url=zenodo_version_test_server.url_for(""),
            allow_draft_abstract=False,
        )
        result = run_release_workflow(request, render_fn=lambda _r, _p: 0)
        assert result.doi == "10.5281/zenodo.54321"

    def test_prepare_release_bundle_missing_pdf(self, tmp_path: Path) -> None:
        request = ReleaseRequest(
            repo_root=tmp_path,
            project_name="missing",
            tag="v1.0.0",
            github_repo="a/b",
        )
        with pytest.raises(PublishingError, match="Combined PDF not found"):
            prepare_release_bundle(request)
