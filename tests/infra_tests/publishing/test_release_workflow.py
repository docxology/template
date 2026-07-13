"""Tests for unified release workflow and config/metadata helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from infrastructure.core.exceptions import MetadataError, PublishingError
from infrastructure.publishing.config_doi import (
    read_publication_doi,
    read_publication_version_doi,
    update_publication_after_zenodo_deposit,
    update_publication_doi,
    uses_split_zenodo_doi_fields,
)
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
        original = 'publication:\n  doi: "10.5281/zenodo.11111"  # checked by gates\n'
        config_path.write_text(original, encoding="utf-8")
        update_publication_doi(config_path, "10.5281/zenodo.22222")
        text = config_path.read_text(encoding="utf-8")
        assert 'doi: "10.5281/zenodo.22222"' in text
        assert "# checked by gates" in text
        assert read_publication_doi(config_path) == "10.5281/zenodo.22222"

    def test_preserves_header_comments(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.yaml"
        original = '# header comment\npaper:\n  title: T\npublication:\n  doi: "10.5281/zenodo.11111"  # existing\n'
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

    def test_split_zenodo_fields_keep_concept_doi(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            "publication:\n"
            '  doi: "10.5281/zenodo.11111"\n'
            '  version_doi: "10.5281/zenodo.22222"\n'
            '  version_record: "https://zenodo.org/records/22222"\n',
            encoding="utf-8",
        )
        assert uses_split_zenodo_doi_fields(config_path) is True
        assert read_publication_doi(config_path) == "10.5281/zenodo.11111"
        assert read_publication_version_doi(config_path) == "10.5281/zenodo.22222"
        assert update_publication_after_zenodo_deposit(config_path, "10.5281/zenodo.33333") is True
        text = config_path.read_text(encoding="utf-8")
        assert 'doi: "10.5281/zenodo.11111"' in text
        assert 'version_doi: "10.5281/zenodo.33333"' in text
        assert 'version_record: "https://zenodo.org/records/33333"' in text
        assert read_publication_doi(config_path) == "10.5281/zenodo.11111"
        assert read_publication_version_doi(config_path) == "10.5281/zenodo.33333"


class TestMetadataFromConfig:
    def test_loads_from_config_and_abstract(self, tmp_path: Path) -> None:
        config_path = _write_minimal_project(tmp_path)
        metadata = publication_metadata_from_config(config_path)
        assert metadata.title == "Release Test Paper"
        assert metadata.authors == ["Test Author"]
        assert "Test abstract" in metadata.abstract
        assert "testing" in metadata.keywords

    def test_loads_hydrated_abstract_from_config(self, tmp_path: Path) -> None:
        config_path = _write_minimal_project(tmp_path)
        abstract_path = config_path.parent / "00_abstract.md"
        abstract_path.write_text(
            "# Abstract\n\nThis release binds {{track_count}} tracks.\n",
            encoding="utf-8",
        )
        variables_path = tmp_path / "projects" / "test_release" / "output" / "data" / "manuscript_variables.json"
        variables_path.parent.mkdir(parents=True)
        variables_path.write_text(json.dumps({"track_count": 7}), encoding="utf-8")

        metadata = publication_metadata_from_config(config_path)

        assert "7 tracks" in metadata.abstract
        assert "{{" not in metadata.abstract

    def test_prefers_output_abstract_from_config(self, tmp_path: Path) -> None:
        config_path = _write_minimal_project(tmp_path)
        source_abstract = config_path.parent / "00_abstract.md"
        source_abstract.write_text("# Abstract\n\nSource {{track_count}} tracks.\n", encoding="utf-8")
        output_abstract = tmp_path / "projects" / "test_release" / "output" / "manuscript" / "00_abstract.md"
        output_abstract.parent.mkdir(parents=True)
        output_abstract.write_text("# Abstract\n\nHydrated 7 tracks.\n", encoding="utf-8")

        metadata = publication_metadata_from_config(config_path)

        assert "Hydrated 7 tracks" in metadata.abstract
        assert "{{" not in metadata.abstract

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

    def test_resolve_combined_pdf_supports_qualified_project_name(self, tmp_path: Path) -> None:
        qualified = "templates/template_sia"
        pdf_dir = tmp_path / "output" / qualified / "pdf"
        pdf_dir.mkdir(parents=True)
        pdf_path = pdf_dir / "template_sia_combined.pdf"
        pdf_path.write_bytes(b"%PDF-1.4")
        found = resolve_combined_pdf(tmp_path, qualified)
        assert found == pdf_path

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
        metadata_payload = json.loads((bundle.bundle_dir / "publication_metadata.json").read_text(encoding="utf-8"))
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

        original_zenodo = release_workflow_module.publish_zenodo_for_release
        original_github = release_workflow_module.run_github_release

        def track_zenodo(*args, **kwargs):
            stage_order.append("zenodo")
            return original_zenodo(*args, **kwargs)

        def track_github(*args, **kwargs):
            stage_order.append("github")
            return original_github(*args, **kwargs)

        monkeypatch.setattr(release_workflow_module, "publish_zenodo_for_release", track_zenodo)
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
        assert (
            read_publication_doi(tmp_path / "projects" / "test_release" / "manuscript" / "config.yaml")
            == "10.5281/zenodo.12345"
        )
        assert render_calls == ["test_release"]
        assert (result.bundle_dir / "manifest.json").exists()
        receipt = json.loads(result.receipt_path.read_text(encoding="utf-8"))
        assert receipt["pdf_sha256"] == result.pdf_sha256

        metadata_payload = json.loads((result.bundle_dir / "publication_metadata.json").read_text(encoding="utf-8"))
        deposit_description = metadata_payload["deposit_description"]
        assert result.doi in deposit_description
        assert result.pdf_sha256 in deposit_description

        from infrastructure.publishing.abstract_plaintext import (
            build_github_release_body,
        )

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

    def test_reserve_doi_first_rerenders_before_upload(
        self,
        tmp_path: Path,
    ) -> None:
        """Reserve-first flow against a real HTTP Zenodo stand-in (no mocks).

        Proves the ordering property end-to-end: the deposition is created
        (reserving the version DOI), the manuscript is re-rendered with that
        DOI baked in, and only then are the bytes uploaded to the bucket.
        """
        import re as _re

        from pytest_httpserver import HTTPServer
        from werkzeug.wrappers import Response

        config_path = _write_minimal_project(tmp_path)
        render_calls: list[str] = []
        upload_seen: list[bytes] = []

        server = HTTPServer()
        server.start()
        try:
            base = server.url_for("")

            # Reserve: create deposition with a pre-reserved version DOI.
            server.expect_request("/deposit/depositions", method="POST").respond_with_json(
                {
                    "id": 22222,
                    "conceptrecid": "11111",
                    "links": {"bucket": f"{base}/files/bucket222"},
                    "metadata": {"prereserve_doi": {"doi": "10.5281/zenodo.22222"}},
                }
            )
            # Draft metadata update + best-effort post-publish description patch.
            server.expect_request("/deposit/depositions/22222", method="PUT").respond_with_json(
                {"id": 22222, "metadata": {"title": "Updated"}}
            )

            # Bucket upload: capture the actual uploaded bytes.
            def _capture_upload(request):
                upload_seen.append(request.get_data())
                return Response(json.dumps({"key": "uploaded"}), status=201, content_type="application/json")

            server.expect_request(
                _re.compile(r"/files/bucket222/.+"),
                method="PUT",
            ).respond_with_handler(_capture_upload)

            server.expect_request(
                "/deposit/depositions/22222/actions/publish",
                method="POST",
            ).respond_with_json(
                {
                    "id": 22222,
                    "doi": "10.5281/zenodo.22222",
                    "conceptdoi": "10.5281/zenodo.11111",
                    "state": "done",
                }
            )

            def fake_render(repo_root: Path, project_name: str) -> int:
                render_calls.append(project_name)
                pdf_path = repo_root / "output" / project_name / "pdf" / f"{project_name}_combined.pdf"
                pdf_path.write_bytes(b"%PDF DOI 10.5281/zenodo.22222")
                return 0

            request = ReleaseRequest(
                repo_root=tmp_path,
                project_name="test_release",
                tag="v1.0.0",
                github_repo="testuser/testrepo",
                zenodo_token="zen-test",
                skip_github=True,
                reserve_doi_first=True,
                zenodo_base_url=base,
            )
            result = run_release_workflow(request, render_fn=fake_render)
        finally:
            server.stop()

        assert render_calls == ["test_release"]
        assert upload_seen, "no bytes were uploaded to the Zenodo bucket"
        # The re-rendered PDF (containing the reserved DOI) is what got uploaded.
        assert any(b"10.5281/zenodo.22222" in payload for payload in upload_seen)
        assert result.doi == "10.5281/zenodo.22222"
        assert result.concept_doi == "10.5281/zenodo.11111"
        assert result.version_doi == "10.5281/zenodo.22222"
        assert read_publication_doi(config_path) == "10.5281/zenodo.11111"
        assert read_publication_version_doi(config_path) == ("10.5281/zenodo.22222")

    def test_prepare_release_bundle_missing_pdf(self, tmp_path: Path) -> None:
        request = ReleaseRequest(
            repo_root=tmp_path,
            project_name="missing",
            tag="v1.0.0",
            github_repo="a/b",
        )
        with pytest.raises(PublishingError, match="Combined PDF not found"):
            prepare_release_bundle(request)
