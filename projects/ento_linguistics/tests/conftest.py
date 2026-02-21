"""Pytest configuration for project tests."""

import os
import sys

# Force headless backend for matplotlib in tests
os.environ.setdefault("MPLBACKEND", "Agg")

# Add template root to path so we can import infrastructure modules
# tests/ -> ento_linguistics/ -> projects_archive/ -> template/
TEMPLATE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if TEMPLATE_ROOT not in sys.path:
    sys.path.insert(0, TEMPLATE_ROOT)

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
