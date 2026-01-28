"""Test configuration for validation infrastructure tests."""

import pytest
from pytest_httpserver import HTTPServer


@pytest.fixture
def http_test_server():
    """Local HTTP test server for link checking tests."""
    server = HTTPServer()
    server.start()

    # Mock successful external links
    server.expect_request("/").respond_with_data(
        "<html><body>Test page</body></html>", content_type="text/html", status=200
    )

    server.expect_request("/valid-link").respond_with_data(
        "<html><body>Valid link content</body></html>",
        content_type="text/html",
        status=200,
    )

    # Mock broken external links
    server.expect_request("/broken-link").respond_with_data(
        "Not found", content_type="text/plain", status=404
    )

    server.expect_request("/timeout-link").respond_with_data(
        "Request timeout", content_type="text/plain", status=408
    )

    # Mock redirects
    server.expect_request("/redirect-link").respond_with_data(
        "",
        content_type="text/plain",
        status=301,
        headers={"Location": "/final-destination"},
    )

    server.expect_request("/final-destination").respond_with_data(
        "<html><body>Redirect destination</body></html>",
        content_type="text/html",
        status=200,
    )

    yield server

    server.stop()
