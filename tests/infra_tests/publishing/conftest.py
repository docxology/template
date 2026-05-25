"""Test configuration for publishing infrastructure tests."""

import pytest
from pytest_httpserver import HTTPServer


@pytest.fixture
def zenodo_test_server():
    """Local HTTP test server mimicking Zenodo API endpoints."""
    server = HTTPServer()
    server.start()

    # Mock deposition creation endpoint (client uses api_base_url + /deposit/depositions)
    server.expect_request("/deposit/depositions", method="POST").respond_with_json(
        {
            "id": 12345,
            "links": {
                "bucket": f"{server.url_for('')}/api/files/bucket123",
                "publish": f"{server.url_for('')}/api/deposit/depositions/12345/actions/publish",
            },
            "metadata": {
                "title": "Test Deposition",
                "upload_type": "publication",
                "publication_type": "article",
            },
            "state": "unsubmitted",
            "submitted": False,
        }
    )

    # Mock file upload endpoint for test.pdf
    server.expect_request("/files/bucket123/test.pdf", method="PUT").respond_with_json(
        {
            "key": "test.pdf",
            "mimetype": "application/pdf",
            "checksum": "md5:abc123",
            "size": 1234,
            "links": {"self": f"{server.url_for('')}/api/files/bucket123/test.pdf"},
        }
    )

    # Mock file upload endpoint for paper.pdf (used in full workflow test)
    server.expect_request("/files/bucket123/paper.pdf", method="PUT").respond_with_json(
        {
            "key": "paper.pdf",
            "mimetype": "application/pdf",
            "checksum": "md5:paper123",
            "size": 5678,
            "links": {"self": f"{server.url_for('')}/api/files/bucket123/paper.pdf"},
        }
    )

    # Mock publish endpoint
    server.expect_request("/deposit/depositions/12345/actions/publish", method="POST").respond_with_json(
        {
            "doi": "10.5281/zenodo.12345",
            "doi_url": "https://doi.org/10.5281/zenodo.12345",
            "links": {
                "record": "https://zenodo.org/record/12345",
                "record_html": "https://zenodo.org/record/12345",
            },
            "metadata": {"doi": "10.5281/zenodo.12345", "title": "Test Publication"},
            "state": "done",
            "submitted": True,
        }
    )

    try:
        yield server
    finally:
        server.stop()


@pytest.fixture
def github_test_server():
    """Local HTTP test server mimicking GitHub API endpoints.

    Provides both the basic ``/repos/testuser/testrepo/releases`` POST endpoint
    and a generic asset-upload endpoint so callers can exercise
    ``create_github_release`` end-to-end against ``server.url_for("")``.
    """
    server = HTTPServer()
    server.start()

    upload_url = f"{server.url_for('')}/repos/testuser/testrepo/releases/12345/assets"

    # Mock GitHub release creation
    server.expect_request("/repos/testuser/testrepo/releases", method="POST").respond_with_json(
        {
            "id": 12345,
            "tag_name": "v1.0.0",
            "name": "Test Release",
            "body": "Test release description",
            "html_url": "https://github.com/testuser/testrepo/releases/tag/v1.0.0",
            # GitHub returns a templated upload_url with {?name,label} suffix
            "upload_url": upload_url + "{?name,label}",
        }
    )

    # Mock GitHub asset upload (generic — accepts any POST under the assets path)
    server.expect_request("/repos/testuser/testrepo/releases/12345/assets", method="POST").respond_with_json(
        {"id": 99, "name": "asset.pdf", "state": "uploaded"},
        status=201,
    )

    try:
        yield server
    finally:
        server.stop()
