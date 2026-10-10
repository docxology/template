"""The fixed native route preserves ordinary supervision and refuses DATA owners."""

import os
import time
from pathlib import Path

import pytest

from infrastructure.core.pipeline.native_stage_launch import launch_owned_native_stage
from infrastructure.core.pipeline.outcomes import StageStatus
from infrastructure.reporting.native_analysis_stage_replay import authenticate_analysis_stage_child
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from tests.infra_tests.core.test_execution_contract import _executor


@pytest.mark.skipif(os.name != "posix", reason="existing stage guardian owns POSIX process groups")
@pytest.mark.parametrize(
    ("original_code", "status"),
    [
        (0, StageStatus.SUCCEEDED),
        (17, StageStatus.FAILED),
        (124, StageStatus.TIMED_OUT),
        (130, StageStatus.INTERRUPTED),
    ],
)
def test_actual_ordinary_stage_retains_script_exit_without_native_owner(
    tmp_path: Path, original_code: int, status: StageStatus
) -> None:
    executor = _executor(tmp_path, f"raise SystemExit({original_code})\n")
    outcome = executor._run_script("scripts/child.py")
    assert outcome.status is status and outcome.child_exit_code == original_code
    assert not (tmp_path / "output/readiness").exists()


def test_environment_nomination_cannot_select_native_launch_or_open_request(tmp_path: Path) -> None:
    missing = tmp_path / "missing.json"
    result = launch_owned_native_stage(
        tmp_path,
        tmp_path / "projects/templates/template_code_project",
        missing,
        {"TEMPLATE_NATIVE_STAGE_PACKET": '{"status":"pass"}'},
        deadline=time.monotonic() + 30,
    )
    assert result is None and not missing.exists()
    assert list(tmp_path.iterdir()) == []


def test_serialized_stage_chain_cannot_authenticate_analysis_before_io(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="genuine fixed Original/current stage-chain reader"):
        authenticate_analysis_stage_child(
            None,  # type: ignore[arg-type]
            "templates/template_code_project",
            {"native_stage_child": {"path": "missing.json", "sha256": "a" * 64}},
            SnapshotReader(tmp_path),
            {"status": "pass"},  # type: ignore[arg-type]
            deadline=time.monotonic() + 30,
        )
    assert list(tmp_path.iterdir()) == []
