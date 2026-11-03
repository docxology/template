"""Real diagnostic I/O preserves the original clock and confines emitted data."""

from __future__ import annotations

from contextlib import redirect_stderr
from io import StringIO
import json
import os
import subprocess
import sys
import textwrap
import time
from pathlib import Path

import pytest

from infrastructure.reporting.native_original_progress import original_cell_progress

SCOPE = "templates/template_code_project"


def test_original_progress_reports_expired_clock_without_granting_or_renewing_it(
    capsys: pytest.CaptureFixture[str],
) -> None:
    deadline = time.monotonic() - 1
    for phase in ("selection-start", "worker-start", "worker-completed", "terminal-observed"):
        original_cell_progress(phase, SCOPE, deadline)
    captured = capsys.readouterr()
    assert not captured.out
    rows = [json.loads(line) for line in captured.err.splitlines()]
    assert len(rows) == 4
    for row in rows:
        assert set(row) == {"schema_version", "phase", "scope", "pid", "observed_monotonic", "remaining_seconds"}
        assert row["schema_version"] == "template-native-original-progress-v1"
        assert row["scope"] == SCOPE and row["pid"] == os.getpid()
        assert row["remaining_seconds"] < 0
        assert row["observed_monotonic"] + row["remaining_seconds"] == deadline


@pytest.mark.parametrize(
    "phase,scope,deadline",
    [
        ("unknown", SCOPE, 1.0),
        ("worker-start", "working/private", 1.0),
        ("worker-start", SCOPE + "\nprivate", 1.0),
        ("worker-start", SCOPE, float("nan")),
        ("worker-start", SCOPE, True),
    ],
)
def test_original_progress_refuses_unbounded_labels_or_clock_before_output(
    capsys: pytest.CaptureFixture[str], phase: str, scope: str, deadline: float
) -> None:
    with pytest.raises(ValueError, match="fixed public phase/scope"):
        original_cell_progress(phase, scope, deadline)
    captured = capsys.readouterr()
    assert captured.out == captured.err == ""


def test_real_closed_diagnostic_stream_does_not_replace_original_failure() -> None:
    stream = StringIO()
    stream.close()
    with redirect_stderr(stream):
        original_cell_progress("terminal-observed", SCOPE, time.monotonic() - 1)


_PRELUDE = """
import json, os, threading, time
from infrastructure.reporting.native_original_progress import (
    _CONTEXT, _PHASES, _preflight_phase, _representative_preflight_diagnostics,
    original_cell_progress,
)
"""


def _probe(program: str, *, stderr: int = subprocess.PIPE, timeout: float = 15) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-B", "-c", _PRELUDE + textwrap.dedent(program)],
        cwd=Path(__file__).resolve().parents[3],
        stdout=subprocess.PIPE,
        stderr=stderr,
        text=True,
        timeout=timeout,
        check=False,
    )


def test_real_representative_context_bounds_labels_count_bytes_and_clock() -> None:
    result = _probe("""
        deadline = time.monotonic() + 20
        with _representative_preflight_diagnostics(deadline):
            for repeat in range(1000):
                _preflight_phase("source-admission-begin", deadline)
            _preflight_phase("private-secret-name", deadline)
            _preflight_phase("source-admission-end", deadline + 1)
            _preflight_phase("worker-popen-returned", deadline)
            _preflight_phase("guardian-ready", deadline, pid=-1)
            _preflight_phase("wait-end", deadline, pid=os.getpid())
            original_cell_progress("worker-start", "templates/template_code_project", deadline)
            print(json.dumps({"deadline": deadline, "pid": os.getpid()}))
        assert not any(thread.name.startswith("native-preflight-") for thread in threading.enumerate())
    """)
    assert result.returncode == 0, result.stderr
    held = json.loads(result.stdout)
    rows = [json.loads(line) for line in result.stderr.splitlines()]
    phases = [row["phase"] for row in rows]
    assert phases == ["diagnostics-start", "source-admission-begin", "worker-start", "diagnostics-stop"]
    assert len(result.stderr.encode()) <= 32768 and len(rows) <= 96
    assert all(len(line.encode()) + 1 <= 512 for line in result.stderr.splitlines())
    for row in rows:
        assert set(row) == {"schema_version", "phase", "scope", "pid", "observed_monotonic", "remaining_seconds"}
        assert row["scope"] == SCOPE and row["pid"] == held["pid"]
        assert row["observed_monotonic"] + row["remaining_seconds"] == held["deadline"]
    assert "private-secret" not in result.stderr


def test_real_regular_file_sink_and_fixed_event_ceiling(tmp_path: Path) -> None:
    sink = tmp_path / "controller.stderr.bin"
    with sink.open("wb") as output:
        result = _probe(
            """
            deadline = time.monotonic() + 20
            with _representative_preflight_diagnostics(deadline):
                for repeat in range(100):
                    for phase in sorted(_PHASES - {"guardian-ready", "worker-popen-returned"}):
                        _preflight_phase(phase, deadline)
        """,
            stderr=output.fileno(),
        )
    assert result.returncode == 0
    raw = sink.read_bytes()
    rows = [json.loads(line) for line in raw.splitlines()]
    assert 30 <= len(rows) <= 96
    assert len(rows) == len({row["phase"] for row in rows})
    assert len(raw) <= 32768


@pytest.mark.skipif(os.name != "posix", reason="real POSIX inherited diagnostic descriptor controls")
@pytest.mark.parametrize("sink_state", ["full", "broken"])
def test_real_blocked_or_broken_pipe_cannot_hold_original_exit(sink_state: str) -> None:
    read_fd, write_fd = os.pipe()
    try:
        if sink_state == "full":
            os.set_blocking(write_fd, False)
            filled = 0
            try:
                while filled < 16 * 1024 * 1024:
                    filled += os.write(write_fd, b"x" * 4096)
            except BlockingIOError:
                pass
            assert 0 < filled < 16 * 1024 * 1024
            os.set_blocking(write_fd, True)
        else:
            os.close(read_fd)
            read_fd = -1
        result = _probe(
            """
            deadline = time.monotonic() + 10
            try:
                with _representative_preflight_diagnostics(deadline):
                    _preflight_phase("worker-start", deadline)
                    threading.Event().wait(0.1)
                    raise SystemExit(17)
            finally:
                assert not any(thread.name == "native-preflight-sampler" for thread in threading.enumerate())
                print("actual-exit-17", flush=True)
        """,
            stderr=write_fd,
        )
        assert result.returncode == 17
        assert result.stdout.strip() == "actual-exit-17"
    finally:
        if read_fd >= 0:
            os.close(read_fd)
        os.close(write_fd)


@pytest.mark.skipif(os.name != "posix", reason="real POSIX closed descriptor control")
def test_real_closed_descriptor_preserves_exception_and_expired_clock() -> None:
    result = _probe("""
        os.close(2)
        try:
            with _representative_preflight_diagnostics(time.monotonic() - 1):
                raise SystemExit(23)
        finally:
            print("actual-exit-23")
    """)
    assert result.returncode == 23 and result.stdout.strip() == "actual-exit-23"


def test_real_sampler_cancels_on_completion_and_does_not_enter_other_threads() -> None:
    result = _probe("""
        from contextvars import copy_context
        deadline = time.monotonic() + 30.2
        with _representative_preflight_diagnostics(deadline):
            context = copy_context()
            thread = threading.Thread(target=lambda: context.run(_preflight_phase, "wait-begin", deadline))
            thread.start()
            thread.join(timeout=1)
            assert not thread.is_alive()
            with _representative_preflight_diagnostics(deadline):
                _preflight_phase("source-admission-begin", deadline)
        assert _CONTEXT.get() is None
        threading.Event().wait(0.4)
        assert not any(thread.name.startswith("native-preflight-") for thread in threading.enumerate())
    """)
    assert result.returncode == 0, result.stderr
    rows = [json.loads(line) for line in result.stderr.splitlines()]
    assert [row["phase"] for row in rows] == ["diagnostics-start", "source-admission-begin", "diagnostics-stop"]


@pytest.mark.timeout(60)
def test_two_real_scheduled_main_thread_samples_have_finite_sanitized_frames() -> None:
    result = _probe(
        """
        def private_secret_function(depth):
            private_secret_local = "/private/secret/source-and-environment"
            if depth:
                private_secret_function(depth - 1)
            else:
                threading.Event().wait(26)
            assert private_secret_local
        deadline = time.monotonic() + 30.5
        with _representative_preflight_diagnostics(deadline):
            private_secret_function(30)
        assert not any(thread.name.startswith("native-preflight-") for thread in threading.enumerate())
        print(json.dumps({"deadline": deadline, "pid": os.getpid()}))
    """,
        timeout=45,
    )
    assert result.returncode == 0, result.stderr
    held = json.loads(result.stdout)
    rows = [json.loads(line) for line in result.stderr.splitlines()]
    stacks = [row for row in rows if row["schema_version"] == "template-native-preflight-stack-v1"]
    assert {row["phase"] for row in stacks} == {"stack-minus-30", "stack-minus-5"}
    for phase, margin in (("stack-minus-30", 30), ("stack-minus-5", 5)):
        frames = [row for row in stacks if row["phase"] == phase]
        assert len(frames) == 24
        assert [row["frame"] for row in frames] == list(range(24))
        for row in frames:
            assert set(row) == {
                "schema_version",
                "phase",
                "scope",
                "pid",
                "observed_monotonic",
                "remaining_seconds",
                "frame",
                "module",
                "function",
                "line",
            }
            assert row["module"] == row["function"] == "unlisted" and row["line"] == 0
            assert row["pid"] == held["pid"] and 0 < row["remaining_seconds"] <= margin
            assert row["observed_monotonic"] + row["remaining_seconds"] == held["deadline"]
    assert len(rows) <= 96 and len(result.stderr.encode()) <= 32768
    assert all(len(line.encode()) + 1 <= 512 for line in result.stderr.splitlines())
    assert "private_secret" not in result.stderr and "/private" not in result.stderr
