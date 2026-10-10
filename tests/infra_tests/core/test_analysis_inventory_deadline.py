"""Actual bounded discovery and subprocess consumption of an existing clock."""

import sys
import time
from pathlib import Path

import pytest

from infrastructure.core.pipeline.artifacts._inventory import (
    _git_ignore_matches,
    collect_stable_output_inventory,
    iter_bounded_tree_paths,
)


def test_expired_original_inventory_clock_refuses_before_discovery(tmp_path: Path) -> None:
    (tmp_path / "body.txt").write_text("actual")
    deadline = time.monotonic() - 1
    with pytest.raises(TimeoutError, match="existing original deadline"):
        list(iter_bounded_tree_paths(tmp_path, max_paths=100, original_deadline=deadline))
    with pytest.raises(TimeoutError, match="existing original deadline"):
        collect_stable_output_inventory(tmp_path, max_snapshot_paths=100, original_deadline=deadline)


def test_real_native_query_uses_remaining_original_clock_instead_of_fresh_30_seconds(tmp_path: Path) -> None:
    body = tmp_path / "body.txt"
    body.write_text("actual")
    started = time.monotonic()
    with pytest.raises(TimeoutError, match="existing original deadline"):
        _git_ignore_matches(
            (body,),
            tmp_path,
            command=(sys.executable, "-I", "-c", "import time; time.sleep(5)"),
            original_deadline=started + 0.05,
        )
    assert time.monotonic() - started < 2
