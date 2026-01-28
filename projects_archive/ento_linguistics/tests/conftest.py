"""Pytest configuration for project tests."""

import os
import sys

# Force headless backend for matplotlib in tests
os.environ.setdefault("MPLBACKEND", "Agg")

# Add src/ to path so we can import project modules
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

# Add infrastructure/ to path so we can import template infrastructure
TEMPLATE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
INFRASTRUCTURE = os.path.join(TEMPLATE_ROOT, "infrastructure")
if INFRASTRUCTURE not in sys.path:
    sys.path.insert(0, INFRASTRUCTURE)

# Configure pytest-httpserver
try:
    import pytest
    from pytest_httpserver import HTTPServer

    @pytest.fixture
    def httpserver():
        """Provide HTTP server for testing."""
        server = HTTPServer()
        server.start()
        yield server
        server.clear()
        if server.is_running():
            server.stop()

except ImportError:
    # pytest-httpserver not available
    pass
