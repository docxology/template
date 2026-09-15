"""Negative control for the documented fast local test loop.

The fast loop (see docs/operational/config/performance-optimization.md)
runs a fixed, high-signal subset of the infrastructure suite for agent
iterations. A fast lane that silently passes on breakage is void, so this
module proves the selector still covers its claimed surface:

1. the declared path manifest is non-empty and every entry exists on disk;
2. each entry still collects at least one test in a real pytest
   ``--collect-only`` subprocess (import errors and moved modules fail here);
3. each entry is a real pytest target (no empty-directory vacuity).

The full infrastructure gate remains the merge authority; this test only
guarantees the fast selector cannot become vacuously green.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

# Keep in sync with docs/operational/config/performance-optimization.md
# (fast local loop). Ordered so later entries reuse warmed interpreter caches.
FAST_LOOP_TEST_PATHS: tuple[Path, ...] = (
    Path("tests/infra_tests/git_hook_smoke"),
    Path("tests/infra_tests/core/test_pytest_orchestration.py"),
    Path("tests/infra_tests/core/test_pipeline.py"),
)

_REPO_ROOT = Path(__file__).resolve().parents[3]


def test_fast_loop_manifest_is_non_empty_and_exists() -> None:
    assert FAST_LOOP_TEST_PATHS, "fast-loop manifest must not be empty"
    for relative_path in FAST_LOOP_TEST_PATHS:
        assert (_REPO_ROOT / relative_path).exists(), f"fast-loop entry missing on disk: {relative_path}"


@pytest.mark.timeout(600)
@pytest.mark.parametrize(
    "relative_path",
    FAST_LOOP_TEST_PATHS,
    ids=[str(path) for path in FAST_LOOP_TEST_PATHS],
)
def test_fast_loop_entry_still_collects(relative_path: Path) -> None:
    """A real pytest subprocess must collect at least one item per entry.

    If a fast-loop module is renamed, deleted, or fails to import, the
    documented loop would either error (good) or silently run nothing (bad);
    this test pins the non-vacuous case by checking collection counts.
    """
    command = [
        sys.executable,
        "-m",
        "pytest",
        str(_REPO_ROOT / relative_path),
        "--collect-only",
        "-q",
        "-p",
        "no:cacheprovider",
        "--timeout=600",
    ]
    result = subprocess.run(
        command,
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=540,
        check=False,
    )
    assert result.returncode == 0, (
        f"collection failed for {relative_path}:\n{result.stdout[-2000:]}\n{result.stderr[-2000:]}"
    )
    counts = [
        int(match.group(1))
        for match in (re.search(r"(\d+) tests? collected", line) for line in result.stdout.splitlines())
        if match
    ]
    assert counts and counts[0] >= 1, f"fast-loop entry {relative_path} collected 0 tests: {result.stdout[-500:]}"
