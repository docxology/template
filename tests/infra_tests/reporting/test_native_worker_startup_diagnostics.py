"""Real subprocess/descriptor controls for diagnostic transport, not native acceptance."""

from __future__ import annotations

import ast
import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap
import time

import pytest

from infrastructure.reporting.native_worker_startup_diagnostics import _diagnostic_envelope


pytestmark = pytest.mark.timeout(30)
PREFIX = "NATIVE_WORKER_STARTUP_V1 "


def _program(body: str, *, duration: float = 10.0) -> str:
    return _diagnostic_envelope(
        textwrap.dedent(body), Path("/private-diagnostic-sentinel"), time.monotonic() + duration
    )


def _run(body: str, *, duration: float = 10.0, stderr: int = subprocess.PIPE) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-I", "-B", "-c", _program(body, duration=duration)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=stderr,
        text=True,
        timeout=15,
        check=False,
    )


def _rows(raw: str) -> list[list[str]]:
    rows = [line.split() for line in raw.splitlines() if line.startswith(PREFIX)]
    assert all(len(row) == 8 for row in rows)
    assert len(rows) <= 96
    assert sum(len(" ".join(row).encode()) + 1 for row in rows) <= 32768
    assert all(len(" ".join(row).encode()) + 1 <= 512 for row in rows)
    assert all(row[6] in {"none", "bootstrap", "worker-main", "unlisted"} for row in rows)
    assert "private-diagnostic-sentinel" not in raw
    return rows


def test_actual_early_child_samples_before_original_deadline() -> None:
    result = _run("""
        import json
        print(json.dumps({'pid':os.getpid(),'deadline':_native_startup.deadline}),flush=True)
        _native_startup_checkpoint('audit-begin')
        time.sleep(1.3)
        raise SystemExit(17)
    """)
    assert result.returncode == 17
    identity = json.loads(result.stdout)
    rows = _rows(result.stderr)
    assert any(row[1] == "audit-begin" for row in rows)
    samples = [row for row in rows if row[1] == "anchored-stack"]
    assert samples and all(int(row[2]) == identity["pid"] for row in rows)
    assert any(row[6] == "bootstrap" for row in samples)
    assert all(float(row[4]) > 0 for row in rows)
    assert all(abs(float(row[3]) + float(row[4]) - identity["deadline"]) < 1e-6 for row in rows)


def test_duplicate_unknown_and_flooded_labels_remain_bounded() -> None:
    result = _run("""
        for count in range(10000):
            _native_startup_checkpoint('private-diagnostic-sentinel')
            _native_startup_checkpoint('source-admission-begin')
            _native_startup.emit('private-diagnostic-sentinel')
            _native_startup.emit('anchored-stack',0,'private-diagnostic-sentinel')
            _native_startup.emit('anchored-stack',0,'unlisted',0)
        time.sleep(0.1)
    """)
    assert result.returncode == 0, result.stderr
    rows = _rows(result.stderr)
    assert sum(row[1] == "source-admission-begin" for row in rows) <= 1


def test_real_closed_and_broken_sinks_preserve_exit() -> None:
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", "import os\nos.close(2)\n" + _program("raise SystemExit(23)")],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=15,
        check=False,
    )
    assert result.returncode == 23
    read_descriptor, write_descriptor = os.pipe()
    os.close(read_descriptor)
    try:
        result = _run("time.sleep(0.1)\nraise SystemExit(23)", stderr=write_descriptor)
        assert result.returncode == 23
    finally:
        os.close(write_descriptor)


def test_real_full_pipe_preserves_exit_without_claiming_writer_cleanup() -> None:
    read_descriptor, write_descriptor = os.pipe()
    try:
        os.set_blocking(write_descriptor, False)
        while True:
            try:
                os.write(write_descriptor, b"x" * 4096)
            except BlockingIOError:
                break
        os.set_blocking(write_descriptor, True)
        started = time.monotonic()
        result = _run("time.sleep(0.2)\nraise SystemExit(29)", stderr=write_descriptor)
        assert result.returncode == 29
        assert time.monotonic() - started < 15
    finally:
        os.close(write_descriptor)
        os.close(read_descriptor)


def test_regular_sink_does_not_change_descriptor_flags_and_sampler_stops(tmp_path: Path) -> None:
    with (tmp_path / "worker.stderr.bin").open("wb") as sink:
        result = _run(
            """
            import fcntl
            os.write(2,b'regular-sink-baseline')
            flags = fcntl.fcntl(2,fcntl.F_GETFL)
            _native_startup_checkpoint('worker-main-enter')
            time.sleep(0.1)
            _native_startup.close()
            assert fcntl.fcntl(2,fcntl.F_GETFL) == flags
            assert not _native_startup.sampler.is_alive()
            assert not _native_startup.writer.is_alive()
            assert _native_startup.anchor is None
        """,
            stderr=sink.fileno(),
        )
    assert result.returncode == 0
    assert _rows((tmp_path / "worker.stderr.bin").read_text())


def test_expired_original_clock_stays_expired_and_silent() -> None:
    result = _run("raise SystemExit(31)", duration=-1.0)
    assert result.returncode == 31
    assert result.stderr == ""


def test_real_deep_private_anchor_emits_only_twelve_sanitized_callers(tmp_path: Path) -> None:
    private = tmp_path / "private-diagnostic-sentinel.py"
    private.write_text(
        textwrap.dedent("""
        import sys,time
        def private_name(depth,observer):
            if depth:
                return private_name(depth-1,observer)
            observer('source-admission-begin',sys._getframe())
            time.sleep(1.3)
        private_name(40,observer)
    """)
    )
    result = _run(f"""
        import runpy
        runpy.run_path({str(private)!r},init_globals={{'observer':_native_startup.observe}})
    """)
    assert result.returncode == 0, result.stderr
    samples = [row for row in _rows(result.stderr) if row[1] == "anchored-stack"]
    assert len(samples) == 12
    assert [int(row[5]) for row in samples] == list(range(12))
    assert all(row[6:] == ["unlisted", "0"] for row in samples)
    assert "private_name" not in result.stderr


def test_production_envelope_has_no_thread_scan_signals_trace_or_source_imports() -> None:
    tree = ast.parse(_program("pass"))
    imports = {
        alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names
    }
    assert imports == {"math", "os", "queue", "sys", "threading", "time", "types"}
    forbidden = {"_current_frames", "settrace", "setprofile", "signal", "setitimer", "f_locals", "f_globals"}
    assert not any(isinstance(node, ast.Attribute) and node.attr in forbidden for node in ast.walk(tree))


def test_real_audit_install_preserves_no_public_import_boundary(tmp_path: Path) -> None:
    from infrastructure.core.implementation_custody import bytecode_audit_bootstrap

    source_root = Path(__file__).resolve().parents[3] / "infrastructure"
    prefix = tmp_path / "bytecode"
    prefix.mkdir()
    audit = bytecode_audit_bootstrap((source_root,), prefix)
    body = (
        f"sys.pycache_prefix={str(prefix)!r}\n"
        + audit
        + "\n"
        + textwrap.dedent("""
        assert not any(name == 'infrastructure' or name.startswith('infrastructure.') for name in sys.modules)
        _native_startup_checkpoint('audit-returned')
        assert sys._template_executed_bytecode_audit['snapshot']() == {}
        time.sleep(0.1)
    """)
    )
    result = _run(body)
    assert result.returncode == 0, result.stderr
    assert any(row[1] == "audit-returned" for row in _rows(result.stderr))


@pytest.mark.timeout(180)
def test_actual_emitted_bootstrap_real_worker_help_does_not_admit_invalid_closure(tmp_path: Path) -> None:
    import hashlib

    import infrastructure
    from infrastructure.reporting.native_source_provider_bootstrap import format_selected_sdk_native_bootstrap

    assert infrastructure.__file__ is not None
    package = Path(infrastructure.__file__).absolute().parent
    implementation = tmp_path / "invalid-implementation.json"
    implementation.write_bytes(b"{}\n")
    closure = tmp_path / "closure"
    closure.mkdir()
    identity = closure.stat().st_dev, closure.stat().st_ino
    command = format_selected_sdk_native_bootstrap(
        (package / "core/bytecode_audit.py").read_bytes(),
        package,
        (),
        implementation,
        hashlib.sha256(implementation.read_bytes()).hexdigest(),
        closure,
        identity,
        time.monotonic() + 90,
    )
    result = subprocess.run(
        [sys.executable, "-I", "-c", command, "--help"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    phases = {row[1] for row in _rows(result.stderr)}
    assert {"audit-returned", "package-exec-returned", "worker-dispatch", "worker-main-enter"} <= phases
    assert "source-admission-returned" not in phases
    receipt = closure / "receipt.json"
    if receipt.is_file():
        assert json.loads(receipt.read_text())["status"] == "failed"
    else:
        assert "selected SDK execution closure retention failed" in result.stderr


@pytest.mark.timeout(180)
@pytest.mark.parametrize("enabled", [False, True])
@pytest.mark.parametrize("code", [0, 17])
def test_real_guardian_os_outcome_with_and_without_worker_diagnostics(
    tmp_path: Path,
    enabled: bool,
    code: int,
) -> None:
    from infrastructure.reporting.native_tool_process import run_native_tool_process

    deadline = time.monotonic() + 120
    body = f"import os\nprint(os.getpid(),flush=True)\nraise SystemExit({code})\n"
    command = _diagnostic_envelope(body, Path("/private-diagnostic-sentinel"), deadline) if enabled else body
    result = run_native_tool_process(
        tmp_path,
        sys.executable,
        ["-I", "-B", "-c", command],
        cwd=tmp_path,
        env=dict(os.environ),
        deadline=deadline,
        purpose="original-native-worker",
    )
    actual_pid = int((tmp_path / "original-native-worker.stdout.bin").read_text())
    assert result["pid"] == actual_pid
    assert result["original_exit_code"] == code and result["timed_out"] is False
    assert result["original_deadline_monotonic"] == deadline
    assert result["cleanup"]["guardian_armed"] is True
    assert result["cleanup"]["root_reaped"] is True
    assert result["cleanup"]["guardian_finished"] is True
    assert result["cleanup"]["final_token_sweep_matched_pids"] == []
