"""Actual phase pipes, strict launch admission and original child outcomes."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import asdict, replace
from pathlib import Path

import pytest

from infrastructure.core._bounded_run_guardian import (
    DEFAULT_GUARDIAN_STARTUP_TIMEOUT_SECONDS,
    _READY,
    _effective_startup_deadline,
    _expect_status,
    _start_wait_timeout,
    start_bounded_run_guardian,
)
from infrastructure.core.execution_boundary import build_bounded_env, run_bounded_subprocess
from infrastructure.core.subprocess_policy import (
    SubprocessPolicy,
    SubprocessPolicyRecord,
    run_with_policy,
    validate_policy_inventory,
)
from infrastructure.publishing.release.release_receipts import (
    SubprocessPolicyReceipt,
    build_subprocess_policy_receipt,
    receipt_digest,
)
from infrastructure.reporting.suite_runner import run_pytest_stream, _stream_arming_failure

# Real private imports, source admission and mandatory cleanup consume this
# finite harness allowance; runtime acceptance uses the unchanged run budget.
pytestmark = pytest.mark.timeout(240)
_INVALID = [True, False, float("nan"), float("inf"), float("-inf"), 0, -1, "60", None]


@pytest.mark.parametrize("field", ["timeout_seconds", "guardian_startup_timeout_seconds"])
@pytest.mark.parametrize("value", _INVALID)
def test_policy_invalid_budget_refuses_real_launch_and_inventory(tmp_path: Path, field: str, value) -> None:
    marker = tmp_path / "must-not-execute"
    policy = replace(
        SubprocessPolicy("owned-invalid", "infrastructure/core/subprocess_policy.py", 180),
        **{field: value},
    )
    command = [sys.executable, "-I", "-c", f"from pathlib import Path;Path({str(marker)!r}).write_text('executed')"]
    with pytest.raises(ValueError, match="positive finite"):
        run_with_policy(command, cwd=tmp_path, env={}, policy=policy)
    with pytest.raises(ValueError, match="positive finite"):
        SubprocessPolicyRecord.from_policy(policy)
    assert validate_policy_inventory((policy,))
    assert not marker.exists()


@pytest.mark.parametrize("field", ["timeout", "guardian_startup_timeout_seconds"])
@pytest.mark.parametrize("value", _INVALID)
def test_boundary_invalid_budget_refuses_before_executable(tmp_path: Path, field: str, value) -> None:
    marker = tmp_path / "must-not-execute"
    options = {"timeout": 180, "guardian_startup_timeout_seconds": 60} | {field: value}
    with pytest.raises(ValueError, match="positive finite"):
        run_bounded_subprocess(
            [sys.executable, "-I", "-c", f"from pathlib import Path;Path({str(marker)!r}).write_text('executed')"],
            cwd=tmp_path,
            env=build_bounded_env(),
            **options,
        )
    assert not marker.exists()


@pytest.mark.parametrize("field", ["timeout_seconds", "guardian_startup_timeout_seconds"])
@pytest.mark.parametrize("value", _INVALID)
def test_stream_invalid_budget_refuses_before_executable(tmp_path: Path, field: str, value) -> None:
    marker = tmp_path / "must-not-execute"
    options = {"timeout_seconds": 180, "guardian_startup_timeout_seconds": 60} | {field: value}
    with pytest.raises(ValueError, match="positive.*finite"):
        run_pytest_stream(
            [sys.executable, "-I", "-c", f"from pathlib import Path;Path({str(marker)!r}).write_text('executed')"],
            tmp_path,
            build_bounded_env(),
            quiet=True,
            **options,
        )
    assert not marker.exists()


def test_policy_public_record_binds_phase_budget_and_refuses_invalid_record() -> None:
    policy = SubprocessPolicy(
        "owned-budget", "infrastructure/core/subprocess_policy.py", 180, guardian_startup_timeout_seconds=45
    )
    record = SubprocessPolicyRecord.from_policy(policy)
    assert asdict(record)["guardian_startup_timeout_seconds"] == 45
    first = SubprocessPolicyReceipt((record,))
    second = SubprocessPolicyReceipt((replace(record, guardian_startup_timeout_seconds=60),))
    assert first.validate() == second.validate() == []
    assert receipt_digest(first) != receipt_digest(second)
    for field in ("timeout_seconds", "guardian_startup_timeout_seconds"):
        for invalid in _INVALID:
            assert SubprocessPolicyReceipt((replace(record, **{field: invalid}),)).validate()


@pytest.mark.parametrize("field", ["timeout_seconds", "guardian_startup_timeout_seconds"])
def test_actual_invocation_policy_error_exits_two_before_child(tmp_path: Path, field: str) -> None:
    """An owned CLI catches the actual canonical admission error, without replacing it."""
    import infrastructure

    selected = Path(infrastructure.__file__).resolve().parent.parent
    marker = tmp_path / "must-not-execute"
    body = r"""
import json,sys
from pathlib import Path
sys.path.insert(0,sys.argv.pop(1))
from infrastructure.core.subprocess_policy import SubprocessPolicy,run_with_policy
options=json.loads(sys.argv.pop(1))
marker=Path(sys.argv.pop(1))
try:
    policy=SubprocessPolicy('owned-cli','infrastructure/core/subprocess_policy.py',**options)
    command=[sys.executable,'-I','-c',f"from pathlib import Path;Path({str(marker)!r}).write_text('executed')"]
    run_with_policy(command,cwd=Path.cwd(),env={},policy=policy)
except ValueError as exc:
    print(str(exc),file=sys.stderr)
    raise SystemExit(2)
raise SystemExit(99)
"""
    options = {"timeout_seconds": 180, "guardian_startup_timeout_seconds": 60} | {field: True}
    completed = subprocess.run(
        [sys.executable, "-I", "-c", body, str(selected), json.dumps(options), str(marker)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 2, (completed.stdout, completed.stderr)
    assert "positive finite" in completed.stderr and not marker.exists()


@pytest.mark.skipif(os.name == "nt", reason="guardian status pipe is POSIX-only")
@pytest.mark.parametrize("short_outer", [False, True])
def test_slow_ready_real_pipe_obeys_phase_and_original_deadline(tmp_path: Path, short_outer: bool) -> None:
    """A real delayed READY exercises the same protocol helper, without cleanup claims."""
    reader, writer = os.pipe()
    started = tmp_path / "real-writer-started"
    sender = subprocess.Popen(
        [
            sys.executable,
            "-I",
            "-c",
            "import os,sys,time;from pathlib import Path;Path(sys.argv[2]).write_text('started');"
            "time.sleep(.25);os.write(int(sys.argv[1]),b'R')",
            str(writer),
            str(started),
        ],
        cwd=tmp_path,
        pass_fds=(writer,),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    os.close(writer)
    try:
        start = time.monotonic()
        # The admitted phase clock can be larger than the original clock;
        # min chooses the original, with no fresh ten-second allowance.
        phase = start + 2
        original = start + (0.04 if short_outer else 3)
        deadline = _effective_startup_deadline(phase, original)
        if short_outer:
            with pytest.raises(TimeoutError):
                _expect_status(reader, _READY, timeout=_start_wait_timeout(deadline), deadline_monotonic=deadline)
            assert time.monotonic() - start < 1.5
        else:
            _expect_status(reader, _READY, timeout=_start_wait_timeout(deadline), deadline_monotonic=deadline)
            assert time.monotonic() - start >= 0.2
        sender.wait(timeout=5)
        assert sender.returncode == 0 and started.read_text() == "started"
    finally:
        os.close(reader)
        if sender.poll() is None:
            sender.kill()
            sender.wait(timeout=5)


def test_original_and_phase_clock_are_not_reset_at_arming() -> None:
    now = time.monotonic()
    phase = now + 0.02
    assert _effective_startup_deadline(phase, now + 60) == phase
    assert _effective_startup_deadline(now + 60, phase) == phase
    assert _start_wait_timeout(now + 60) > 10
    with pytest.raises(TimeoutError):
        _start_wait_timeout(_effective_startup_deadline(now - 1, now + 60))
    assert DEFAULT_GUARDIAN_STARTUP_TIMEOUT_SECONDS == 60


@pytest.mark.parametrize("short_phase", [False, True])
def test_actual_boundary_short_budget_refuses_before_command(tmp_path: Path, short_phase: bool) -> None:
    marker = tmp_path / "must-not-execute"
    result = run_bounded_subprocess(
        [sys.executable, "-I", "-c", f"from pathlib import Path;Path({str(marker)!r}).write_text('executed')"],
        cwd=tmp_path,
        env=build_bounded_env(),
        timeout=180 if short_phase else 1e-7,
        guardian_startup_timeout_seconds=1e-7 if short_phase else 60,
    )
    assert result.returncode == 124 and result.timed_out
    assert result.original_returncode is None and not result.custody_refused
    assert "before" in result.command_error and not marker.exists()


def test_actual_stream_short_outer_refuses_before_command(tmp_path: Path) -> None:
    marker = tmp_path / "must-not-execute"
    code, stdout, stderr = run_pytest_stream(
        [sys.executable, "-I", "-c", f"from pathlib import Path;Path({str(marker)!r}).write_text('executed')"],
        tmp_path,
        build_bounded_env(),
        quiet=True,
        timeout_seconds=1e-7,
    )
    assert code == 124 and not stdout and "before command launch" in stderr
    assert not marker.exists()


@pytest.mark.parametrize("original", [0, 2, 7])
def test_actual_child_original_code_survives_phase_budget(tmp_path: Path, original: int) -> None:
    marker = tmp_path / "actually-executed"
    result = run_with_policy(
        [
            sys.executable,
            "-I",
            "-c",
            f"from pathlib import Path;Path({str(marker)!r}).write_text('executed');raise SystemExit({original})",
        ],
        cwd=tmp_path,
        env=build_bounded_env(),
        policy=SubprocessPolicy("owned-original", "infrastructure/core/subprocess_policy.py", 180),
    )
    assert marker.read_text() == "executed"
    assert result.returncode == result.original_returncode == original
    assert not result.timed_out and not result.custody_refused and not result.command_error


@pytest.mark.parametrize("field", ["timeout_seconds", "guardian_startup_timeout_seconds"])
def test_builder_blocks_complete_actual_invalid_inventory(field: str) -> None:
    valid = SubprocessPolicy("owned-valid", "infrastructure/core/subprocess_policy.py", 180)
    invalid = replace(valid, policy_id="owned-invalid", **{field: float("nan")})
    receipt = build_subprocess_policy_receipt(policies=(valid, invalid))
    assert receipt.status == "blocked" and receipt.policies == ()
    assert "owned-invalid" in receipt.skip_reason
    assert "positive finite" in receipt.skip_reason
    assert receipt.validate() == []
    passing = build_subprocess_policy_receipt(policies=(valid,))
    assert passing.status == "pass" and len(passing.policies) == 1


@pytest.mark.parametrize("original", [0, 2, 7, 130])
def test_actual_stream_preserves_original_child_policy(tmp_path: Path, original: int) -> None:
    marker = tmp_path / "actual-stream-executed"
    code, stdout, stderr = run_pytest_stream(
        [
            sys.executable,
            "-I",
            "-c",
            f"from pathlib import Path;Path({str(marker)!r}).write_text('executed');raise SystemExit({original})",
        ],
        tmp_path,
        build_bounded_env(),
        quiet=True,
        timeout_seconds=180,
    )
    assert marker.read_text() == "executed" and code == original
    assert not stdout and not stderr


@pytest.mark.skipif(os.name == "nt", reason="actual stopped guardian and detached POSIX session")
@pytest.mark.parametrize("outcome", ["timeout", "interrupted-child", "supervisor-interruption"])
def test_actual_unarmed_guardian_cleanup_sweeps_reparented_token_holders(tmp_path: Path, outcome: str) -> None:
    """Exercise the production ARM failure helper with actual owned live processes.

    This is an ARM helper control, not a forced full-stream scheduling race.
    """
    import contextlib
    import signal
    from infrastructure.core.execution_boundary import build_bounded_run_env, terminate_bounded_run_processes

    env, token = build_bounded_run_env(build_bounded_env())
    detached_pid_path = tmp_path / "actual-detached.pid"
    detached_started = tmp_path / "actual-detached-started"
    root_pid_path = tmp_path / "actual-root.pid"
    body = (
        "import os,sys,time;from pathlib import Path;"
        "Path(sys.argv[1]).write_text(str(os.getpid()));"
        "Path(sys.argv[2]).write_text('actual');time.sleep(60)"
    )
    root_body = (
        "import os,subprocess,sys,time;from pathlib import Path;"
        "Path(sys.argv[4]).write_text(str(os.getpid()));"
        "subprocess.Popen([sys.executable,'-I','-c',sys.argv[1],sys.argv[2],sys.argv[3]],"
        "start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);"
        "raise SystemExit(130)"
        if outcome == "interrupted-child"
        else "import os,subprocess,sys,time;from pathlib import Path;"
        "Path(sys.argv[4]).write_text(str(os.getpid()));"
        "subprocess.Popen([sys.executable,'-I','-c',sys.argv[1],sys.argv[2],sys.argv[3]],"
        "start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(60)"
    )
    guardian = start_bounded_run_guardian(build_bounded_env(), deadline_monotonic=time.monotonic() + 180)
    assert guardian is not None
    process = None
    detached_pid = None
    try:
        assert guardian.cache is not None
        cache = Path(guardian.cache.name).resolve()
        os.kill(guardian.process.pid, signal.SIGSTOP)
        process = subprocess.Popen(
            [
                sys.executable,
                "-I",
                "-c",
                root_body,
                body,
                str(detached_pid_path),
                str(detached_started),
                str(root_pid_path),
            ],
            cwd=tmp_path,
            env=env,
            start_new_session=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        observer = time.monotonic() + 15
        while not detached_started.exists() and time.monotonic() < observer:
            time.sleep(0.01)
        assert root_pid_path.read_text() == str(process.pid)
        assert detached_started.read_text() == "actual"
        detached_pid = int(detached_pid_path.read_text())
        os.kill(detached_pid, 0)
        before = subprocess.run(
            ["ps", "-o", "stat=", "-p", str(detached_pid)],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        assert before.returncode == 0 and before.stdout.strip() and not before.stderr.strip()
        assert not before.stdout.strip().startswith("Z"), "positive live control is already a zombie"
        if outcome == "interrupted-child":
            assert process.wait(timeout=5) == 130
            parent = subprocess.run(
                ["ps", "-o", "ppid=", "-p", str(detached_pid)],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            assert parent.returncode == 0 and not parent.stderr.strip()
            assert int(parent.stdout.strip()) != process.pid, "detached child has not been reparented"
        try:
            guardian.arm(root_pid=process.pid, run_token=token, deadline_monotonic=time.monotonic() - 1)
        except TimeoutError as expired:
            original = (
                KeyboardInterrupt("owned supervisor interruption") if outcome == "supervisor-interruption" else expired
            )
        else:
            raise AssertionError("expired ARM budget unexpectedly bound guardian")
        if outcome == "supervisor-interruption":
            with pytest.raises(KeyboardInterrupt) as raised:
                _stream_arming_failure(process, guardian, token, original)
            assert raised.value is original
        else:
            code, _, notes = _stream_arming_failure(process, guardian, token, original)
            assert code == (130 if outcome == "interrupted-child" else 124)
            assert "arming" in notes
        assert process.poll() is not None and guardian.process.poll() is not None
        assert not cache.exists()
        observed = subprocess.run(
            ["ps", "-o", "stat=", "-p", str(detached_pid)],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        state = observed.stdout.strip()
        absent = observed.returncode == 1 and not state and not observed.stderr.strip()
        zombie = observed.returncode == 0 and state.startswith("Z") and not observed.stderr.strip()
        assert absent or zombie, (observed.returncode, observed.stdout, observed.stderr)
    finally:
        try:
            guardian.close()
        finally:
            try:
                terminate_bounded_run_processes(token)
            finally:
                if process is not None:
                    with contextlib.suppress(ProcessLookupError):
                        os.kill(process.pid, signal.SIGKILL)
                    process.wait(timeout=5)
                if detached_pid is not None:
                    with contextlib.suppress(ProcessLookupError):
                        os.kill(detached_pid, signal.SIGKILL)


def test_builder_empty_inventory_is_blocked_not_pass() -> None:
    receipt = build_subprocess_policy_receipt(policies=())
    assert receipt.status == "blocked" and receipt.policies == ()
    assert "MISSING-POLICY-INVENTORY" in receipt.skip_reason
    assert receipt.validate() == []
