"""Test configuration for publishing infrastructure tests."""

import json

import pytest
from pytest_httpserver import HTTPServer


@pytest.fixture
def zenodo_test_server():
    """Local HTTP test server mimicking Zenodo API endpoints."""
    server = HTTPServer()
    server.start()

    # Mock deposition creation endpoint
    server.expect_request("/api/deposit/depositions", method="POST").respond_with_json(
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
    server.expect_request(
        "/api/files/bucket123/test.pdf", method="PUT"
    ).respond_with_json(
        {
            "key": "test.pdf",
            "mimetype": "application/pdf",
            "checksum": "md5:abc123",
            "size": 1234,
            "links": {"self": f"{server.url_for('')}/api/files/bucket123/test.pdf"},
        }
    )

    # Mock file upload endpoint for paper.pdf (used in full workflow test)
    server.expect_request(
        "/api/files/bucket123/paper.pdf", method="PUT"
    ).respond_with_json(
        {
            "key": "paper.pdf",
            "mimetype": "application/pdf",
            "checksum": "md5:paper123",
            "size": 5678,
            "links": {"self": f"{server.url_for('')}/api/files/bucket123/paper.pdf"},
        }
    )

    # Mock publish endpoint
    server.expect_request(
        "/api/deposit/depositions/12345/actions/publish", method="POST"
    ).respond_with_json(
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

    yield server

    server.stop()


@pytest.fixture
def github_test_server():
    """Local HTTP test server mimicking GitHub API endpoints."""
    server = HTTPServer()
    server.start()

    # Mock GitHub release creation
    server.expect_request(
        "/repos/testuser/testrepo/releases", method="POST"
    ).respond_with_json(
        {
            "id": 12345,
            "tag_name": "v1.0.0",
            "name": "Test Release",
            "body": "Test release description",
            "html_url": "https://github.com/testuser/testrepo/releases/tag/v1.0.0",
        }
    )

    yield server

    server.stop()
