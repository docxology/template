"""Best-effort Original phase diagnostics; never custody or execution authority."""

from __future__ import annotations

import json
import math
import os
import queue
import sys
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

_SCOPE = "templates/template_code_project"
_MAX_EVENTS = 96
_MAX_BYTES = 32768
_MAX_RECORD_BYTES = 512
_MAX_FRAMES = 24
_PHASES = frozenset(
    {
        "diagnostics-start",
        "diagnostics-stop",
        "preparation-begin",
        "preparation-end",
        "source-admission-begin",
        "source-admission-end",
        "mermaid-begin",
        "mermaid-end",
        "providers-begin",
        "providers-end",
        "descriptor-begin",
        "descriptor-end",
        "sdk-command-begin",
        "sdk-command-end",
        "supervisor-begin",
        "supervisor-end",
        "launch-verify-begin",
        "launch-verify-end",
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
        "preflight-returned",
        "selection-start",
        "worker-start",
        "worker-completed",
        "terminal-observed",
    }
)
_PUBLIC_FRAMES = {
    "reporting/native_installed_preflight.py": {"main", "_run_preflight"},
    "reporting/native_format_acceptance.py": {
        "run_native_format_acceptance",
        "_run_native_format_acceptance",
        "_run_admitted_native_format_acceptance",
        "_run_original_native_cells",
    },
    "reporting/native_original_supervisor.py": {"__init__", "_verify", "launch", "finish"},
    "reporting/native_tool_process.py": {"run_native_tool_process", "_finish_guardian"},
    "reporting/native_source_external_admission.py": {
        "_anchored_directory_identity",
        "_observe_source_directory_identities",
        "_verify_source_directory_identities",
        "_pure_source_records",
        "admit_path",
        "_verify_current_source_modes",
        "_verify_current_source",
        "verify_correspondence",
        "_correspondence_guard",
        "descriptor",
        "_descriptor_data",
        "admit_external_native_source",
        "admit_explicitly_bound_native_source",
    },
    "core/_bounded_run_guardian.py": {"start_bounded_run_guardian", "arm", "close"},
    "core/pipeline/fingerprints.py": {
        "verify_loaded_implementation",
        "_observe_loaded_implementation",
        "paths_digest",
        "tree_records",
        "visit",
        "names",
    },
    "core/pipeline/fingerprint_files.py": {
        "digest_file",
        "digest_path",
        "anchored_parent",
        "open_directory",
        "verify_directory",
    },
    "core/implementation_custody.py": {
        "capture_implementation_custody",
        "verify_implementation_custody",
        "source_file_manifest",
        "_regular_bytes",
        "_regular_bytes_at",
        "bytecode_audit_bootstrap",
    },
    "core/bytecode_audit.py": {"_read_cache", "verify_executed_source_code", "canonical_code"},
    "reporting/native_format_portable_custody.py": {"executable_observation"},
}
_CONTEXT: ContextVar[_PreflightDiagnostics | None] = ContextVar("native_preflight_diagnostics", default=None)


class _PreflightDiagnostics:
    """Finite DATA only; one sampler and one sink daemon, no execution authority."""

    def __init__(self, deadline: float) -> None:
        self.deadline = deadline
        self.started = time.monotonic()
        self.owner_pid = os.getpid()
        self.owner_thread = threading.get_ident()
        self.stop = threading.Event()
        self.sink_stop = threading.Event()
        self.lock = threading.Lock()
        self.pending: queue.SimpleQueue[bytes | None] = queue.SimpleQueue()
        self.events = 0
        self.byte_count = 0
        self.seen: set[str] = set()
        self.writer: threading.Thread | None = None
        self.sampler: threading.Thread | None = None
        package = os.path.dirname(os.path.dirname(__file__))
        self.modules = {os.path.join(package, name): name for name in _PUBLIC_FRAMES}

    def start(self) -> None:
        """Only the writer owns the duplicated descriptor after successful start."""
        descriptor = os.dup(2)
        try:
            self.writer = threading.Thread(
                target=self._write,
                args=(descriptor,),
                name="native-preflight-sink",
                daemon=True,
            )
            self.writer.start()
        except Exception:
            os.close(descriptor)
            raise
        self.sampler = threading.Thread(target=self._sample, name="native-preflight-sampler", daemon=True)
        self.sampler.start()

    def emit(self, phase: str, *, pid: int | None = None, frame: dict[str, object] | None = None) -> None:
        """Never wait for sink I/O or a contended diagnostic lock; count attempted bytes."""
        if self.stop.is_set() or not self.lock.acquire(blocking=False):
            return
        try:
            if self.events >= _MAX_EVENTS or (frame is None and phase in self.seen):
                return
            observed = time.monotonic()
            value: dict[str, object] = {
                "schema_version": "template-native-original-progress-v1",
                "phase": phase,
                "scope": _SCOPE,
                "pid": self.owner_pid if pid is None else pid,
                "observed_monotonic": observed,
                "remaining_seconds": self.deadline - observed,
            }
            if frame is not None:
                if observed >= self.deadline:
                    return
                value["schema_version"] = "template-native-preflight-stack-v1"
                value.update(frame)
            encoded = (json.dumps(value, sort_keys=True, allow_nan=False) + "\n").encode("ascii")
            self.events += 1
            if len(encoded) > _MAX_RECORD_BYTES or self.byte_count + len(encoded) > _MAX_BYTES:
                return
            self.byte_count += len(encoded)
            if frame is None:
                self.seen.add(phase)
            self.pending.put(encoded)
        except Exception:
            pass
        finally:
            self.lock.release()

    def _write(self, descriptor: int) -> None:
        """A blocked kernel write is isolated here, never joined beyond the original clock."""
        try:
            while not self.sink_stop.is_set():
                record = self.pending.get(timeout=max(0.0, self.deadline - time.monotonic()))
                if record is None or self.sink_stop.is_set() or time.monotonic() >= self.deadline:
                    return
                if os.write(descriptor, record) != len(record):
                    return
        except Exception:
            pass
        finally:
            try:
                os.close(descriptor)
            except OSError:
                pass

    def _sample(self) -> None:
        """Inspect at most twenty-four main-thread frames at each of two original-clock targets."""
        try:
            for phase, margin in (("stack-minus-30", 30.0), ("stack-minus-5", 5.0)):
                target = self.deadline - margin
                if target < self.started:
                    continue
                if self.stop.wait(max(0.0, target - time.monotonic())) or time.monotonic() >= self.deadline:
                    return
                current = sys._current_frames().get(self.owner_thread)
                try:
                    for index in range(_MAX_FRAMES):
                        if current is None or self.stop.is_set() or time.monotonic() >= self.deadline:
                            break
                        module = self.modules.get(current.f_code.co_filename)
                        function = current.f_code.co_name
                        known = module is not None and function in _PUBLIC_FRAMES[module]
                        self.emit(
                            phase,
                            frame={
                                "frame": index,
                                "module": module if module is not None else "unlisted",
                                "function": function if known else "unlisted",
                                "line": min(max(current.f_lineno, 0), 1000000) if module is not None else 0,
                            },
                        )
                        current = current.f_back
                finally:
                    del current
        except Exception:
            pass

    def close(self) -> None:
        """Cancel sampling and queued output; share one at-most-50ms original-clock join."""
        self.stop.set()
        self.pending.put(None)
        join_deadline = min(self.deadline, time.monotonic() + 0.05)
        for thread in (self.sampler, self.writer):
            if thread is not None and thread.ident is not None:
                thread.join(timeout=max(0.0, join_deadline - time.monotonic()))
        self.sink_stop.set()


@contextmanager
def _representative_preflight_diagnostics(deadline: float) -> Iterator[None]:
    """Fixed installed preflight only; no sink, callbacks, schedule or scope nomination."""
    diagnostics = None
    token = None
    try:
        if (
            _CONTEXT.get() is None
            and threading.current_thread() is threading.main_thread()
            and type(deadline) in (int, float)
            and math.isfinite(deadline)
        ):
            diagnostics = _PreflightDiagnostics(deadline)
            token = _CONTEXT.set(diagnostics)
            try:
                diagnostics.start()
            except Exception:
                diagnostics.close()
            _preflight_phase("diagnostics-start", deadline)
        yield
    finally:
        if diagnostics is not None:
            try:
                _preflight_phase("diagnostics-stop", deadline)
                diagnostics.close()
            except Exception:
                pass
        if token is not None:
            _CONTEXT.reset(token)


def _preflight_phase(phase: str, deadline: float, *, pid: int | None = None) -> None:
    """Drop mismatched clocks/owners/labels; actual child PID observations are explicit."""
    try:
        diagnostics = _CONTEXT.get()
        if (
            diagnostics is None
            or diagnostics.deadline != deadline
            or phase not in _PHASES
            or diagnostics.owner_pid != os.getpid()
            or diagnostics.owner_thread != threading.get_ident()
        ):
            return
        if phase in {"guardian-ready", "worker-popen-returned"}:
            if type(pid) is not int or not 0 < pid <= 2147483647:
                return
        elif pid is not None:
            return
        diagnostics.emit(phase, pid=pid)
    except Exception:
        pass


def _preflight_worker_phase(phase: str, purpose: str, deadline: float, *, pid: int | None = None) -> None:
    """Only the fixed Original worker role participates; no ordinary native-tool trace."""
    if purpose == "original-native-worker":
        _preflight_phase(phase, deadline, pid=pid)


def original_cell_progress(phase: str, scope: str, deadline: float) -> None:
    """Observe the unchanged clock without masking an actual expired outcome.

    Fixed labels and public scope only: no argv, environment, paths or receipts.
    A closed diagnostic stream cannot replace the retained OS/custody failure.
    """
    if (
        not isinstance(phase, str)
        or phase not in {"selection-start", "worker-start", "worker-completed", "terminal-observed"}
        or not isinstance(scope, str)
        or scope not in PUBLIC_PROJECT_NAMES
        or type(deadline) not in (float, int)
        or not math.isfinite(deadline)
    ):
        raise ValueError("Original progress requires fixed public phase/scope and the finite existing clock")
    if _CONTEXT.get() is not None:
        if scope == _SCOPE:
            _preflight_phase(phase, deadline)
        return
    observed = time.monotonic()
    value = {
        "schema_version": "template-native-original-progress-v1",
        "phase": phase,
        "scope": scope,
        "pid": os.getpid(),
        "observed_monotonic": observed,
        "remaining_seconds": deadline - observed,
    }
    try:
        print(json.dumps(value, sort_keys=True, allow_nan=False), file=sys.stderr, flush=True)
    except (OSError, ValueError):
        # Diagnostics grant no authority and must not launder the primary exit.
        pass
