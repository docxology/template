"""Session fixtures for preserving the tracked exemplar output tree."""

from __future__ import annotations

import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent


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


# TEST-ISOLATION-SYSPATH-1: expose the unique nested source package.
import os as _os
import sys as _sys

_SRC = _os.path.join(_os.path.dirname(__file__), "..", "src")
if _SRC not in _sys.path:
    _sys.path.insert(0, _SRC)
