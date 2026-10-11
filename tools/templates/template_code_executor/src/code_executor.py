"""Finite host-code execution with an independent POSIX descendant guardian.

This supervises processes under the current user. Operating-system isolation is
a separate responsibility; the installed tool needs only the Python runtime.
"""

from __future__ import annotations

import contextlib
import json
import math
import os
import select
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from pathlib import Path

# Isolated startup deliberately omits the script directory; admit only the
# supervisor's adjacent, bundled implementation module.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from process_cleanup import TOKEN_KEY as _TOKEN_KEY, kill_group as _kill_group, kill_tagged as _kill_tagged

_OUTPUT_LIMIT = 1024 * 1024
_INPUT_LIMIT = 64 * 1024


def _environment() -> dict[str, str]:
    markers = ("TOKEN", "SECRET", "PASSWORD", "API_KEY", "PRIVATE_KEY", "CREDENTIAL")
    return {
        key: value
        for key, value in os.environ.items()
        if not any(marker in key.upper() for marker in markers) and key not in {"PYTHONPATH", "PYTHONHOME"}
    }


def _guardian(control: int, status: int, token: str, deadline: float) -> int:
    """Watch command exit, parent pipe closure or deadline independently."""
    pid = None
    try:
        os.write(status, b"R")
        if not select.select([control], [], [], 5)[0]:
            raise TimeoutError("guardian was not armed")
        text = os.read(control, 64).decode()
        if not text:
            return 0
        pid = int(text.strip())
        pidfd = None
        queue = None
        try:
            if hasattr(os, "pidfd_open"):
                try:
                    pidfd = os.pidfd_open(pid)
                except ProcessLookupError:
                    pass
            elif hasattr(select, "kqueue"):
                queue = select.kqueue()
                try:
                    queue.control(
                        [
                            select.kevent(
                                pid,
                                filter=select.KQ_FILTER_PROC,
                                flags=select.KQ_EV_ADD | select.KQ_EV_ENABLE | select.KQ_EV_ONESHOT,
                                fflags=select.KQ_NOTE_EXIT,
                            )
                        ],
                        0,
                        0,
                    )
                except ProcessLookupError:
                    queue.close()
                    queue = None
            else:
                raise RuntimeError("guardian requires a supported POSIX exit watcher")
            os.write(status, b"A")
            while time.monotonic() < deadline:
                if select.select([control], [], [], 0)[0]:
                    break
                remaining = min(0.05, max(0, deadline - time.monotonic()))
                if pidfd is not None:
                    if select.select([pidfd], [], [], remaining)[0]:
                        break
                elif queue is not None:
                    if queue.control([], 1, remaining):
                        break
                else:
                    break
        finally:
            if pidfd is not None:
                os.close(pidfd)
            if queue is not None:
                queue.close()
        _kill_group(pid)
        _kill_tagged(token)
        os.write(status, b"D")
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        if pid is not None:
            _kill_group(pid)
        with contextlib.suppress(OSError):
            os.write(status, b"E" + str(error).encode()[:2048])
        return 1
    finally:
        os.close(control)
        os.close(status)


def _expect(descriptor: int, value: bytes) -> None:
    if not select.select([descriptor], [], [], 8)[0]:
        raise RuntimeError("independent descendant guardian failed its handshake")
    observed = os.read(descriptor, 1)
    if observed == b"E":
        raise RuntimeError("independent descendant guardian refused: " + os.read(descriptor, 2048).decode())
    if observed != value:
        raise RuntimeError(f"independent descendant guardian expected {value!r}, observed {observed!r}")


def execute(payload: dict) -> dict:
    """Run one bounded command and preserve its real child code and captured bytes."""
    timeout = payload.get("timeout_s", 30)
    code = payload.get("code")
    language = payload.get("language", "python")
    if (
        type(timeout) not in {int, float}
        or not math.isfinite(timeout)
        or not 0 < timeout <= 300
        or not isinstance(code, str)
        or not code.strip()
        or len(code.encode()) > _INPUT_LIMIT
        or not isinstance(language, str)
        or language not in {"python", "python3", "bash", "sh"}
    ):
        raise ValueError("code/language/timeout requires nonempty code and a finite budget in (0, 300]")
    if os.name != "posix":
        raise RuntimeError("the portable guardian requires POSIX process supervision")
    deadline = time.monotonic() + timeout
    token = uuid.uuid4().hex
    environment = _environment()
    child_env = {**environment, _TOKEN_KEY: token}
    control_read, control_write = os.pipe()
    status_read, status_write = os.pipe()
    try:
        guardian = subprocess.Popen(
            [
                sys.executable,
                "-I",
                str(Path(__file__).resolve()),
                "--guard",
                str(control_read),
                str(status_write),
                token,
                str(deadline),
            ],
            env=environment,
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            pass_fds=(control_read, status_write),
        )
    except BaseException:
        for descriptor in (control_read, control_write, status_read, status_write):
            os.close(descriptor)
        raise
    os.close(control_read)
    os.close(status_write)
    process = None
    completed = False
    overflow = threading.Event()
    buffers = [bytearray(), bytearray()]
    try:
        _expect(status_read, b"R")
        if time.monotonic() >= deadline:
            return {
                "exit_code": 124,
                "child_exit_code": None,
                "timed_out": True,
                "output_truncated": False,
                "stdout": "",
                "stderr": "startup deadline exhausted",
            }
        with tempfile.TemporaryDirectory(prefix="template-code-executor-") as directory:
            program = Path(directory) / ("program.py" if language.startswith("python") else "program.sh")
            program.write_text(code)
            executable = sys.executable if language.startswith("python") else shutil.which("bash")
            if executable is None:
                raise RuntimeError("selected shell runtime is missing")
            command = [executable, "-I", str(program)] if language.startswith("python") else [executable, str(program)]
            process = subprocess.Popen(
                command,
                env=child_env,
                start_new_session=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            os.write(control_write, f"{process.pid}\n".encode())
            _expect(status_read, b"A")

            def capture(stream, buffer):
                while content := stream.read(65536):
                    capacity = max(0, _OUTPUT_LIMIT - len(buffer))
                    buffer.extend(content[:capacity])
                    if len(content) > capacity:
                        overflow.set()

            threads = [
                threading.Thread(target=capture, args=(stream, buffer), daemon=True)
                for stream, buffer in zip((process.stdout, process.stderr), buffers, strict=True)
            ]
            for thread in threads:
                thread.start()
            while process.poll() is None and time.monotonic() < deadline and not overflow.is_set():
                time.sleep(0.01)
            expired = time.monotonic() >= deadline
            if expired or overflow.is_set():
                _kill_group(process.pid)
            child_code = process.wait(timeout=5)
            os.close(control_write)
            control_write = -1
            _expect(status_read, b"D")
            if guardian.wait(timeout=5):
                raise RuntimeError("independent descendant guardian refused completion")
            for thread in threads:
                thread.join(timeout=5)
                if thread.is_alive():
                    raise RuntimeError("command output did not close after descendant cleanup")
            _kill_tagged(token)
            for stream in (process.stdout, process.stderr):
                if stream is not None:
                    stream.close()
            result = {
                "exit_code": 124 if expired else 1 if overflow.is_set() else child_code,
                "child_exit_code": child_code,
                "timed_out": expired,
                "output_truncated": overflow.is_set(),
                "stdout": buffers[0].decode(errors="replace"),
                "stderr": buffers[1].decode(errors="replace"),
            }
            expired = expired or time.monotonic() >= deadline
            result["timed_out"] = expired
            if expired:
                result["exit_code"] = 124
            completed = True
            return result
    finally:
        if process is not None:
            if process.poll() is None:
                _kill_group(process.pid)
                with contextlib.suppress(subprocess.TimeoutExpired):
                    process.wait(timeout=5)
        if control_write >= 0:
            os.close(control_write)
        os.close(status_read)
        with contextlib.suppress(subprocess.TimeoutExpired):
            guardian.wait(timeout=8)
        if guardian.poll() is None:
            guardian.kill()
            guardian.wait(timeout=5)
        if process is not None and not completed:
            _kill_tagged(token)
            for stream in (process.stdout, process.stderr):
                if stream is not None:
                    stream.close()


def _read_input() -> bytes:
    """Bound both JSON bytes and slow/never-completing stdin before execution."""
    deadline = time.monotonic() + 5
    content = bytearray()
    while time.monotonic() < deadline:
        if not select.select([sys.stdin], [], [], max(0, deadline - time.monotonic()))[0]:
            break
        chunk = os.read(sys.stdin.fileno(), _INPUT_LIMIT + 1 - len(content))
        if not chunk:
            return bytes(content)
        content.extend(chunk)
        if len(content) > _INPUT_LIMIT:
            raise ValueError("executor input exceeds 64 KiB")
    raise TimeoutError("executor stdin deadline exhausted")


def main() -> int:
    if len(sys.argv) == 6 and sys.argv[1] == "--guard":
        return _guardian(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], float(sys.argv[5]))
    try:
        payload = json.loads(_read_input())
        if not isinstance(payload, dict):
            raise ValueError("executor input must be an object")
        print(json.dumps(execute(payload), allow_nan=False))
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(json.dumps({"exit_code": 2, "stdout": "", "stderr": str(error)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
