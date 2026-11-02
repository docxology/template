"""Independently reaped OS facts survive real post-process retention failure."""

import os
import json
import subprocess
import sys
import textwrap
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


def _actual_diagnostic_probe(tmp_path: Path, mode: str, enabled: bool) -> subprocess.CompletedProcess[str]:
    program = textwrap.dedent("""
        import json, os, sys, time
        from contextlib import nullcontext
        from pathlib import Path
        from infrastructure.reporting.native_original_progress import _representative_preflight_diagnostics
        from infrastructure.reporting.native_tool_process import run_native_tool_process
        directory = Path(sys.argv[1]).resolve(strict=True)
        mode = sys.argv[2]
        deadline = time.monotonic() + (-1 if mode == "expired" else 120)
        context = _representative_preflight_diagnostics(deadline) if sys.argv[3] == "yes" else nullcontext()
        facts = []
        record = directory / "original-native-worker.native-process.json"
        code = "import os,sys;print(os.getpid(),flush=True);sys.exit(int(sys.argv[1]))"
        arguments = ["-I", "-B", "-c", code, "17" if mode == "nonzero" else "0"]
        if mode == "retention-failure":
            code = "import os,sys;os.mkdir(sys.argv[1]);print(os.getpid(),flush=True);sys.exit(17)"
            arguments = ["-I", "-B", "-c", code, str(record)]
        with context:
            try:
                result = run_native_tool_process(
                    directory, "absent-native-diagnostic-tool" if mode == "missing" else sys.executable,
                    arguments, cwd=directory, env=dict(os.environ), deadline=deadline,
                    purpose="original-native-worker", observed_processes=facts,
                )
            except FileExistsError:
                assert mode == "retention-failure"
                result = {"retention_failed": True, "facts": facts}
            except TimeoutError:
                assert mode == "expired"
                result = {"expired": True, "facts": facts}
        stream = directory / "original-native-worker.stdout.bin"
        raw = stream.read_text() if stream.exists() else ""
        print(json.dumps({"result": result, "deadline": deadline, "actual_pid": int(raw) if raw else None}))
    """)
    return subprocess.run(
        [sys.executable, "-B", "-c", program, str(tmp_path), mode, "yes" if enabled else "no"],
        cwd=Path(__file__).resolve().parents[3],
        capture_output=True,
        text=True,
        timeout=150,
        check=False,
    )


@pytest.mark.skipif(os.name != "posix", reason="genuine native guardian and owned POSIX subprocesses")
@pytest.mark.parametrize("enabled", [False, True])
@pytest.mark.parametrize("mode,expected_code", [("zero", 0), ("nonzero", 17)])
@pytest.mark.timeout(180)
def test_diagnostics_observe_actual_popen_and_preserve_original_cleanup(
    tmp_path: Path,
    enabled: bool,
    mode: str,
    expected_code: int,
) -> None:
    completed = _actual_diagnostic_probe(tmp_path, mode, enabled)
    assert completed.returncode == 0, completed.stderr
    data = json.loads(completed.stdout)
    result = data["result"]
    assert result["original_exit_code"] == expected_code and result["timed_out"] is False
    assert result["pid"] == data["actual_pid"] and result["accepted"] is True
    assert result["cleanup"]["root_reaped"] is True
    assert result["cleanup"]["guardian_armed"] is True
    assert result["cleanup"]["guardian_finished"] is True
    assert result["cleanup"]["final_token_sweep_matched_pids"] == []
    rows = [json.loads(line) for line in completed.stderr.splitlines()]
    if not enabled:
        assert rows == []
        return
    phases = [row["phase"] for row in rows if row["schema_version"] == "template-native-original-progress-v1"]
    expected = [
        "streams-open-begin",
        "streams-open-end",
        "nomination-begin",
        "nomination-end",
        "guardian-start",
        "guardian-ready",
        "environment-begin",
        "environment-end",
        "worker-popen-begin",
        "worker-popen-returned",
        "arm-begin",
        "arm-end",
        "wait-begin",
        "wait-end",
        "cleanup-begin",
        "cleanup-end",
        "retention-begin",
        "retention-end",
    ]
    assert [phase for phase in phases if phase not in {"diagnostics-start", "diagnostics-stop"}] == expected
    child = next(row for row in rows if row["phase"] == "worker-popen-returned")
    guardian = next(row for row in rows if row["phase"] == "guardian-ready")
    assert child["pid"] == data["actual_pid"]
    assert guardian["pid"] == result["cleanup"]["guardian_pid"]
    for row in rows:
        assert row["observed_monotonic"] + row["remaining_seconds"] == data["deadline"]
    assert str(tmp_path) not in completed.stderr and "sys.exit" not in completed.stderr


@pytest.mark.skipif(os.name != "posix", reason="genuine native nomination and retention failures")
@pytest.mark.parametrize("mode", ["missing", "retention-failure"])
@pytest.mark.timeout(180)
def test_diagnostics_do_not_invent_pid_or_replace_real_retention_failure(tmp_path: Path, mode: str) -> None:
    completed = _actual_diagnostic_probe(tmp_path, mode, True)
    assert completed.returncode == 0, completed.stderr
    data = json.loads(completed.stdout)
    result = data["result"]
    rows = [json.loads(line) for line in completed.stderr.splitlines()]
    if mode == "missing":
        assert result["pid"] is None and result["original_exit_code"] is None and result["accepted"] is False
        assert not any(row["phase"] in {"worker-popen-returned", "guardian-ready"} for row in rows)
    else:
        assert result["retention_failed"] is True
        assert result["facts"][0]["original_exit_code"] == 17
        observed = next(row for row in rows if row["phase"] == "worker-popen-returned")
        assert observed["pid"] == result["facts"][0]["pid"] == data["actual_pid"]
        assert not any(row["phase"] == "retention-end" for row in rows)


def test_actual_expired_native_clock_is_not_renewed_by_diagnostics(tmp_path: Path) -> None:
    completed = _actual_diagnostic_probe(tmp_path, "expired", True)
    assert completed.returncode == 0, completed.stderr
    data = json.loads(completed.stdout)
    assert data["result"] == {"expired": True, "facts": []}
    assert data["actual_pid"] is None
    assert completed.stderr == "" and list(tmp_path.iterdir()) == []
