"""Pytest configuration for template tests.

This file:
- Forces headless matplotlib (MPLBACKEND=Agg)
- Disables Git fsmonitor for child processes that create temporary repositories
- Disables optional Git index writes for child processes that inspect repositories
- Inserts repository roots (infrastructure/, project/src/) ahead of tests/ to avoid shadowing
- Keeps imports consistent for both infrastructure and project test suites
- Provides credential fixtures for external service testing
"""

import os
import sys
from pathlib import Path

import pytest

# Force headless backend for matplotlib in tests
os.environ.setdefault("MPLBACKEND", "Agg")

# Optional Hypothesis profile switching (opt-in, zero cost when unset).
# ``HYPOTHESIS_PROFILE=fast`` shrinks example counts for smoke/agent loops;
# CI and scheduled lanes keep the library default by not setting the variable.
# Importing hypothesis here is deferred so suites that never use it pay nothing.
_hypothesis_profile = os.environ.get("HYPOTHESIS_PROFILE", "").strip()
if _hypothesis_profile:
    import hypothesis

    hypothesis.settings.register_profile(
        _hypothesis_profile,
        max_examples=5 if _hypothesis_profile == "fast" else 100,
        deadline=None,
    )
    hypothesis.settings.load_profile(_hypothesis_profile)

# A user-level ``core.fsmonitor=true`` makes every temporary Git repository in
# the infrastructure suite start a detached fsmonitor daemon. Those daemons can
# outlive ``tmp_path`` cleanup and accumulate across xdist workers. Keep the
# override process-local: Git child processes inherit it, while production and
# the user's persistent Git configuration remain untouched. Command-scope
# parameters take precedence over repository and global configuration.
_GIT_FSMONITOR_PARAMETER = "'core.fsmonitor'='false'"
_git_config_parameters = os.environ.get("GIT_CONFIG_PARAMETERS", "").strip()
if not _git_config_parameters.endswith(_GIT_FSMONITOR_PARAMETER):
    os.environ["GIT_CONFIG_PARAMETERS"] = " ".join(
        parameter for parameter in (_git_config_parameters, _GIT_FSMONITOR_PARAMETER) if parameter
    )

# Read-only commands such as ``git status`` normally refresh cached index stat
# data behind ``.git/index.lock``. Test workers only need the result, not that
# optional cache write; mandatory operations such as add/commit remain enabled.
os.environ["GIT_OPTIONAL_LOCKS"] = "0"

# Add paths for imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Remove tests/ directory from path if present to prevent shadowing
TESTS_DIR = os.path.join(ROOT, "tests")
if TESTS_DIR in sys.path:
    sys.path.remove(TESTS_DIR)

# Add ROOT to path so we can import infrastructure as a package
# Ensure ROOT is FIRST in path to avoid shadowing by tests/infra_tests
if ROOT in sys.path:
    sys.path.remove(ROOT)
sys.path.insert(0, ROOT)

# CRITICAL: Import and cache the real infrastructure module NOW
# before pytest discovers tests/infra_tests which would shadow it
import infrastructure as _real_infra  # noqa: E402

sys.modules["infrastructure"] = _real_infra

# Also cache core submodule
from infrastructure import core as _real_core  # noqa: E402

sys.modules["infrastructure.core"] = _real_core

# Public collection admits only the canonical roster, in its declared order.
# Selected infrastructure is already cached before any scientific import path.
# Local lifecycle directories and external sidecars are never inspected here.
from infrastructure.project.public_scope import public_project_source_roots  # noqa: E402

_PUBLIC_SOURCE_ROOTS = public_project_source_roots(ROOT)
_public_paths = [str(source) for source in _PUBLIC_SOURCE_ROOTS]
sys.path[:] = _public_paths + [path for path in sys.path if path not in _public_paths]


# ============================================================================
# Shared Path Fixtures
# ============================================================================


@pytest.fixture
def repo_root() -> Path:
    """Return the repository root (where pyproject.toml lives).

    Centralized here so both ``tests/infra_tests/`` and ``tests/integration/``
    inherit one definition. Subdir conftests no longer need to redefine it.
    """
    return Path(ROOT)


# ============================================================================
# Pytest Configuration and Markers
# ============================================================================


def pytest_configure(config):
    """Register custom markers for test categorization."""
    config.addinivalue_line("markers", "requires_zenodo: tests requiring Zenodo API access")
    config.addinivalue_line("markers", "requires_github: tests requiring GitHub API access")
    config.addinivalue_line("markers", "requires_arxiv: tests requiring arXiv API access")
    config.addinivalue_line("markers", "requires_latex: tests requiring LaTeX installation")
    config.addinivalue_line("markers", "requires_network: tests requiring network access")
    config.addinivalue_line("markers", "requires_credentials: tests requiring external service credentials")
    config.addinivalue_line(
        "markers",
        "private_project: tests for private sidecar project tooling; opt in only when present",
    )
    config.addinivalue_line(
        "markers",
        "external_fixture: tests requiring downloaded external fixture trees; opt in after setup",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Extend pytest-timeout for real Ollama calls (global default is 10s; streaming often exceeds it)."""
    ollama_timeout = pytest.mark.timeout(180)
    for item in items:
        if item.get_closest_marker("requires_ollama") is None:
            continue
        if item.get_closest_marker("timeout") is not None:
            continue
        item.add_marker(ollama_timeout)


@pytest.fixture
def skip_if_no_latex():
    """Skip test if LaTeX is not installed."""
    import shutil

    if not shutil.which("pdflatex") and not shutil.which("xelatex"):
        pytest.skip("LaTeX not installed (pdflatex or xelatex required)")


# ============================================================================
# Test Workspace Ownership Guard
# ============================================================================


@pytest.fixture(scope="session", autouse=True)
def guard_persistent_test_workspaces():
    """Detect persistent named test leaks while preserving every unowned path."""
    from tests.helpers.workspace_ownership import guard_test_workspaces

    with guard_test_workspaces(Path(ROOT) / "projects"):
        yield
