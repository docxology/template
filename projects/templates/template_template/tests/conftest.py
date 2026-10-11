"""Select the declared SDK before binding this own project namespace."""

from __future__ import annotations

import importlib.util
import os
import sys
from collections.abc import Iterator

import pytest
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
ROOT = Path(__file__).resolve().parent.parent
TESTS = Path(__file__).resolve().parent
_bootstrap_spec = importlib.util.spec_from_file_location("template_test_bootstrap", ROOT / "scripts/_bootstrap.py")
if _bootstrap_spec is None or _bootstrap_spec.loader is None:
    raise ImportError("actual own project bootstrap is unavailable")
_bootstrap = importlib.util.module_from_spec(_bootstrap_spec)
_bootstrap_spec.loader.exec_module(_bootstrap)
_bootstrap.bootstrap_project(ROOT)
# Test helpers resolve complete SOURCE DATA separately; it is never added to imports.
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))


@pytest.fixture(scope="session", autouse=True)
def _verify_bound_source_data() -> Iterator[None]:
    """Keep the declared DATA reference separate from SDK and own source imports."""
    from template_template.core.paths import data_repo_root, verify_reference_inputs

    data_repo_root(ROOT)
    yield
    verify_reference_inputs()
