"""Independent POSIX guardian for token-bound subprocess cleanup.

The bounded executor normally waits for a direct child and then removes any
detached descendants that inherited the run token.  A heavily loaded caller can
be descheduled after the direct child exits, however, which leaves a detached
writer time to act before caller-side cleanup begins.  This private helper is
started and armed before the bounded command is awaited.  It observes the root
process with a kernel exit notification where available and performs the same
token-bound cleanup independently of the caller's scheduler state.
"""

from __future__ import annotations

import contextlib
import json
import math
import os
import select
import subprocess  # nosec B404 - fixed internal guardian and ps commands
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

_READY = b"R"
_ARMED = b"A"
_DONE = b"D"
_ERROR = b"E"
_CUSTODY_REFUSED = b"C"
DEFAULT_GUARDIAN_STARTUP_TIMEOUT_SECONDS = 60.0
_DONE_TIMEOUT_SECONDS = 45.0
_BOOTSTRAP = """
import importlib, json, os, shutil, stat, sys
from pathlib import Path
prefix = Path(sys.argv.pop(1))
search_paths = json.loads(sys.argv.pop(1))
if not isinstance(search_paths, list) or any(not isinstance(path, str) for path in search_paths):
    raise ValueError('guardian requires explicit parent import directories')
metadata = prefix.lstat()
if (prefix != prefix.resolve(strict=True) or not stat.S_ISDIR(metadata.st_mode)
        or stat.S_IMODE(metadata.st_mode) != 0o700 or metadata.st_uid != os.getuid()
        or any(prefix.iterdir())):
    raise ValueError('guardian requires an empty private canonical bytecode prefix')
sys.pycache_prefix = str(prefix)
# Parent-admitted directories preserve installed metadata under -S, including
# wheel-only callers. Extending sys.path executes no .pth or sitecustomize code.
sys.path.extend(path for path in search_paths if path not in sys.path)
sys.path.insert(0, sys.argv.pop(1))
try:
    exec(compile(sys.argv.pop(1), '<guardian-audit-bootstrap>', 'exec'), {'__name__':'_guardian_audit_bootstrap'})
    guardian = importlib.import_module('infrastructure.core._bounded_run_guardian')
    raise SystemExit(guardian.main())
finally:
    # The parent retains its handle through reaping; this also removes the
    # private scratch after an abrupt caller exit that cannot run finalizers.
    shutil.rmtree(prefix, ignore_errors=True)
"""


class GuardianCustodyError(ValueError):
    """Admitted source or actual fresh imported implementation no longer agrees."""


@dataclass
class BoundedRunGuardian:
    """Parent-side handle for one independent cleanup guardian."""

    process: subprocess.Popen[bytes]
    control_fd: int
    status_fd: int
    armed: bool = False
    finished: bool = False
    cache: tempfile.TemporaryDirectory[str] | None = None
    startup_deadline_monotonic: float | None = None

    def _release_cache(self) -> None:
        if self.cache is not None and self.process.poll() is not None:
            self.cache.cleanup()
            self.cache = None

    def arm(self, *, root_pid: int, run_token: str, deadline_monotonic: float | None = None) -> None:
        """Bind the ready guardian to *root_pid* and its inherited token."""
        if self.armed:
            raise RuntimeError("bounded-run guardian is already armed")
        deadline = _effective_startup_deadline(self.startup_deadline_monotonic, deadline_monotonic)
        _start_wait_timeout(deadline)
        payload = f"{root_pid}\n{run_token}\n".encode("ascii")
        try:
            _write_all(self.control_fd, payload)
        finally:
            _close_fd(self.control_fd)
            self.control_fd = -1
        _expect_status(
            self.status_fd,
            _ARMED,
            timeout=_start_wait_timeout(deadline),
            deadline_monotonic=deadline,
        )
        self.armed = True

    def wait_for_cleanup(self) -> None:
        """Wait until root-exit cleanup is complete and reap the guardian."""
        if self.finished:
            return
        if not self.armed:
            raise RuntimeError("bounded-run guardian was not armed")
        try:
            _expect_status(self.status_fd, _DONE, timeout=_DONE_TIMEOUT_SECONDS)
            returncode = self.process.wait(timeout=5)
            if returncode != 0:
                raise RuntimeError(f"bounded-run guardian exited with status {returncode}")
            self.finished = True
        finally:
            _close_fd(self.status_fd)
            self.status_fd = -1
            self._release_cache()

    def close(self) -> None:
        """Close protocol descriptors and reap or terminate the guardian."""
        _close_fd(self.control_fd)
        _close_fd(self.status_fd)
        self.control_fd = -1
        self.status_fd = -1
        if self.process.poll() is None:
            with contextlib.suppress(OSError, ProcessLookupError):
                self.process.kill()
        with contextlib.suppress(OSError, subprocess.TimeoutExpired):
            self.process.wait(timeout=5)
        self._release_cache()


def start_bounded_run_guardian(
    env: dict[str, str],
    *,
    deadline_monotonic: float | None = None,
    startup_timeout_seconds: float = DEFAULT_GUARDIAN_STARTUP_TIMEOUT_SECONDS,
) -> BoundedRunGuardian | None:
    """Admit source, READY and ARM under one finite phase and the run deadline.

    The 60-second default accommodates measured fresh source-audited startup;
    it never extends the caller's original deadline or resets between phases.
    Source verification is mandatory; an overrun refuses subsequent launch.
    Returns ``None`` on Windows after validating the admitted budgets.
    """
    validate_guardian_startup_timeout(startup_timeout_seconds)
    startup_deadline = _effective_startup_deadline(time.monotonic() + startup_timeout_seconds, deadline_monotonic)
    _start_wait_timeout(startup_deadline)
    if os.name == "nt":
        return None
    control_read = control_write = status_read = status_write = -1
    process: subprocess.Popen[bytes] | None = None
    cache: tempfile.TemporaryDirectory[str] | None = None
    source_digest: str | None = None
    package_root = Path(__file__).resolve().parents[1]
    try:
        from infrastructure.core.implementation_custody import bytecode_audit_bootstrap
        from infrastructure.core.pipeline.fingerprints import paths_digest, verify_loaded_implementation

        try:
            verify_loaded_implementation()
            source_digest = paths_digest((package_root,), source=True)
        except (OSError, ValueError) as exc:
            raise GuardianCustodyError("guardian source custody refused before startup") from exc
        _start_wait_timeout(startup_deadline)
        cache = tempfile.TemporaryDirectory(prefix="template-guardian-bytecode-")
        # Canonicalize only the scratch directory we just created, including
        # macOS's /var alias; source admission remains the fingerprint guard.
        prefix = Path(cache.name).resolve(strict=True)
        audit_bootstrap = bytecode_audit_bootstrap((package_root, package_root.parent / "scripts"), prefix)
        control_read, control_write = os.pipe()
        status_read, status_write = os.pipe()
        _start_wait_timeout(startup_deadline)
        process = subprocess.Popen(
            [
                sys.executable,
                "-I",
                "-S",
                "-c",
                _BOOTSTRAP,
                str(prefix),
                json.dumps(sys.path),
                str(package_root.parent),
                audit_bootstrap,
                str(control_read),
                str(status_write),
                source_digest,
            ],
            cwd=str(Path(__file__).resolve().parents[2]),
            env=dict(env),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            pass_fds=(control_read, status_write),
            start_new_session=True,
        )
        _close_fd(control_read)
        _close_fd(status_write)
        control_read = -1
        status_write = -1
        guardian = BoundedRunGuardian(
            process=process,
            control_fd=control_write,
            status_fd=status_read,
            cache=cache,
            startup_deadline_monotonic=startup_deadline,
        )
        _expect_status(
            status_read,
            _READY,
            timeout=_start_wait_timeout(startup_deadline),
            deadline_monotonic=startup_deadline,
        )
        return guardian
    except BaseException as exc:
        for fd in (control_read, control_write, status_read, status_write):
            _close_fd(fd)
        if process is not None:
            if process.poll() is None:
                with contextlib.suppress(OSError, ProcessLookupError):
                    process.kill()
            with contextlib.suppress(OSError, subprocess.TimeoutExpired):
                process.wait(timeout=5)
        if cache is not None and (process is None or process.poll() is not None):
            cache.cleanup()
        # An import can fail before the child's typed handshake. Convert only
        # a positively observed change to the already admitted public tree;
        # unrelated setup errors and operator interruption keep their type.
        if (
            source_digest is not None
            and not isinstance(exc, GuardianCustodyError)
            and isinstance(exc, (OSError, RuntimeError, TimeoutError, ValueError))
        ):
            try:
                changed = paths_digest((package_root,), source=True) != source_digest
            except (OSError, ValueError):
                changed = True
            if changed:
                raise GuardianCustodyError("guardian source changed during startup") from exc
        raise


def validate_guardian_startup_timeout(value: float) -> None:
    """Reject nonnumeric, Boolean, nonfinite or nonpositive phase budgets."""
    if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
        raise ValueError("guardian startup timeout must be a positive finite number")


def _effective_startup_deadline(phase_deadline: float | None, run_deadline: float | None) -> float | None:
    deadlines = tuple(value for value in (phase_deadline, run_deadline) if value is not None)
    if any(type(value) not in (int, float) or not math.isfinite(value) for value in deadlines):
        raise ValueError("guardian deadline must be a finite number")
    return min(deadlines) if deadlines else None


def _start_wait_timeout(deadline_monotonic: float | None) -> float:
    if deadline_monotonic is None:
        return DEFAULT_GUARDIAN_STARTUP_TIMEOUT_SECONDS
    if type(deadline_monotonic) not in (int, float) or not math.isfinite(deadline_monotonic):
        raise ValueError("guardian deadline must be finite")
    remaining = deadline_monotonic - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("bounded-run guardian deadline expired before launch or handshake")
    return remaining


def _expect_status(
    fd: int,
    expected: bytes,
    *,
    timeout: float,
    deadline_monotonic: float | None = None,
) -> None:
    ready, _, _ = select.select([fd], [], [], timeout)
    if not ready:
        raise TimeoutError(f"timed out waiting for bounded-run guardian status {expected!r}")
    if deadline_monotonic is not None:
        _start_wait_timeout(deadline_monotonic)
    observed = os.read(fd, 1)
    if observed == _CUSTODY_REFUSED:
        raise GuardianCustodyError("bounded-run guardian refused implementation custody")
    if observed == _ERROR:
        raise RuntimeError("bounded-run guardian reported an internal error")
    if observed != expected:
        raise RuntimeError(f"bounded-run guardian status {observed!r}; expected {expected!r}")


def _write_all(fd: int, payload: bytes) -> None:
    view = memoryview(payload)
    while view:
        written = os.write(fd, view)
        view = view[written:]


def _close_fd(fd: int) -> None:
    if fd < 0:
        return
    with contextlib.suppress(OSError):
        os.close(fd)


def _wait_for_process_exit(pid: int, status_fd: int) -> None:
    """Arm a kernel exit watcher, acknowledge it, and wait for *pid*."""
    if hasattr(os, "pidfd_open"):
        try:
            pid_fd = os.pidfd_open(pid)
        except ProcessLookupError:
            _write_all(status_fd, _ARMED)
            return
        try:
            _write_all(status_fd, _ARMED)
            select.select([pid_fd], [], [])
        finally:
            os.close(pid_fd)
        return

    if sys.platform == "darwin" and hasattr(select, "kqueue"):
        queue = select.kqueue()
        try:
            event = select.kevent(
                pid,
                filter=select.KQ_FILTER_PROC,
                flags=select.KQ_EV_ADD | select.KQ_EV_ENABLE | select.KQ_EV_ONESHOT,
                fflags=select.KQ_NOTE_EXIT,
            )
            try:
                immediate = queue.control([event], 1, 0)
            except ProcessLookupError:
                _write_all(status_fd, _ARMED)
                return
            _write_all(status_fd, _ARMED)
            if not immediate:
                queue.control([], 1, None)
        finally:
            queue.close()
        return

    _write_all(status_fd, _ARMED)
    while _process_is_running(pid):
        time.sleep(0.05)


def _process_is_running(pid: int) -> bool:
    """Fallback process-state probe that treats zombies as exited."""
    ps_command = "/bin/ps" if Path("/bin/ps").is_file() else "ps"
    try:
        completed = subprocess.run(  # nosec B603 - fixed process-state query
            [ps_command, "-o", "stat=", "-p", str(pid)],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        # An unavailable probe is not evidence that the target exited.  Keep
        # waiting so a transient ps failure cannot trigger premature cleanup
        # of a still-running bounded command.
        return True
    state = completed.stdout.strip()
    return completed.returncode == 0 and bool(state) and not state.startswith("Z")


def _verify_guardian_implementation(source_digest: str) -> None:
    from infrastructure.core.implementation_custody import verify_fresh_module_bytecode
    from infrastructure.core.pipeline.fingerprints import paths_digest, verify_loaded_implementation

    prefix = sys.pycache_prefix
    if not prefix:
        raise ValueError("guardian has no owned fresh bytecode prefix")
    package_root = Path(__file__).resolve().parents[1]
    try:
        verify_loaded_implementation()
        if paths_digest((package_root,), source=True) != source_digest:
            raise ValueError("guardian implementation changed after parent admission")
        verify_fresh_module_bytecode(package_root, Path(prefix))
    except (OSError, ValueError) as exc:
        raise GuardianCustodyError("guardian implementation custody refused") from exc


def _guardian_main(control_fd: int, status_fd: int, source_digest: str) -> int:
    try:
        # Import cleanup before the handshake, under the owned empty cache,
        # so root exit never waits on public imports or uses inherited pyc.
        from infrastructure.core.execution_boundary import terminate_bounded_run_processes

        _verify_guardian_implementation(source_digest)
        _write_all(status_fd, _READY)
        with os.fdopen(control_fd, "rb", closefd=True) as control:
            payload = control.read().decode("ascii")
        root_pid_text, run_token = payload.splitlines()
        root_pid = int(root_pid_text)
        _wait_for_process_exit(root_pid, status_fd)

        terminate_bounded_run_processes(run_token)
        # Always clean the admitted process token first, even if source bytes
        # changed while waiting. Such a run still cannot report clean success.
        _verify_guardian_implementation(source_digest)
        _write_all(status_fd, _DONE)
        return 0
    except GuardianCustodyError:
        with contextlib.suppress(OSError):
            _write_all(status_fd, _CUSTODY_REFUSED)
        return 75
    except BaseException:
        with contextlib.suppress(OSError):
            _write_all(status_fd, _ERROR)
        return 1
    finally:
        _close_fd(status_fd)


def main(argv: list[str] | None = None) -> int:
    """Run the internal two-pipe guardian protocol."""
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 3:
        return 2
    try:
        control_fd, status_fd = (int(value) for value in args[:2])
    except ValueError:
        return 2
    return _guardian_main(control_fd, status_fd, args[2])


if __name__ == "__main__":
    raise SystemExit(main())
