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
import os
import select
import subprocess  # nosec B404 - fixed internal guardian and ps commands
import sys
import time
from dataclasses import dataclass
from pathlib import Path

_READY = b"R"
_ARMED = b"A"
_DONE = b"D"
_ERROR = b"E"
_START_TIMEOUT_SECONDS = 10.0
_DONE_TIMEOUT_SECONDS = 45.0


@dataclass
class BoundedRunGuardian:
    """Parent-side handle for one independent cleanup guardian."""

    process: subprocess.Popen[bytes]
    control_fd: int
    status_fd: int
    armed: bool = False
    finished: bool = False

    def arm(self, *, root_pid: int, run_token: str) -> None:
        """Bind the ready guardian to *root_pid* and its inherited token."""
        if self.armed:
            raise RuntimeError("bounded-run guardian is already armed")
        payload = f"{root_pid}\n{run_token}\n".encode("ascii")
        try:
            _write_all(self.control_fd, payload)
        finally:
            _close_fd(self.control_fd)
            self.control_fd = -1
        _expect_status(self.status_fd, _ARMED, timeout=_START_TIMEOUT_SECONDS)
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


def start_bounded_run_guardian(env: dict[str, str]) -> BoundedRunGuardian | None:
    """Start and handshake with a guardian, returning ``None`` on Windows."""
    if os.name == "nt":
        return None
    control_read = control_write = status_read = status_write = -1
    process: subprocess.Popen[bytes] | None = None
    try:
        control_read, control_write = os.pipe()
        status_read, status_write = os.pipe()
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "infrastructure.core._bounded_run_guardian",
                str(control_read),
                str(status_write),
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
        )
        _expect_status(status_read, _READY, timeout=_START_TIMEOUT_SECONDS)
        return guardian
    except BaseException:
        for fd in (control_read, control_write, status_read, status_write):
            _close_fd(fd)
        if process is not None:
            if process.poll() is None:
                with contextlib.suppress(OSError, ProcessLookupError):
                    process.kill()
            with contextlib.suppress(OSError, subprocess.TimeoutExpired):
                process.wait(timeout=5)
        raise


def _expect_status(fd: int, expected: bytes, *, timeout: float) -> None:
    ready, _, _ = select.select([fd], [], [], timeout)
    if not ready:
        raise TimeoutError(f"timed out waiting for bounded-run guardian status {expected!r}")
    observed = os.read(fd, 1)
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


def _guardian_main(control_fd: int, status_fd: int) -> int:
    try:
        _write_all(status_fd, _READY)
        with os.fdopen(control_fd, "rb", closefd=True) as control:
            payload = control.read().decode("ascii")
        root_pid_text, run_token = payload.splitlines()
        root_pid = int(root_pid_text)
        _wait_for_process_exit(root_pid, status_fd)

        # Import only after the watcher is armed so module import time cannot
        # widen the post-root-exit cleanup window.
        from infrastructure.core.execution_boundary import terminate_bounded_run_processes

        terminate_bounded_run_processes(run_token)
        _write_all(status_fd, _DONE)
        return 0
    except BaseException:
        with contextlib.suppress(OSError):
            _write_all(status_fd, _ERROR)
        return 1
    finally:
        _close_fd(status_fd)


def main(argv: list[str] | None = None) -> int:
    """Run the internal two-pipe guardian protocol."""
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2:
        return 2
    try:
        control_fd, status_fd = (int(value) for value in args)
    except ValueError:
        return 2
    return _guardian_main(control_fd, status_fd)


if __name__ == "__main__":
    raise SystemExit(main())
