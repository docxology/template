"""Session fixtures for preserving the tracked exemplar output tree."""

from __future__ import annotations

import importlib.util
import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
# Select actual SDK before exposing the own namespace; no ancestor imports.

_bootstrap_spec = importlib.util.spec_from_file_location(
    "autopoiesis_test_bootstrap", PROJECT_ROOT / "scripts/_bootstrap.py"
)
if _bootstrap_spec is None or _bootstrap_spec.loader is None:
    raise ImportError("actual own bootstrap is unavailable")
_bootstrap = importlib.util.module_from_spec(_bootstrap_spec)
_bootstrap_spec.loader.exec_module(_bootstrap)
_sdk = _bootstrap.bootstrap_project(PROJECT_ROOT)
if _sdk is None or _sdk.__version__ != "4.0.2":
    raise ImportError("the own test suite requires the declared platform 4.0.2 dependency")


@pytest.fixture(scope="session", autouse=True)
def _preserve_project_output(
    tmp_path_factory: pytest.TempPathFactory,
) -> Iterator[None]:
    """Restore real output byte-for-byte after the no-mock project suite."""
    output = PROJECT_ROOT / "output"
    snapshot = tmp_path_factory.mktemp("autopoiesis-output") / "output"
    existed = output.is_dir()
    if existed:
        shutil.copytree(output, snapshot, symlinks=True)

    yield

    if output.exists():
        shutil.rmtree(output)
    if existed:
        shutil.copytree(snapshot, output, symlinks=True)
