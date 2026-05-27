"""Tests for infrastructure.publishing.zenodo client (Deposit API)."""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.core.exceptions import PublishingError, UploadError
from infrastructure.publishing.zenodo.client import ZenodoClient
from infrastructure.publishing.zenodo.config import ZenodoConfig
from infrastructure.publishing.zenodo.models import DepositionResult
from infrastructure.publishing.zenodo.publish import (
    publish_new_version_to_zenodo,
    publish_to_zenodo,
)
from infrastructure.publishing.models import AuthorRecord, PublicationMetadata
from infrastructure.publishing.zenodo.publish import deposition_metadata_dict


class TestDepositionMetadataDict:
    def test_maps_creators_publication_date_version_and_related(self) -> None:
        metadata = PublicationMetadata(
            title="Mapped Paper",
            authors=["Legacy Author"],
            abstract="Short abstract.",
            keywords=["release"],
            license="CC-BY-4.0",
            deposit_description="Full deposit description with footer.",
            publication_date="2026-05-27",
            paper_version="1.0",
            release_tag="v1.0.0",
            github_release_url="https://github.com/owner/repo/releases/tag/v1.0.0",
            author_records=[
                AuthorRecord(
                    name="Dr. Jane Smith",
                    orcid="0000-0002-1825-0097",
                    affiliation="Example University",
                )
            ],
        )
        payload = deposition_metadata_dict(metadata)
        assert payload["description"] == "Full deposit description with footer."
        assert payload["publication_date"] == "2026-05-27"
        assert payload["version"] == "1.0"
        assert payload["creators"] == [
            {
                "name": "Dr. Jane Smith",
                "affiliation": "Example University",
                "orcid": "0000-0002-1825-0097",
            }
        ]
        assert payload["related_identifiers"] == [
            {
                "identifier": "https://github.com/owner/repo/releases/tag/v1.0.0",
                "relation": "isSupplementTo",
                "resource_type": "software",
            }
        ]

    def test_omits_placeholder_orcid_from_creators(self) -> None:
        metadata = PublicationMetadata(
            title="Placeholder ORCID",
            authors=["Author"],
            abstract="Abstract.",
            keywords=["test"],
            author_records=[
                AuthorRecord(name="Author", orcid="0000-0000-0000-1234", affiliation="Institute"),
            ],
        )
        payload = deposition_metadata_dict(metadata)
        assert payload["creators"] == [{"name": "Author", "affiliation": "Institute"}]


class TestDepositionResult:
    def test_frozen_dataclass(self) -> None:
        result = DepositionResult(deposition_id="1", bucket_url="http://example/bucket")
        assert result.deposition_id == "1"
        assert result.bucket_url == "http://example/bucket"


class TestZenodoClientImportGuard:
    def test_requires_requests_package(self, monkeypatch) -> None:
        import infrastructure.publishing.zenodo.client as zenodo_client

        monkeypatch.setattr(zenodo_client, "_requests_available", False)
        with pytest.raises(ImportError, match="requests package is required"):
            ZenodoClient(ZenodoConfig(access_token="test"))


class TestZenodoClientDepositFlow:
    """Full create → bucket upload → publish against a local HTTP server."""

    def test_full_deposit_upload_publish_flow(
        self, tmp_path: Path, zenodo_test_server
    ) -> None:
        pdf = tmp_path / "paper.pdf"
        pdf.write_bytes(b"%PDF-1.4 test")

        config = ZenodoConfig(
            access_token="test",
            base_url=zenodo_test_server.url_for(""),
        )
        client = ZenodoClient(config)

        deposition = client.create_deposition({"title": "Integration Test"})
        assert isinstance(deposition, DepositionResult)
        assert deposition.deposition_id == "12345"
        assert deposition.bucket_url.endswith("/files/bucket123")

        client.upload_file(deposition.bucket_url, pdf)
        doi = client.publish(deposition.deposition_id)
        assert doi == "10.5281/zenodo.12345"

    def test_upload_uses_bucket_url_not_deposition_id(
        self, tmp_path: Path, zenodo_test_server
    ) -> None:
        """Regression: uploads must target links.bucket, not /files/{deposition_id}/."""
        pdf = tmp_path / "test.pdf"
        pdf.write_bytes(b"%PDF")

        config = ZenodoConfig(
            access_token="test",
            base_url=zenodo_test_server.url_for(""),
        )
        client = ZenodoClient(config)
        deposition = client.create_deposition({"title": "Bucket regression"})
        client.upload_file(deposition.bucket_url, pdf)

    def test_publish_to_zenodo_end_to_end(
        self, tmp_path: Path, zenodo_test_server
    ) -> None:
        paper = tmp_path / "paper.pdf"
        paper.write_bytes(b"%PDF")

        metadata = PublicationMetadata(
            title="Test Paper",
            authors=["Author One"],
            abstract="Abstract text.",
            keywords=["test"],
            license="CC-BY-4.0",
        )
        result = publish_to_zenodo(
            metadata,
            [paper],
            access_token="test-token",
            sandbox=True,
            base_url=zenodo_test_server.url_for(""),
        )
        assert result.doi == "10.5281/zenodo.12345"
        assert result.deposition_id == "12345"

    def test_create_deposition_failure(self) -> None:
        config = ZenodoConfig(
            access_token="test",
            base_url="http://invalid-host:9999/",
        )
        client = ZenodoClient(config)
        with pytest.raises(PublishingError):
            client.create_deposition({"title": "Fail"})

    def test_upload_file_missing_path(self, tmp_path: Path) -> None:
        config = ZenodoConfig(access_token="test")
        client = ZenodoClient(config)
        with pytest.raises(UploadError):
            client.upload_file(
                "http://example/bucket",
                tmp_path / "missing.pdf",
            )

    def test_publish_to_zenodo_skips_missing_file(
        self,
        tmp_path: Path,
        zenodo_test_server,
        caplog,
    ) -> None:
        existing = tmp_path / "paper.pdf"
        existing.write_bytes(b"%PDF")
        missing = tmp_path / "missing.pdf"

        metadata = PublicationMetadata(
            title="Skip missing",
            authors=["Author"],
            abstract="Abstract.",
            keywords=["test"],
        )

        with caplog.at_level("WARNING"):
            result = publish_to_zenodo(
                metadata,
                [existing, missing],
                access_token="test-token",
                sandbox=True,
                base_url=zenodo_test_server.url_for(""),
            )

        assert result.doi == "10.5281/zenodo.12345"
        assert "Skipping non-existent file" in caplog.text

    def test_publish_raises_when_response_lacks_doi(
        self,
        tmp_path: Path,
    ) -> None:
        from pytest_httpserver import HTTPServer

        server = HTTPServer()
        server.start()
        try:
            server.expect_request("/deposit/depositions", method="POST").respond_with_json(
                {
                    "id": 999,
                    "links": {"bucket": f"{server.url_for('')}/files/bucket999"},
                }
            )
            server.expect_request("/files/bucket999/paper.pdf", method="PUT").respond_with_json(
                {"key": "paper.pdf"}
            )
            server.expect_request(
                "/deposit/depositions/999/actions/publish",
                method="POST",
            ).respond_with_json({"state": "done"})

            pdf = tmp_path / "paper.pdf"
            pdf.write_bytes(b"%PDF")

            config = ZenodoConfig(
                access_token="test",
                base_url=server.url_for(""),
            )
            client = ZenodoClient(config)
            deposition = client.create_deposition({"title": "No DOI response"})
            client.upload_file(deposition.bucket_url, pdf)

            with pytest.raises(PublishingError, match="no DOI"):
                client.publish(deposition.deposition_id)
        finally:
            server.stop()


class TestZenodoVersioning:
    def test_resolve_deposition_id_from_doi(self, zenodo_version_test_server) -> None:
        config = ZenodoConfig(
            access_token="test",
            base_url=zenodo_version_test_server.url_for(""),
        )
        client = ZenodoClient(config)
        deposition_id = client.resolve_deposition_id_from_doi("10.5281/zenodo.11111")
        assert deposition_id == "999"

    def test_resolve_deposition_id_from_doi_list_response(self) -> None:
        """Production Zenodo may return a bare list for filtered deposition queries."""
        from pytest_httpserver import HTTPServer

        server = HTTPServer()
        server.start()
        server.expect_request("/deposit/depositions", method="GET").respond_with_json(
            [{"id": 888, "doi": "10.5281/zenodo.list", "metadata": {"doi": "10.5281/zenodo.list"}}]
        )
        try:
            config = ZenodoConfig(access_token="test", base_url=server.url_for(""))
            client = ZenodoClient(config)
            deposition_id = client.resolve_deposition_id_from_doi("10.5281/zenodo.list")
            assert deposition_id == "888"
        finally:
            server.stop()

    def test_resolve_deposition_id_falls_back_to_conceptdoi(self) -> None:
        """Version DOIs may miss deposit search; conceptdoi query resolves latest deposition."""
        import json

        from pytest_httpserver import HTTPServer
        from werkzeug.wrappers import Response

        server = HTTPServer()
        server.start()

        def deposition_handler(request):
            query = request.args.get("q", "")
            if query == "conceptdoi:10.5281/zenodo.20415767":
                payload = [{"id": 20415779, "doi": "10.5281/zenodo.20415779"}]
            else:
                payload = []
            return Response(json.dumps(payload), mimetype="application/json")

        server.expect_request("/deposit/depositions", method="GET").respond_with_handler(
            deposition_handler
        )
        server.expect_request("/records", method="GET").respond_with_json(
            {
                "hits": {
                    "hits": [
                        {
                            "id": 20415768,
                            "doi": "10.5281/zenodo.20415768",
                            "conceptdoi": "10.5281/zenodo.20415767",
                        }
                    ]
                }
            }
        )
        try:
            config = ZenodoConfig(access_token="test", base_url=server.url_for(""))
            client = ZenodoClient(config)
            deposition_id = client.resolve_deposition_id_from_doi("10.5281/zenodo.20415768")
            assert deposition_id == "20415779"
        finally:
            server.stop()

    def test_create_new_version_and_update_metadata(
        self,
        zenodo_version_test_server,
    ) -> None:
        config = ZenodoConfig(
            access_token="test",
            base_url=zenodo_version_test_server.url_for(""),
        )
        client = ZenodoClient(config)
        result = client.create_new_version("999")
        assert result.deposition_id == "54321"
        removed = client.clear_deposition_files(result.deposition_id)
        assert removed == ["test_release_combined.pdf"]
        client.update_deposition_metadata(result.deposition_id, {"title": "Updated title"})

    def test_clear_deposition_files_empty_draft(self) -> None:
        from pytest_httpserver import HTTPServer

        server = HTTPServer()
        server.start()
        try:
            server.expect_request("/deposit/depositions/777", method="GET").respond_with_json(
                {"id": 777, "files": []}
            )
            config = ZenodoConfig(access_token="test", base_url=server.url_for(""))
            client = ZenodoClient(config)
            assert client.clear_deposition_files("777") == []
        finally:
            server.stop()

    def test_publish_new_version_to_zenodo(
        self,
        tmp_path: Path,
        zenodo_version_test_server,
    ) -> None:
        pdf = tmp_path / "test_release_combined.pdf"
        pdf.write_bytes(b"%PDF")
        metadata = PublicationMetadata(
            title="Version Two",
            authors=["Author"],
            abstract="Updated abstract.",
            keywords=["release"],
            license="CC-BY-4.0",
        )
        result = publish_new_version_to_zenodo(
            metadata,
            [pdf],
            access_token="test",
            existing_doi="10.5281/zenodo.11111",
            sandbox=True,
            base_url=zenodo_version_test_server.url_for(""),
        )
        assert result.doi == "10.5281/zenodo.54321"
        assert result.deposition_id == "54321"

    def test_patch_deposition_description_after_publish(
        self,
        tmp_path: Path,
        zenodo_test_server,
    ) -> None:
        from infrastructure.publishing.models import PublicationMetadata
        from infrastructure.publishing.zenodo.publish import (
            patch_deposition_description,
            publish_to_zenodo,
        )

        zenodo_test_server.expect_request(
            "/deposit/depositions/12345",
            method="PUT",
        ).respond_with_json({"id": 12345, "metadata": {"description": "patched"}})

        pdf = tmp_path / "paper.pdf"
        pdf.write_bytes(b"%PDF")
        metadata = PublicationMetadata(
            title="Patch Test",
            authors=["Author"],
            abstract="Abstract.",
            keywords=["test"],
            deposit_description="Abstract.\n\n---\nAssociated artifacts\nDOI: https://doi.org/10.5281/zenodo.12345",
        )
        result = publish_to_zenodo(
            metadata,
            [pdf],
            access_token="test-token",
            sandbox=True,
            base_url=zenodo_test_server.url_for(""),
        )
        patch_deposition_description(
            result.deposition_id,
            metadata,
            access_token="test-token",
            sandbox=True,
            base_url=zenodo_test_server.url_for(""),
        )
        assert result.doi == "10.5281/zenodo.12345"
