"""Original native tool process observations; no Python audit label for tools."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import stat
import subprocess
import threading
import time
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from infrastructure.core._bounded_run_guardian import (
    _DONE,
    _expect_status,
    BoundedRunGuardian,
    start_bounded_run_guardian,
)
from infrastructure.core.execution_boundary import (
    build_bounded_env,
    build_bounded_run_env,
    terminate_bounded_run_processes,
    terminate_process_tree,
)
from infrastructure.reporting.native_format_portable_custody import (
    executable_observation,
)

SCHEMA = "template-original-native-tool-process-v1"
# Even six-byte JSON escaping of the complete text stays inside one 64 MiB artifact.
MAX_STREAM_BYTES = 8 * 1024 * 1024
_LIVE_OWNER_KEY = object()


class NativeLiveToolProcess:
    """A short-lived owner supplied directly by the real Popen supervisor.

    This object authenticates this process lifetime and command. It grants no
    browser, loaded-provider or kernel admission. The Source-owned interaction
    must retain its own observations and close its protocol before returning.
    No receipt parser can acquire this owner's actual Popen/guardian objects.
    """

    def __init__(
        self,
        process: subprocess.Popen[bytes],
        guardian: BoundedRunGuardian,
        command: tuple[str, ...],
        deadline: float,
        *,
        key: object,
    ) -> None:
        if key is not _LIVE_OWNER_KEY:
            raise ValueError("native live owner requires the actual supervisor factory")
        self._process = process
        self._guardian = guardian
        self._owner_pid = os.getpid()
        self._active = True
        self._command = command
        self._deadline = deadline
        self.verify_live()

    @property
    def pid(self) -> int:
        self.verify_live()
        return self._process.pid

    @property
    def command(self) -> tuple[str, ...]:
        self.verify_live()
        return self._command

    @property
    def deadline(self) -> float:
        self.verify_live()
        return self._deadline

    def verify_live(self) -> None:
        """Require this genuine still-active original owner and its same clock."""
        _remaining(self._deadline)
        actual_arguments = self._process.args
        if (
            not self._active
            or self._owner_pid != os.getpid()
            or self._process.poll() is not None
            or not isinstance(actual_arguments, (list, tuple))
            or tuple(actual_arguments) != self._command
            or not self._guardian.armed
            or self._guardian.process.poll() is not None
        ):
            raise ValueError("native interaction lost its actual live original process")

    def _close_owner(self) -> None:
        self._active = False


def _physical_identity(path: Path) -> dict[str, int]:
    """Retain actual executable metadata; this grants no loaded-library proof."""
    metadata = path.stat()
    return {
        "device": metadata.st_dev,
        "inode": metadata.st_ino,
        "mode": metadata.st_mode,
        "size": metadata.st_size,
        "mtime_ns": metadata.st_mtime_ns,
        "ctime_ns": metadata.st_ctime_ns,
        "links": metadata.st_nlink,
    }


def _nomination_observation(path: Path) -> dict[str, Any]:
    metadata = path.lstat()
    return {
        "device": metadata.st_dev,
        "inode": metadata.st_ino,
        "mode": metadata.st_mode,
        "size": metadata.st_size,
        "mtime_ns": metadata.st_mtime_ns,
        "ctime_ns": metadata.st_ctime_ns,
        "links": metadata.st_nlink,
        "symlink_target": os.readlink(path) if stat.S_ISLNK(metadata.st_mode) else None,
    }


def _stamp() -> dict[str, str | float]:
    return {
        "utc": datetime.now(timezone.utc).isoformat(),
        "monotonic": time.monotonic(),
    }


def _remaining(deadline: float) -> float:
    if type(deadline) not in (int, float) or not math.isfinite(deadline):
        raise ValueError("native tool requires the original finite absolute deadline")
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("native tool exhausted its original admitted deadline")
    return remaining


def _stream(path: Path) -> tuple[dict[str, Any], str]:
    digest = hashlib.sha256()
    size, chunks = 0, []
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
            size += len(chunk)
            if size > MAX_STREAM_BYTES:
                raise ValueError("native tool stream exceeds its finite retained byte ceiling")
            chunks.append(chunk)
    raw = b"".join(chunks)
    return {"path": str(path), "sha256": digest.hexdigest(), "bytes": size}, raw.decode("utf-8", errors="replace")


def _finish_guardian(guardian: BoundedRunGuardian, deadline: float) -> None:
    """Use its exact DONE protocol with the original deadline, no fresh wait budget."""
    _expect_status(
        guardian.status_fd,
        _DONE,
        timeout=_remaining(deadline),
        deadline_monotonic=deadline,
    )
    if guardian.process.wait(timeout=_remaining(deadline)) != 0:
        raise RuntimeError("native tool cleanup guardian returned an original nonzero exit")
    guardian.finished = True


def run_native_tool_process(
    directory: Path,
    name: str,
    arguments: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    deadline: float,
    purpose: str,
    preserve_nominated_launcher: bool = False,
    while_live: Callable[[NativeLiveToolProcess], None] | None = None,
) -> dict[str, Any]:
    """Own actual Popen/guardian PIDs, signed OS exit and complete raw streams.

    All accepted work, custody and retention use the same externally supplied
    finite deadline. The independently admitted originating caller authenticates
    these DATA observations; this function does not grant kernel/library proof.
    """
    _remaining(deadline)
    if while_live is not None and not callable(while_live):
        raise ValueError("native interaction requires a Source-owned callable")
    if type(preserve_nominated_launcher) is not bool or (
        preserve_nominated_launcher
        and (not Path(name).is_absolute() or re.fullmatch(r"python(?:[0-9]+(?:\.[0-9]+)*)?", Path(name).name) is None)
    ):
        raise ValueError("preserving a launcher requires an explicit absolute selected Python nomination")
    directory = directory.absolute()
    cwd = cwd.absolute()
    if (
        os.name != "posix"
        or directory != directory.resolve(strict=True)
        or cwd != cwd.resolve(strict=True)
        or not cwd.is_dir()
        or not isinstance(name, str)
        or not name
        or not isinstance(arguments, list)
        or any(not isinstance(item, str) or "\0" in item for item in arguments)
        or re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,180}", purpose) is None
    ):
        raise ValueError("native tool requires owned POSIX evidence and explicit command paths")
    stdout_path = directory / f"{purpose}.stdout.bin"
    stderr_path = directory / f"{purpose}.stderr.bin"
    record_path = directory / f"{purpose}.native-process.json"
    if any(path.exists() or path.is_symlink() for path in (stdout_path, stderr_path, record_path)):
        raise ValueError("native tool evidence paths must be fresh")
    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "owner_pid": os.getpid(),
        "original_deadline_monotonic": deadline,
        "operation_begin": _stamp(),
        "pid": None,
        "command": None,
        "nominated_command": None,
        "nomination": None,
        "executable_observation_before": None,
        "executable_observation_after": None,
        "launch_begin": None,
        "launch_returned": None,
        "root_reaped": None,
        "original_exit_code": None,
        "cwd": str(cwd),
        "diagnostics": [],
        "timed_out": False,
        "accepted": False,
    }
    process: subprocess.Popen[bytes] | None = None
    guardian: BoundedRunGuardian | None = None
    original_error: BaseException | None = None
    run_token = ""
    limit_refused = threading.Event()
    monitor_stop = threading.Event()
    monitor: threading.Thread | None = None

    def monitor_streams() -> None:
        while not monitor_stop.wait(0.05):
            try:
                total = sum(path.stat().st_size for path in (stdout_path, stderr_path))
                if total > MAX_STREAM_BYTES:
                    limit_refused.set()
                    if process is not None and process.poll() is None:
                        terminate_process_tree(process.pid, group_id=process.pid)
                    return
            except OSError:
                limit_refused.set()
                return

    cleanup: dict[str, Any] = {
        "guardian_pid": None,
        "guardian_original_exit_code": None,
        "guardian_armed": False,
        "guardian_finished": False,
        "final_token_sweep_matched_pids": None,
    }
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        try:
            selected_env = build_bounded_env(env)
            selected = shutil.which(name, path=selected_env.get("PATH"))
            if not selected:
                raise ValueError("actual nominated native tool is unavailable")
            nominated = Path(selected).absolute()
            executable = nominated.resolve(strict=True)
            payload["nomination"] = {
                "tool": name,
                "path": str(nominated),
                "resolved_path": str(executable),
            }
            payload["executable_observation_before"] = executable_observation(executable)
            payload["executable_identity_before"] = _physical_identity(executable)
            payload["nominated_command"] = [str(nominated), *arguments]
            payload["command"] = [str(nominated) if preserve_nominated_launcher else str(executable), *arguments]
            payload["launcher_preserved"] = preserve_nominated_launcher
            payload["nominated_identity_before"] = _nomination_observation(nominated)

            process_env, run_token = build_bounded_run_env(selected_env)
            guardian = start_bounded_run_guardian(
                selected_env,
                deadline_monotonic=deadline,
                startup_timeout_seconds=min(_remaining(deadline), 60.0),
            )
            if guardian is None:
                raise ValueError("actual native tool requires its independent owned guardian")
            cleanup["guardian_pid"] = guardian.process.pid
            _remaining(deadline)
            payload["launch_begin"] = _stamp()
            process = subprocess.Popen(
                payload["command"],
                cwd=cwd,
                env=process_env,
                stdin=subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
                start_new_session=True,
            )
            payload["pid"] = process.pid
            payload["launch_returned"] = _stamp()
            guardian.arm(root_pid=process.pid, run_token=run_token, deadline_monotonic=deadline)
            cleanup["guardian_armed"] = guardian.armed
            monitor = threading.Thread(target=monitor_streams, name="native-tool-owned-streams", daemon=True)
            monitor.start()
            if while_live is not None:
                interaction: dict[str, Any] = {"begin": _stamp(), "end": None, "completed": False}
                payload["live_interaction"] = interaction
                owner = NativeLiveToolProcess(
                    process, guardian, tuple(payload["command"]), deadline, key=_LIVE_OWNER_KEY
                )
                try:
                    while_live(owner)
                    # The callback may legitimately have closed Chrome through
                    # its own protocol. The supervisor alone reaps that real OS
                    # outcome; returning from a callback supplies no exit code.
                    _remaining(deadline)
                    interaction["completed"] = True
                finally:
                    owner._close_owner()
                    interaction["end"] = _stamp()
            process.wait(timeout=_remaining(deadline))
            payload["root_reaped"] = _stamp()
        except BaseException as error:
            original_error = error
            payload["diagnostics"].append(f"{type(error).__name__}: {error}")
            payload["timed_out"] = isinstance(error, (TimeoutError, subprocess.TimeoutExpired))
        finally:
            monitor_stop.set()
            if monitor is not None:
                monitor.join(timeout=max(0.0, deadline - time.monotonic()))
                if monitor.is_alive():
                    payload["diagnostics"].append(
                        "native tool stream monitor did not close inside the original deadline"
                    )
            if limit_refused.is_set():
                payload["diagnostics"].append("native tool aggregate stream byte ceiling refused")
            cleanup["begin"] = _stamp()
            try:
                try:
                    if process is not None and process.poll() is None:
                        terminate_process_tree(process.pid, group_id=process.pid)
                finally:
                    try:
                        if guardian is not None:
                            if guardian.armed:
                                _finish_guardian(guardian, deadline)
                            else:
                                guardian.close()
                            cleanup["guardian_finished"] = guardian.finished
                            cleanup["guardian_original_exit_code"] = guardian.process.returncode
                    finally:
                        cleanup["final_token_sweep_matched_pids"] = (
                            sorted(terminate_bounded_run_processes(run_token)) if run_token else []
                        )
            except BaseException as error:
                payload["diagnostics"].append(f"owned cleanup {type(error).__name__}: {error}")
                original_error = original_error or error
            finally:
                if guardian is not None:
                    try:
                        guardian.close()
                    except Exception as error:
                        payload["diagnostics"].append(f"guardian close {type(error).__name__}: {error}")
                    cleanup["guardian_original_exit_code"] = guardian.process.returncode
                if process is not None:
                    if process.poll() is None:
                        try:
                            process.wait(timeout=max(0.0, deadline - time.monotonic()))
                        except subprocess.TimeoutExpired:
                            payload["diagnostics"].append("native tool root not reaped inside the original deadline")
                    payload["original_exit_code"] = process.returncode
                    if process.returncode is not None and payload["root_reaped"] is None:
                        payload["root_reaped"] = _stamp()
                cleanup["root_reaped"] = process is not None and process.returncode is not None
                cleanup["end"] = _stamp()
    payload["cleanup"] = cleanup
    try:
        if payload["nomination"] is not None:
            nominated = Path(payload["nomination"]["path"])
            executable = Path(payload["nomination"]["resolved_path"])
            payload["nominated_identity_after"] = _nomination_observation(nominated)
            payload["executable_observation_after"] = executable_observation(executable)
            payload["executable_identity_after"] = _physical_identity(executable)
            if (
                nominated.resolve(strict=True) != executable
                or payload["nominated_identity_after"] != payload["nominated_identity_before"]
                or payload["executable_observation_after"] != payload["executable_observation_before"]
                or payload["executable_identity_after"] != payload["executable_identity_before"]
            ):
                raise ValueError("native tool nomination or executable bytes changed during observation")
    except Exception as error:
        payload["diagnostics"].append(f"original executable custody {type(error).__name__}: {error}")
    for channel, path in (("stdout", stdout_path), ("stderr", stderr_path)):
        try:
            payload[f"raw_{channel}"], payload[channel] = _stream(path)
            payload[f"{channel}_preview_truncated"] = False
        except Exception as error:
            payload["diagnostics"].append(f"original {channel} custody {type(error).__name__}: {error}")
    if sum(payload.get(f"raw_{channel}", {}).get("bytes", 0) for channel in ("stdout", "stderr")) > MAX_STREAM_BYTES:
        payload["diagnostics"].append("native tool aggregate retained stream byte ceiling refused")
    payload["operation_end"] = _stamp()
    expired = time.monotonic() >= deadline
    payload["timed_out"] = payload["timed_out"] or expired
    payload["accepted"] = (
        payload["pid"] is not None
        and type(payload["original_exit_code"]) is int
        and cleanup["guardian_armed"]
        and cleanup["guardian_finished"]
        and cleanup["root_reaped"]
        and cleanup["final_token_sweep_matched_pids"] == []
        and not payload["diagnostics"]
        and not payload["timed_out"]
    )
    with record_path.open("x") as record:
        record.write(json.dumps(payload, indent=2) + "\n")
    if time.monotonic() >= deadline:
        payload["timed_out"] = True
        payload["accepted"] = False
        payload["operation_end"] = _stamp()
        payload["diagnostics"].append("native tool evidence retention exceeded the original deadline")
        record_path.write_text(json.dumps(payload, indent=2) + "\n")
    if original_error is not None and not isinstance(original_error, Exception):
        raise original_error
    return payload
