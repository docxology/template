"""Untrusted actual receipt bytes cannot authorize native slide child tools."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pytest

from infrastructure.reporting.native_projection_contracts import ProjectionSourceUnsupported
from infrastructure.reporting.native_slide_control_adapter import (
    replay_slide_source_controls,
    supervise_slide_source_controls,
)
from infrastructure.reporting.native_slide_controls import SLIDE_CONTROL_CODES
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def test_slide_supervisor_refuses_before_launch_without_its_live_source_owner(tmp_path: Path) -> None:
    directory = tmp_path / "output/readiness/controls"
    with pytest.raises(ValueError, match="actual live Source/tool owner"):
        supervise_slide_source_controls(
            tmp_path,
            directory,
            scope="templates/template_code_project",
            interpreter=Path(sys.executable),
            env={},
            deadline=time.monotonic() + 10,
            run_id="untrusted-slide-data",
        )
    assert not directory.exists()
    assert list(tmp_path.iterdir()) == []


def test_retained_control_exit_data_never_constructs_original_slide_authority(tmp_path: Path) -> None:
    # Complete names and plausible exit fields are still untrusted DATA. Read
    # actual serialized bytes through SnapshotReader without a live custodian.
    records = [
        {"name": name, "original_exit_code": 0 if code is None else 1} for name, code in SLIDE_CONTROL_CODES.items()
    ]
    receipt_relative = "tests/slide-control-receipt.json"
    receipt = tmp_path / receipt_relative
    receipt.parent.mkdir()
    receipt.write_text(json.dumps({"records": records}), encoding="utf-8")
    reader = SnapshotReader(tmp_path)
    actual = reader.read(receipt_relative).json_object()["records"]
    deadline = time.monotonic() + 10
    with pytest.raises(ProjectionSourceUnsupported):
        replay_slide_source_controls(
            actual,
            reader,
            tmp_path / "output/readiness/controls",
            scope="templates/template_code_project",
            run_id="untrusted-slide-data",
            custody={},
            runtime={},
            versions={},
            original_deadline=deadline,
            deadline=deadline,
            env={},
        )
    assert not (tmp_path / "output").exists()
    assert reader.unchanged()
