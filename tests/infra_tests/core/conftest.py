"""Shared fixtures for ``tests/infra_tests/core`` (moved from test_test_runner.py)."""

from __future__ import annotations

from pathlib import Path

import pytest

from ._test_runner_helpers import _write_template_repo_skeleton


@pytest.fixture()
def synthetic_repo(tmp_path: Path) -> Path:
    _write_template_repo_skeleton(tmp_path)
    return tmp_path
