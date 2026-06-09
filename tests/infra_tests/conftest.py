"""Pytest configuration for infrastructure layer tests.

Provides shared fixtures and utilities for testing infrastructure modules.
All fixtures use real implementations following the 'no mocks' policy.
"""

import os
from pathlib import Path

# Force headless backend for matplotlib in tests
os.environ.setdefault("MPLBACKEND", "Agg")

# Repository root path
ROOT = Path(__file__).parent.parent.parent.resolve()
TESTS_INFRASTRUCTURE = Path(__file__).parent.resolve()

# Add repo root to path so we can import infrastructure modules
# (infrastructure/ is at the repo root level)
# IMPORTANT: Do NOT add tests/infra_tests to sys.path - it would shadow
# infrastructure.* imports with tests/infra_tests/* packages
import sys

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import helper functions using importlib to avoid sys.path pollution
# (adding tests/infra_tests to sys.path would cause tests/infra_tests/validation
# to shadow infrastructure/validation)
import importlib.util

_helpers_path = TESTS_INFRASTRUCTURE / "_test_helpers.py"
_spec = importlib.util.spec_from_file_location("_test_helpers", _helpers_path)
_test_helpers = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_test_helpers)

# Export helper functions
create_project_config_structure = _test_helpers.create_project_config_structure
create_sample_config_data = _test_helpers.create_sample_config_data
write_config_file = _test_helpers.write_config_file
create_output_directory_structure = _test_helpers.create_output_directory_structure
create_pdf_file = _test_helpers.create_pdf_file
create_output_with_pdf = _test_helpers.create_output_with_pdf
create_test_manuscript_files = _test_helpers.create_test_manuscript_files
create_test_figure_files = _test_helpers.create_test_figure_files
cleanup_test_directory = _test_helpers.cleanup_test_directory


# =============================================================================
# Path Fixtures
# =============================================================================
#
# ``repo_root`` lives in tests/conftest.py (the root) so all subdirectories
# inherit one definition. Do not redefine it here.
#
# Project-config and output-directory scaffolding is provided as plain helper
# functions in ``_test_helpers.py`` (re-exported above), not as fixtures —
# tests call them directly with their own ``tmp_path``.
#
# ensure_ollama_for_tests lives in tests/conftest.py (repo root) so integration
# and infra tests share one session-scoped definition.
