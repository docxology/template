"""Network guard helpers for tests that reach external or local services."""

from __future__ import annotations

import contextlib
from collections.abc import Iterator

import pytest
import requests

from infrastructure.core.exceptions import LLMConnectionError


@contextlib.contextmanager
def safe_network_test(service_name: str = "External service") -> Iterator[None]:
    """Context manager to safely run network-dependent tests.

    Catches common connection errors and fails with setup guidance instead of
    producing a skip. Designed for integration tests whose marker fixtures
    should already have made the local service (Ollama, etc.) available.

    Args:
        service_name: Name of the service for the failure message

    Usage:
        with safe_network_test("Ollama"):
            response = client.query("test")
    """
    try:
        yield
    except (LLMConnectionError, requests.exceptions.RequestException, ConnectionError) as e:
        pytest.fail(f"{service_name} connection issue after test setup: {e}")
