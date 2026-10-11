"""Scientific Office receipt shape never constructs actual original custody."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from infrastructure.reporting.native_office_scientific_controls import CONTROL_CODES, run_office_scientific_controls
from infrastructure.reporting.native_office_scientific_replay import replay_office_scientific_controls
from infrastructure.reporting.native_print_child_custody import OfficeScientificControlReaderOperation
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


@pytest.mark.parametrize("kind", ["docx", "epub"])
@pytest.mark.parametrize("mutation", ["missing", "duplicate", "reordered"])
def test_incomplete_scientific_suite_refuses_before_receipt_admission(tmp_path: Path, kind: str, mutation: str) -> None:
    names = list(CONTROL_CODES)
    if mutation == "missing":
        names.pop()
    elif mutation == "duplicate":
        names[-1] = names[0]
    else:
        names.reverse()
    deadline = time.monotonic() + 10
    with pytest.raises(ValueError, match="omitted|missing, duplicated or reordered"):
        replay_office_scientific_controls(
            tmp_path,
            tmp_path / "output/readiness/scientific",
            kind,
            [{"name": name} for name in names],
            SnapshotReader(tmp_path),
            scope="templates/template_code_project",
            source=None,
            run_id="0" * 32,
            custody={},
            runtime={},
            versions={},
            original_deadline=deadline,
            deadline=deadline,
            env={},
        )


@pytest.mark.parametrize("kind", ["docx", "epub"])
def test_scientific_producer_cannot_launch_without_actual_source_owner(tmp_path: Path, kind: str) -> None:
    leaf = tmp_path / "scientific"
    with pytest.raises(ValueError, match="actual genuine Source/ToolAPI owner/run/clock"):
        run_office_scientific_controls(
            tmp_path,
            leaf,
            kind,
            reader=SnapshotReader(tmp_path),
            env={},
            deadline=time.monotonic() + 10,
            run_id="0" * 32,
        )
    assert not leaf.exists()


def test_serialized_scientific_records_cannot_construct_original_capability(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="genuine unwrapped"):
        OfficeScientificControlReaderOperation(
            None,
            SnapshotReader(tmp_path),
            [{"name": name, "original_exit_code": int(code is not None)} for name, code in CONTROL_CODES.items()],
            scope="templates/template_code_project",
            run_id="0" * 32,
            deadline=time.monotonic() + 10,
        )


def test_scientific_reader_subclass_cannot_select_original_child_role(tmp_path: Path) -> None:
    class CallerSelectedRole(OfficeScientificControlReaderOperation):
        schema = "template-source-owned-print-child-v1"

    with pytest.raises(ValueError, match="exact Source-owned concrete reader type"):
        CallerSelectedRole(
            None,
            SnapshotReader(tmp_path),
            [],
            scope="templates/template_code_project",
            run_id="0" * 32,
            deadline=time.monotonic() + 10,
        )
