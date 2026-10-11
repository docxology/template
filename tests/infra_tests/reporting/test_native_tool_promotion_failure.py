"""Independently reaped OS facts survive real post-process retention failure."""

import os
import sys
import time
from pathlib import Path

import pytest

from infrastructure.reporting.native_tool_process import run_native_tool_process


@pytest.mark.skipif(os.name != "posix", reason="the existing native supervisor owns POSIX process groups")
@pytest.mark.parametrize("original_code", [0, 17, 124, 130])
def test_actual_reaped_code_survives_final_record_open_failure(tmp_path: Path, original_code: int) -> None:
    directory = tmp_path / "actual-tool"
    directory.mkdir()
    purpose = "retention-fault"
    record = directory / f"{purpose}.native-process.json"
    facts: list[dict] = []
    # The actual child creates this collision only after the supervisor's
    # fresh-path check. No process, exit, guardian, stream or Source owner is
    # mocked; the final exclusive record open must fail after actual reap.
    command = "import os,sys;os.mkdir(sys.argv[1]);sys.exit(int(sys.argv[2]))"
    with pytest.raises(FileExistsError):
        run_native_tool_process(
            directory,
            sys.executable,
            ["-I", "-B", "-c", command, str(record), str(original_code)],
            cwd=tmp_path,
            env=dict(os.environ),
            deadline=time.monotonic() + 120,
            purpose=purpose,
            observed_processes=facts,
        )
    assert record.is_dir()
    assert len(facts) == 1
    observed = facts[0]
    assert observed["owner_pid"] == os.getpid()
    assert type(observed["pid"]) is int and observed["pid"] != os.getpid()
    assert observed["original_exit_code"] == original_code
    assert observed["timed_out"] is False
    assert observed["command"][-2:] == [str(record), str(original_code)]
    # Partial DATA contains neither an artifact nor completion authority.
    assert "accepted" not in observed and "artifact" not in observed


def test_invalid_observation_sink_refuses_before_evidence_io(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="observation sink"):
        run_native_tool_process(
            tmp_path,
            sys.executable,
            ["-c", "raise SystemExit(0)"],
            cwd=tmp_path,
            env=dict(os.environ),
            deadline=time.monotonic() + 120,
            purpose="invalid-sink",
            observed_processes={},  # type: ignore[arg-type]
        )
    assert list(tmp_path.iterdir()) == []
