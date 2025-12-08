"""Pytest configuration for template tests.

This file:
- Forces headless matplotlib (MPLBACKEND=Agg)
- Inserts repository roots (infrastructure/, project/src/) ahead of tests/ to avoid shadowing
- Keeps imports consistent for both infrastructure and project test suites
- Provides credential fixtures for external service testing
"""
import os
import sys
import pytest
from pathlib import Path

# Force headless backend for matplotlib in tests
os.environ.setdefault("MPLBACKEND", "Agg")

# Add paths for imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Add ROOT to path so we can import infrastructure as a package
# Ensure ROOT is FIRST in path to avoid shadowing by tests/infrastructure
if ROOT in sys.path:
    sys.path.remove(ROOT)
sys.path.insert(0, ROOT)

# Remove tests/ directory from path if present to prevent shadowing
TESTS_DIR = os.path.join(ROOT, "tests")
if TESTS_DIR in sys.path:
    sys.path.remove(TESTS_DIR)

# Add src/ to path for scientific modules (if it exists)
SRC = os.path.join(ROOT, "src")
if os.path.exists(SRC) and SRC not in sys.path:
    sys.path.insert(0, SRC)

# Add project/src/ to path for project modules
PROJECT_SRC = os.path.join(ROOT, "project", "src")
if os.path.exists(PROJECT_SRC) and PROJECT_SRC not in sys.path:
    sys.path.insert(0, PROJECT_SRC)


# ============================================================================
# Pytest Configuration and Markers
# ============================================================================

def pytest_configure(config):
    """Register custom markers for test categorization."""
    config.addinivalue_line(
        "markers", "requires_zenodo: tests requiring Zenodo API access"
    )
    config.addinivalue_line(
        "markers", "requires_github: tests requiring GitHub API access"
    )
    config.addinivalue_line(
        "markers", "requires_arxiv: tests requiring arXiv API access"
    )
    config.addinivalue_line(
        "markers", "requires_latex: tests requiring LaTeX installation"
    )
    config.addinivalue_line(
        "markers", "requires_network: tests requiring network access"
    )
    config.addinivalue_line(
        "markers", "requires_credentials: tests requiring external service credentials"
    )


# ============================================================================
# Credential Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def credential_manager():
    """Provide CredentialManager for tests.
    
    Returns:
        CredentialManager instance configured for testing
    """
    from infrastructure.core.credentials import CredentialManager
    
    # Try to load test credentials config if it exists
    config_file = Path(ROOT) / "test_credentials.yaml"
    return CredentialManager(config_file=config_file if config_file.exists() else None)


@pytest.fixture(scope="session")
def zenodo_credentials(credential_manager):
    """Provide Zenodo credentials for tests (sandbox by default).
    
    Returns:
        Dictionary with Zenodo API credentials
        
    Raises:
        pytest.skip: If Zenodo credentials are not available
    """
    if not credential_manager.has_zenodo_credentials(use_sandbox=True):
        pytest.skip("Zenodo sandbox credentials not available. "
                   "Set ZENODO_SANDBOX_TOKEN in .env file.")
    
    return credential_manager.get_zenodo_credentials(use_sandbox=True)


@pytest.fixture(scope="session")
def github_credentials(credential_manager):
    """Provide GitHub credentials for tests.
    
    Returns:
        Dictionary with GitHub API credentials
        
    Raises:
        pytest.skip: If GitHub credentials are not available
    """
    if not credential_manager.has_github_credentials():
        pytest.skip("GitHub credentials not available. "
                   "Set GITHUB_TOKEN and GITHUB_REPO in .env file.")
    
    return credential_manager.get_github_credentials()


@pytest.fixture(scope="session")
def arxiv_credentials(credential_manager):
    """Provide arXiv credentials for tests (optional).
    
    Returns:
        Dictionary with arXiv API credentials
        
    Raises:
        pytest.skip: If arXiv credentials are not available
    """
    if not credential_manager.has_arxiv_credentials():
        pytest.skip("arXiv credentials not available. "
                   "Set ARXIV_USERNAME and ARXIV_PASSWORD in .env file.")
    
    return credential_manager.get_arxiv_credentials()


@pytest.fixture
def skip_if_no_latex():
    """Skip test if LaTeX is not installed."""
    import shutil
    
    if not shutil.which("pdflatex") and not shutil.which("xelatex"):
        pytest.skip("LaTeX not installed (pdflatex or xelatex required)")

