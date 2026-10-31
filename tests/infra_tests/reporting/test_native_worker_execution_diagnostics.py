"""Real diagnostic transport controls, not native-worker acceptance evidence."""

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

from infrastructure.reporting.native_worker_startup_diagnostics import (
    _diagnostic_envelope,
    _EXECUTION_PHASES,
)


pytestmark = pytest.mark.timeout(30)
ROOT = Path(__file__).resolve().parents[3]
PREFIX = "NATIVE_WORKER_STARTUP_V1 "


def _run(
    body: str,
    *,
    duration: float = 10.0,
    stderr: int = subprocess.PIPE,
    close_stderr: bool = False,
    timeout: float = 15.0,
) -> subprocess.CompletedProcess[str]:
    imports = f"""
import sys
sys.path.insert(0, {str(ROOT)!r})
from pathlib import Path
from infrastructure.reporting.native_worker_startup_diagnostics import (
    _worker_execution_observer, _worker_execution_phase, _worker_execution_entry,
    _EXECUTION_PHASES,
)
"""
    program = _diagnostic_envelope(
        imports + textwrap.dedent(body), ROOT / "infrastructure", time.monotonic() + duration
    )
    if close_stderr:
        program = "import os\nos.close(2)\n" + program
    return subprocess.run(
        [sys.executable, "-I", "-B", "-c", program],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=stderr,
        text=True,
        timeout=timeout,
        check=False,
    )


def _rows(raw: str) -> list[list[str]]:
    rows = [line.split() for line in raw.splitlines() if line.startswith(PREFIX)]
    assert all(len(row) == 8 for row in rows)
    assert len(rows) <= 96
    assert sum(len(" ".join(row).encode()) + 1 for row in rows) <= 32768
    assert all(len(" ".join(row).encode()) + 1 <= 512 for row in rows)
    assert all(float(row[4]) > 0 for row in rows)
    assert all(row[6] in {"none", "bootstrap", "worker-main", "unlisted"} for row in rows)
    assert "private-diagnostic-sentinel" not in raw
    return rows


def test_real_helpers_emit_order_and_entry_return_before_body(tmp_path: Path) -> None:
    path = tmp_path / "private-diagnostic-sentinel"
    path.write_text("actual file bytes")
    result = _run(f"""
        with _worker_execution_observer(_native_startup.observe):
            with _worker_execution_phase('run-native-worker'):
                with _worker_execution_entry('producer-entry', Path({str(path)!r}).open()) as stream:
                    with _worker_execution_phase('worker-body'):
                        assert stream.read() == 'actual file bytes'
                assert stream.closed
        with _worker_execution_phase('worker-fingerprint'):
            pass
        time.sleep(0.1)
    """)
    assert result.returncode == 0, result.stderr
    phases = [
        row[1]
        for row in _rows(result.stderr)
        if row[1].startswith(("run-native-worker", "producer-entry", "worker-body"))
    ]
    assert phases == [
        "run-native-worker-begin",
        "producer-entry-begin",
        "producer-entry-returned",
        "worker-body-begin",
        "worker-body-returned",
        "run-native-worker-returned",
    ]
    assert not any(row[1].startswith("worker-fingerprint") for row in _rows(result.stderr))


def test_runpy_injected_sink_crosses_real_canonical_module_imports(tmp_path: Path) -> None:
    driver = tmp_path / "diagnostic_driver.py"
    payload = tmp_path / "payload.txt"
    payload.write_text("real payload")
    driver.write_text(
        textwrap.dedent(f"""
        from pathlib import Path
        import infrastructure.reporting.native_format_acceptance_worker as canonical_worker
        import infrastructure.reporting.native_format_scope_replay as canonical_scope
        from infrastructure.reporting.native_worker_startup_diagnostics import _worker_execution_observer
        assert '_native_startup_observer' not in vars(canonical_worker)
        canonical_worker._native_startup_phase('source-admission-begin')
        with _worker_execution_observer(globals().get('_native_startup_observer')):
            with canonical_worker._worker_execution_phase('run-native-worker'):
                with canonical_scope._worker_execution_entry('producer-entry', Path({str(payload)!r}).open()) as stream:
                    with canonical_scope._worker_execution_phase('worker-body'):
                        assert stream.read() == 'real payload'
    """)
    )
    result = _run(
        f"""
        import runpy
        runpy.run_path({str(driver)!r}, run_name='__main__',
                      init_globals={{'_native_startup_observer': _native_startup.observe}})
        time.sleep(0.1)
    """,
        duration=20.0,
        timeout=25.0,
    )
    assert result.returncode == 0, result.stderr
    phases = [row[1] for row in _rows(result.stderr)]
    assert "source-admission-begin" not in phases
    assert [phase for phase in phases if phase.startswith(("run-native-worker", "producer-entry", "worker-body"))] == [
        "run-native-worker-begin",
        "producer-entry-begin",
        "producer-entry-returned",
        "worker-body-begin",
        "worker-body-returned",
        "run-native-worker-returned",
    ]


def test_actual_entry_failure_and_original_body_exception(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    result = _run(f"""
        from contextlib import chdir, suppress
        failure = ValueError('private-diagnostic-sentinel')
        with _worker_execution_observer(_native_startup.observe):
            try:
                with _worker_execution_entry('producer-entry', chdir({str(missing)!r})):
                    raise AssertionError('entry must not complete')
            except FileNotFoundError:
                pass
            else:
                raise AssertionError('entry error was suppressed')
            try:
                with _worker_execution_phase('worker-body'):
                    raise failure
            except ValueError as caught:
                assert caught is failure
            else:
                raise AssertionError('body error was suppressed')
            with _worker_execution_entry('mermaid-runtime-entry', suppress(ValueError)):
                raise failure
        time.sleep(0.1)
    """)
    assert result.returncode == 0, result.stderr
    phases = [row[1] for row in _rows(result.stderr)]
    assert "producer-entry-raised" in phases and "producer-entry-returned" not in phases
    assert "worker-body-raised" in phases and "worker-body-returned" not in phases
    assert "mermaid-runtime-entry-returned" in phases and "mermaid-runtime-entry-raised" not in phases


@pytest.mark.parametrize("error_type", ["RuntimeError", "KeyboardInterrupt", "SystemExit"])
def test_observer_failure_cannot_replace_original_result_or_exception(error_type: str) -> None:
    result = _run(f"""
        calls = []
        def failing_observer(phase, frame):
            calls.append(phase)
            raise {error_type}('private-diagnostic-sentinel')
        original = LookupError('private-diagnostic-sentinel')
        with _worker_execution_observer(failing_observer):
            with _worker_execution_phase('worker-body'):
                value = 41
            assert value == 41
            try:
                with _worker_execution_phase('worker-fingerprint'):
                    raise original
            except LookupError as caught:
                assert caught is original
            else:
                raise AssertionError('original exception lost')
        assert calls == ['worker-body-begin', 'worker-body-returned',
                         'worker-fingerprint-begin', 'worker-fingerprint-raised']
    """)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("mode", ["closed", "broken", "full"])
def test_real_sink_failures_do_not_replace_original_exception(mode: str) -> None:
    body = """
        original = LookupError('private-diagnostic-sentinel')
        observer = _native_startup.observe if _native_startup is not None else None
        try:
            with _worker_execution_observer(observer), _worker_execution_phase('worker-body'):
                raise original
        except LookupError as caught:
            assert caught is original
        else:
            raise AssertionError('original exception lost')
        time.sleep(0.1)
        raise SystemExit(29)
    """
    if mode == "closed":
        assert _run(body, close_stderr=True).returncode == 29
        return
    read_descriptor, write_descriptor = os.pipe()
    try:
        if mode == "broken":
            os.close(read_descriptor)
            read_descriptor = -1
        else:
            os.set_blocking(write_descriptor, False)
            while True:
                try:
                    os.write(write_descriptor, b"x" * 4096)
                except BlockingIOError:
                    break
            os.set_blocking(write_descriptor, True)
        started = time.monotonic()
        result = _run(body, stderr=write_descriptor)
        assert result.returncode == 29
        assert time.monotonic() - started < 15
    finally:
        os.close(write_descriptor)
        if read_descriptor >= 0:
            os.close(read_descriptor)


def test_expired_deadline_actual_helpers_remain_silent() -> None:
    result = _run(
        """
        original = ValueError('private-diagnostic-sentinel')
        with _worker_execution_observer(_native_startup.observe):
            try:
                with _worker_execution_phase('worker-body'):
                    raise original
            except ValueError as caught:
                assert caught is original
        raise SystemExit(31)
    """,
        duration=-1.0,
    )
    assert result.returncode == 31 and result.stderr == ""


def test_actual_full_queue_fixed_labels_dedup_and_bounds() -> None:
    result = _run("""
        saturated = _NativeStartupDiagnostics()
        for count in range(96):
            saturated.pending.put_nowait(b'full')
        original = ValueError('private-diagnostic-sentinel')
        with _worker_execution_observer(saturated.observe):
            try:
                with _worker_execution_phase('worker-body'):
                    raise original
            except ValueError as caught:
                assert caught is original
        assert saturated.pending.qsize() == 96
        assert saturated.events == 2
        saturated.close()
        bounded = _NativeStartupDiagnostics()
        with _worker_execution_observer(bounded.observe), _worker_execution_phase('mermaid-tool-api'):
            for count in range(100):
                for phase in _EXECUTION_PHASES:
                    with _worker_execution_phase(phase):
                        pass
                with _worker_execution_phase('private-diagnostic-sentinel'):
                    pass
        records = []
        while not bounded.pending.empty():
            records.append(bounded.pending.get_nowait())
        assert len(records) == len(_EXECUTION_PHASES) * 2
        assert len(set(records)) == len(records)
        assert bounded.events <= 96 and bounded.byte_count <= 32768
        assert all(len(record) <= 512 for record in records)
        assert not any(b'private-diagnostic-sentinel' in record for record in records)
        bounded.close()
        with _worker_execution_observer(_native_startup.observe), _worker_execution_phase('mermaid-tool-api'):
            for count in range(100):
                for phase in _EXECUTION_PHASES:
                    with _worker_execution_phase(phase):
                        pass
        time.sleep(0.1)
    """)
    assert result.returncode == 0, result.stderr
    phases = [row[1] for row in _rows(result.stderr) if row[5] == "-1"]
    assert len(phases) == len(set(phases))
    assert "worker-body-returned" in phases


def test_real_thread_fork_owner_checks_and_context_restoration() -> None:
    result = _run("""
        import json
        from contextvars import copy_context
        from threading import Thread
        def attempt():
            with _worker_execution_phase('worker-fingerprint'):
                pass
        with _worker_execution_observer(_native_startup.observe):
            context = copy_context()
            thread = Thread(target=context.run, args=(attempt,))
            thread.start()
            thread.join(timeout=2)
            assert not thread.is_alive()
            child = os.fork()
            if child == 0:
                attempt()
                os._exit(0)
            assert os.waitpid(child, 0)[1] == 0
            with _worker_execution_observer(None):
                attempt()
            with _worker_execution_phase('worker-body'):
                pass
        attempt()
        print(json.dumps({'pid': os.getpid()}))
        time.sleep(0.1)
    """)
    assert result.returncode == 0, result.stderr
    rows = _rows(result.stderr)
    assert all(int(row[2]) == json.loads(result.stdout)["pid"] for row in rows)
    assert not any(row[1].startswith("worker-fingerprint") for row in rows)
    assert any(row[1] == "worker-body-returned" for row in rows)


def test_real_queue_reserves_every_phase_after_stack_saturation() -> None:
    result = _run("""
        reserved = _NativeStartupDiagnostics()
        assert len(reserved.phases) == 84
        for count in range(500):
            reserved.emit('anchored-stack', count % 12, 'unlisted', 0)
        assert reserved.stack_events == 12
        with _worker_execution_observer(reserved.observe), _worker_execution_phase('mermaid-tool-api'):
            for phase in _EXECUTION_PHASES:
                with _worker_execution_phase(phase):
                    pass
                try:
                    with _worker_execution_phase(phase):
                        raise ValueError('private-diagnostic-sentinel')
                except ValueError:
                    pass
        execution_labels = {phase + '-' + outcome for phase in _EXECUTION_PHASES
                            for outcome in ('begin', 'returned', 'raised')}
        for phase in reserved.phases - execution_labels:
            reserved.observe(phase, sys._getframe())
        assert reserved.events == 96 and reserved.pending.qsize() == 96
        assert reserved.byte_count <= 32768
        records = [reserved.pending.get_nowait() for count in range(96)]
        labels = [record.decode().split()[1] for record in records]
        assert labels.count('anchored-stack') == 12
        assert set(labels) - {'anchored-stack'} == reserved.phases
        assert all(labels.count(phase) == 1 for phase in reserved.phases)
        assert all(len(record) <= 512 for record in records)
        reserved.close()
    """)
    assert result.returncode == 0, result.stderr


def test_retention_labels_belong_only_to_fixed_mermaid_tool_interval() -> None:
    result = _run("""
        with _worker_execution_observer(_native_startup.observe):
            with _worker_execution_phase('retain-tool-data'):
                pass
            with _worker_execution_phase('mermaid-tool-api'):
                with _worker_execution_phase('retain-tool-verify'):
                    pass
            try:
                with _worker_execution_phase('retain-tool-verify'):
                    raise ValueError('private-diagnostic-sentinel')
            except ValueError:
                pass
        time.sleep(0.1)
    """)
    assert result.returncode == 0, result.stderr
    phases = [row[1] for row in _rows(result.stderr)]
    assert "retain-tool-data-begin" not in phases
    assert "retain-tool-verify-returned" in phases
    assert "retain-tool-verify-raised" not in phases


@pytest.mark.parametrize("position", ["yielded", "returned"])
def test_real_sampler_retains_bootstrap_anchor_across_execution_phases(position: str) -> None:
    result = _run(f"""
        _native_startup_checkpoint('worker-execution-begin')
        held_anchor = _native_startup.anchor
        def await_actual_sampler():
            observed = time.monotonic()
            targets = (_native_startup.started + 1, _native_startup.started + 5,
                       _native_startup.started + 20, _native_startup.started + 60,
                       _native_startup.deadline - 30, _native_startup.deadline - 5)
            target = min(value for value in targets if observed < value < _native_startup.deadline)
            time.sleep(max(0.0, target + 0.2 - time.monotonic()))
        with _worker_execution_observer(_native_startup.observe):
            with _worker_execution_phase('run-native-worker'):
                with _worker_execution_phase('worker-body'):
                    if {position!r} == 'yielded':
                        await_actual_sampler()
                if {position!r} == 'returned':
                    await_actual_sampler()
                assert _native_startup.anchor is held_anchor
    """)
    assert result.returncode == 0, result.stderr
    rows = _rows(result.stderr)
    entry = next(float(row[3]) for row in rows if row[1] == "worker-body-begin")
    if position == "returned":
        entry = next(float(row[3]) for row in rows if row[1] == "worker-body-returned")
    samples = [row for row in rows if row[1] == "anchored-stack" and float(row[3]) > entry]
    assert samples and any(row[6] == "bootstrap" and int(row[7]) > 0 for row in samples)


def test_fixed_source_flow_supplements_real_transport_controls() -> None:
    paths = (
        "native_format_acceptance_worker.py",
        "native_format_scope_replay.py",
        "native_mermaid_runtime_selection.py",
        "native_tool_producer.py",
    )
    observed = set()
    entries = {}
    for name in paths:
        tree = ast.parse((ROOT / "infrastructure/reporting" / name).read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
                continue
            if node.func.id not in {"_worker_execution_phase", "_worker_execution_entry"}:
                continue
            assert isinstance(node.args[0], ast.Constant)
            observed.add(node.args[0].value)
            if node.func.id == "_worker_execution_entry":
                manager = node.args[1]
                assert isinstance(manager, ast.Call)
                entries[node.args[0].value] = ast.unparse(manager.func)
    assert observed == set(_EXECUTION_PHASES)
    assert entries == {
        "producer-entry": "native_producer_operation",
        "mermaid-runtime-entry": "source_mermaid_runtime_operation",
        "pdfium-execution-entry": "full_worker_pdfium_execution",
        "mermaid-post-node-guard": "producer._verification_guard",
    }
    worker = ast.parse((ROOT / "infrastructure/reporting/native_format_acceptance_worker.py").read_text())
    main = next(node for node in worker.body if isinstance(node, ast.FunctionDef) and node.name == "main")
    bindings = [
        node
        for node in ast.walk(main)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_worker_execution_observer"
    ]
    assert len(bindings) == 1
    assert ast.unparse(bindings[0].args[0]) == "globals().get('_native_startup_observer')"
