"""Tests for infrastructure.publishing.zenodo client (Deposit API)."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit

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

    def test_prereserve_doi_flag_is_explicit_opt_in(self) -> None:
        metadata = PublicationMetadata(
            title="Reserve DOI",
            authors=["Author"],
            abstract="Abstract.",
            keywords=["test"],
        )
        payload = deposition_metadata_dict(metadata, prereserve_doi=True)
        assert payload["prereserve_doi"] is True
        assert "prereserve_doi" not in deposition_metadata_dict(metadata)


class TestDepositionResult:
    def test_frozen_dataclass(self) -> None:
        result = DepositionResult(
            deposition_id="1",
            bucket_url="http://example/bucket",
            reserved_doi="10.5281/zenodo.22222",
            concept_doi="10.5281/zenodo.11111",
        )
        assert result.deposition_id == "1"
        assert result.bucket_url == "http://example/bucket"
        assert result.reserved_doi == "10.5281/zenodo.22222"
        assert result.concept_doi == "10.5281/zenodo.11111"

    def test_from_zenodo_body_parses_prereserve_and_conceptrecid(self) -> None:
        body = {
            "id": 22222,
            "links": {"bucket": "https://zenodo.test/api/files/bucket222/"},
            "metadata": {
                "prereserve_doi": {"doi": "10.5281/zenodo.22222", "value": "10.5281/zenodo.22222"},
            },
            "conceptrecid": "11111",
        }
        result = DepositionResult.from_zenodo_body(body)
        assert result.deposition_id == "22222"
        assert result.bucket_url == "https://zenodo.test/api/files/bucket222"
        assert result.reserved_doi == "10.5281/zenodo.22222"
        assert result.concept_record_id == "11111"
        assert result.concept_doi == "10.5281/zenodo.11111"


class TestZenodoClientImportGuard:
    def test_requires_requests_package(self) -> None:
        with pytest.raises(ImportError, match="requests package is required"):
            ZenodoClient(ZenodoConfig(access_token="test"), requests_available=False)


class TestZenodoClientDepositFlow:
    """Full create → bucket upload → publish against a local HTTP server."""

    def test_full_deposit_upload_publish_flow(self, tmp_path: Path, zenodo_test_server) -> None:
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

    def test_create_deposition_parses_reserved_and_concept_doi(self) -> None:
        from pytest_httpserver import HTTPServer

        server = HTTPServer()
        server.start()
        try:
            server.expect_request(
                "/deposit/depositions",
                method="POST",
            ).respond_with_json(
                {
                    "id": 22222,
                    "conceptrecid": "11111",
                    "links": {"bucket": f"{server.url_for('')}/files/bucket222"},
                    "metadata": {"prereserve_doi": {"doi": "10.5281/zenodo.22222"}},
                }
            )
            client = ZenodoClient(ZenodoConfig(access_token="test", base_url=server.url_for("")))
            deposition = client.create_deposition({"title": "Reserved", "prereserve_doi": True})
        finally:
            server.stop()

        assert deposition.deposition_id == "22222"
        assert deposition.reserved_doi == "10.5281/zenodo.22222"
        assert deposition.concept_record_id == "11111"
        assert deposition.concept_doi == "10.5281/zenodo.11111"

    def test_upload_uses_bucket_url_not_deposition_id(self, tmp_path: Path, zenodo_test_server) -> None:
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

    def test_publish_to_zenodo_end_to_end(self, tmp_path: Path, zenodo_test_server) -> None:
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
            server.expect_request("/files/bucket999/paper.pdf", method="PUT").respond_with_json({"key": "paper.pdf"})
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
            [
                {
                    "id": 888,
                    "doi": "10.5281/zenodo.list",
                    "metadata": {"doi": "10.5281/zenodo.list"},
                }
            ]
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

        server.expect_request("/deposit/depositions", method="GET").respond_with_handler(deposition_handler)
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
            server.expect_request("/deposit/depositions/777", method="GET").respond_with_json({"id": 777, "files": []})
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


def test_explicit_bearer_ignores_netrc_on_success_and_http_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    zenodo_test_server,
) -> None:
    """A nominated NETRC cannot replace the selected bearer on real HTTP calls."""
    base_url = zenodo_test_server.url_for("")
    hostname = urlsplit(base_url).hostname
    assert hostname is not None
    netrc_path = tmp_path / "netrc"
    netrc_path.write_text(
        f"machine {hostname} login unrelated-user password unrelated-password\n",
        encoding="utf-8",
    )
    netrc_path.chmod(0o600)
    monkeypatch.setenv("NETRC", str(netrc_path))
    token = "explicit-test-bearer"
    headers = {"Authorization": f"Bearer {token}"}
    zenodo_test_server.expect_oneshot_request(
        "/deposit/depositions/auth-success", method="GET", headers=headers
    ).respond_with_json({"id": "auth-success"})
    zenodo_test_server.expect_oneshot_request(
        "/deposit/depositions/auth-error", method="GET", headers=headers
    ).respond_with_json({"message": "unavailable"}, status=503)
    client = ZenodoClient(ZenodoConfig(access_token=token, sandbox=True, base_url=base_url))

    assert client.get_deposition("auth-success") == {"id": "auth-success"}
    with pytest.raises(PublishingError, match="Failed to load deposition auth-error"):
        client.get_deposition("auth-error")

    zenodo_test_server.check()
    requests_received = [request for request, _response in zenodo_test_server.log]
    assert [(request.method, request.path) for request in requests_received] == [
        ("GET", "/deposit/depositions/auth-success"),
        ("GET", "/deposit/depositions/auth-error"),
    ]
    assert all(request.headers["Authorization"] == headers["Authorization"] for request in requests_received)


@pytest.mark.parametrize(
    "link_case",
    [
        "missing",
        "malformed",
        "relative",
        "foreign",
        "scheme",
        "credentials",
        "wrong-path",
        "nonnumeric",
        "query",
        "fragment",
        "original",
        "empty-query",
        "empty-fragment",
        "leading-control",
        "path-control",
    ],
)
def test_new_version_rejects_invalid_latest_draft(link_case, zenodo_test_server) -> None:
    """Reject unusable action links without fetching or modifying a record."""
    base = zenodo_test_server.url_for("").rstrip("/")
    links = {
        "missing": None,
        "malformed": "http://[",
        "relative": "/deposit/depositions/8",
        "foreign": "https://example.invalid/deposit/depositions/8",
        "scheme": base.replace("http://", "https://") + "/deposit/depositions/8",
        "credentials": base.replace("http://", "http://user:password@") + "/deposit/depositions/8",
        "wrong-path": base + "/records/8",
        "nonnumeric": base + "/deposit/depositions/draft",
        "query": base + "/deposit/depositions/8?anything=1",
        "fragment": base + "/deposit/depositions/8#anything",
        "original": base + "/deposit/depositions/7",
        "empty-query": base + "/deposit/depositions/8?",
        "empty-fragment": base + "/deposit/depositions/8#",
        "leading-control": "\n" + base + "/deposit/depositions/8",
        "path-control": base + "/depo\tsit/depositions/8",
    }
    zenodo_test_server.expect_oneshot_request(
        "/deposit/depositions/7/actions/newversion", method="POST"
    ).respond_with_json({"id": 7, "links": {"bucket": base + "/files/original", "latest_draft": links[link_case]}})
    client = ZenodoClient(ZenodoConfig(access_token="loopback-only", base_url=base))
    with pytest.raises(PublishingError, match="latest_draft"):
        client.create_new_version("7")
    zenodo_test_server.check()
    assert [(request.method, request.path) for request, _response in zenodo_test_server.log] == [
        ("POST", "/deposit/depositions/7/actions/newversion")
    ]


@pytest.mark.parametrize(
    "draft_id,state,submitted,reason",
    [
        (9, "unsubmitted", False, "identity differs"),
        (8, "done", True, "unpublished"),
        (8, "unsubmitted", True, "unpublished"),
        (8, "done", False, "unpublished"),
        (8, "inprogress", True, "unpublished"),
        (8, "error", False, "unpublished"),
        (8, None, False, "unpublished"),
        (8, "unsubmitted", None, "unpublished"),
    ],
)
def test_new_version_rejects_wrong_identity_or_published_draft(
    draft_id, state, submitted, reason, zenodo_test_server
) -> None:
    """Read the genuine draft but refuse an unsafe resource before later writes."""
    base = zenodo_test_server.url_for("").rstrip("/")
    zenodo_test_server.expect_oneshot_request(
        "/deposit/depositions/7/actions/newversion", method="POST"
    ).respond_with_json({"id": 7, "links": {"latest_draft": base + "/deposit/depositions/8"}})
    zenodo_test_server.expect_oneshot_request("/deposit/depositions/8", method="GET").respond_with_json(
        {"id": draft_id, "state": state, "submitted": submitted, "links": {"bucket": base + "/files/actual-draft"}}
    )
    client = ZenodoClient(ZenodoConfig(access_token="loopback-only", base_url=base))
    with pytest.raises(PublishingError, match=reason):
        client.create_new_version("7")
    zenodo_test_server.check()
    assert [(request.method, request.path) for request, _response in zenodo_test_server.log] == [
        ("POST", "/deposit/depositions/7/actions/newversion"),
        ("GET", "/deposit/depositions/8"),
    ]


@pytest.mark.parametrize("draft_state", ["unsubmitted", "inprogress"])
def test_new_version_returns_latest_draft_not_original_action_resource(draft_state, zenodo_test_server) -> None:
    base = zenodo_test_server.url_for("").rstrip("/")
    zenodo_test_server.expect_oneshot_request(
        "/deposit/depositions/7/actions/newversion", method="POST"
    ).respond_with_json(
        {
            "id": 7,
            "state": "done",
            "submitted": True,
            "links": {"bucket": base + "/files/original", "latest_draft": base + "/deposit/depositions/8"},
        }
    )
    zenodo_test_server.expect_oneshot_request("/deposit/depositions/8", method="GET").respond_with_json(
        {
            "id": 8,
            "state": draft_state,
            "submitted": False,
            "links": {"bucket": base + "/files/actual-draft"},
            "conceptdoi": "10.5281/zenodo.6",
            "metadata": {"prereserve_doi": {"doi": "10.5281/zenodo.8"}},
        }
    )
    client = ZenodoClient(ZenodoConfig(access_token="loopback-only", base_url=base))
    result = client.create_new_version("7")
    assert result.deposition_id == "8" and result.bucket_url == base + "/files/actual-draft"
    assert result.reserved_doi == "10.5281/zenodo.8" and result.concept_doi == "10.5281/zenodo.6"
    zenodo_test_server.check()
    assert [(request.method, request.path) for request, _response in zenodo_test_server.log] == [
        ("POST", "/deposit/depositions/7/actions/newversion"),
        ("GET", "/deposit/depositions/8"),
    ]


@pytest.mark.parametrize("supplied_date", [None, "", "2026", "2024-02-29"])
def test_zenodo_date_mapping_preserves_full_date_and_omits_citation_year(supplied_date, zenodo_test_server) -> None:
    """Exercise the genuine mapper/client and inspect the actual POST payload."""
    metadata = PublicationMetadata(
        title="Date mapping", authors=["Test Author"], abstract="Abstract.", keywords=[], publication_date=supplied_date
    )
    result = publish_to_zenodo(metadata, [], access_token="loopback-only", base_url=zenodo_test_server.url_for(""))
    assert result.deposition_id == "12345"
    requests_received = [request for request, _response in zenodo_test_server.log]
    assert [(request.method, request.path) for request in requests_received] == [
        ("POST", "/deposit/depositions"),
        ("POST", "/deposit/depositions/12345/actions/publish"),
    ]
    payload = requests_received[0].get_json()["metadata"]
    if supplied_date == "2024-02-29":
        assert payload["publication_date"] == supplied_date
    else:
        assert "publication_date" not in payload
    assert metadata.publication_date == supplied_date
    zenodo_test_server.check()


@pytest.mark.parametrize("supplied_date", ["2026-02-30", "2026-2-1", "20260201", "not-a-date", "0000"])
@pytest.mark.parametrize("route", ["first", "reserve", "new-version"])
def test_invalid_zenodo_date_refuses_before_any_http_request(supplied_date, route, zenodo_test_server) -> None:
    from infrastructure.publishing.zenodo.publish import reserve_zenodo_deposition

    metadata = PublicationMetadata(
        title="Invalid date", authors=["Test Author"], abstract="Abstract.", keywords=[], publication_date=supplied_date
    )
    base_url = zenodo_test_server.url_for("")
    with pytest.raises(PublishingError, match="publication_date"):
        if route == "first":
            publish_to_zenodo(metadata, [], access_token="loopback-only", base_url=base_url)
        elif route == "reserve":
            reserve_zenodo_deposition(
                metadata, access_token="loopback-only", base_url=base_url, existing_doi="10.5281/zenodo.7"
            )
        else:
            publish_new_version_to_zenodo(
                metadata, [], access_token="loopback-only", existing_doi="10.5281/zenodo.7", base_url=base_url
            )
    assert zenodo_test_server.log == []
    assert metadata.publication_date == supplied_date
    zenodo_test_server.check()
