"""Reader controls refuse unavailable clocks before interpreting retained data."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from infrastructure.reporting.native_format_browser_replay import (
    replay_browser_controls,
)
from infrastructure.reporting.native_format_browser_semantic_replay import (
    replay_semantic_control,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def test_control_replay_requires_caller_deadline(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="finite clock"):
        replay_browser_controls(
            tmp_path,
            tmp_path,
            [],
            SnapshotReader(tmp_path),
            run_id="control",
            custody={},
            runtime={},
        )


@pytest.mark.parametrize("semantic", [False, True])
def test_control_replay_refuses_expired_clock_before_artifact_access(tmp_path: Path, semantic: bool) -> None:
    deadline = time.monotonic() - 1
    with pytest.raises(TimeoutError):
        if semantic:
            replay_semantic_control(
                tmp_path,
                tmp_path,
                {},
                SnapshotReader(tmp_path),
                run_id="control",
                custody={},
                runtime={},
                deadline=deadline,
                env={},
            )
        else:
            replay_browser_controls(
                tmp_path,
                tmp_path,
                [],
                SnapshotReader(tmp_path),
                run_id="control",
                custody={},
                runtime={},
                deadline=deadline,
                env={},
            )
