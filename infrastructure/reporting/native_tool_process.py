"""Original native tool process observations; no Python audit label for tools."""

from __future__ import annotations

import contextvars
import json
import os
import re
import shutil
import subprocess
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, TYPE_CHECKING

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
from infrastructure.reporting.native_original_progress import _preflight_worker_phase

from infrastructure.reporting.native_tool_process_inputs import (
    _nomination_observation as _nomination_observation,
    _physical_identity as _physical_identity,
    _remaining as _remaining,
    _stamp as _stamp,
    _stdin_observation as _stdin_observation,
    _stream as _stream,
)

if TYPE_CHECKING:
    from infrastructure.reporting.native_loader_observation import NativeLoaderObservation

SCHEMA = "template-original-native-tool-process-v1"
STDIN_SCHEMA = "template-original-native-tool-stdin-process-v2"
LOADER_SCHEMA = "template-original-native-loader-tool-process-v3"
# Even six-byte JSON escaping of the complete text stays inside one 64 MiB artifact.
MAX_STREAM_BYTES = 8 * 1024 * 1024
_LIVE_OWNER_KEY = object()


class NativeLiveToolProcess:
    """Actual Popen/guardian custody; serialized DATA cannot acquire it."""

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

    def observe_original_os_exit(self) -> int:
        """Reap this genuine Popen's signed OS result, preserving its clock."""
        _remaining(self._deadline)
        actual_arguments = self._process.args
        if (
            not self._active
            or self._owner_pid != os.getpid()
            or not isinstance(actual_arguments, (list, tuple))
            or tuple(actual_arguments) != self._command
            or not self._guardian.armed
            or self._guardian.process.poll() is not None
        ):
            raise ValueError("original OS reaping lost its actual supervisor-held Popen/guardian")
        outcome = self._process.wait(timeout=_remaining(self._deadline))
        _remaining(self._deadline)
        if type(outcome) is not int:
            raise ValueError("original OS reaping lacks the actual signed kernel exit result")
        return outcome

    def _close_owner(self) -> None:
        self._active = False


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
    stdin_path: Path | None = None,
    loader: NativeLoaderObservation | None = None,
    observed_processes: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Retain actual Popen/guardian outcomes under the original finite clock."""
    _remaining(deadline)
    if observed_processes is not None and not isinstance(observed_processes, list):
        raise ValueError("actual native OS observation sink must be a list")
    if loader is not None:
        from infrastructure.reporting.native_loader_observation import NativeLoaderObservation

        if type(loader) is not NativeLoaderObservation:
            raise ValueError("native loader requires the fixed Source/actual compiler capability")
        loader.compiled.verify(deadline=deadline)
    if while_live is not None and not callable(while_live):
        raise ValueError("native interaction requires a Source-owned callable")
    if type(preserve_nominated_launcher) is not bool or (
        preserve_nominated_launcher
        and name not in {"xelatex", "lualatex", "pdflatex"}
        and (not Path(name).is_absolute() or re.fullmatch(r"python(?:[0-9]+(?:\.[0-9]+)*)?", Path(name).name) is None)
    ):
        raise ValueError("preserving a launcher requires an absolute selected Python or fixed TeX engine nomination")
    directory = directory.absolute()
    cwd = cwd.absolute()
    if stdin_path is not None and (
        not isinstance(stdin_path, Path)
        or not stdin_path.is_absolute()
        or not stdin_path.is_relative_to(directory)
        or stdin_path != stdin_path.resolve(strict=True)
        or stdin_path.is_symlink()
    ):
        raise ValueError("native stdin must be an exact owned private-directory input")
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
        "environment_custody": None,
    }
    process: subprocess.Popen[bytes] | None = None
    guardian: BoundedRunGuardian | None = None
    original_error: BaseException | None = None
    run_token = ""
    limit_refused = threading.Event()
    monitor_stop = threading.Event()
    monitor: threading.Thread | None = None
    stdin_stream = None
    loader_thread: threading.Thread | None = None
    loader_errors: list[BaseException] = []
    loader_owner: NativeLiveToolProcess | None = None

    def collect_loader() -> None:
        try:
            if loader is None or loader_owner is None:
                raise ValueError("actual loader observer lost its Source/Popen capability")
            loader.collect(loader_owner)
        except BaseException as error:
            loader_errors.append(error)

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
    _preflight_worker_phase("streams-open-begin", purpose, deadline)
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        _preflight_worker_phase("streams-open-end", purpose, deadline)
        try:
            if stdin_path is not None:
                stdin_stream = os.fdopen(
                    os.open(stdin_path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC),
                    "rb",
                )
                payload["schema_version"] = STDIN_SCHEMA
                payload["stdin_input_before"] = _stdin_observation(stdin_stream, stdin_path, deadline)
            from infrastructure.reporting._native_hosted_launch import current_fixed_reader_launch

            hosted_route = current_fixed_reader_launch(
                directory, name, arguments, cwd=cwd, environment=env, deadline=deadline, purpose=purpose
            )
            if hosted_route is not None and (
                loader is not None
                or stdin_path is not None
                or while_live is not None
                or not preserve_nominated_launcher
            ):
                raise ValueError("fixed hosted reader cannot select another native instrumentation/interaction role")
            _preflight_worker_phase("nomination-begin", purpose, deadline)
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
            payload["command"] = [
                str(nominated) if preserve_nominated_launcher else str(executable),
                *arguments,
            ]
            payload["launcher_preserved"] = preserve_nominated_launcher
            payload["nominated_identity_before"] = _nomination_observation(nominated)
            _preflight_worker_phase("nomination-end", purpose, deadline)

            _preflight_worker_phase("guardian-start", purpose, deadline)
            process_env, run_token = build_bounded_run_env(selected_env)
            bounded_env = dict(process_env)
            guardian = start_bounded_run_guardian(
                selected_env,
                deadline_monotonic=deadline,
                startup_timeout_seconds=min(_remaining(deadline), 60.0),
            )
            if guardian is None:
                raise ValueError("actual native tool requires its independent owned guardian")
            cleanup["guardian_pid"] = guardian.process.pid
            _preflight_worker_phase("guardian-ready", purpose, deadline, pid=guardian.process.pid)
            _remaining(deadline)
            payload["launch_begin"] = _stamp()
            if loader is not None:
                # Instrument only this exact Source-owned qualification launch;
                # guardian/env sanitation and all ordinary launches stay intact.
                process_env = loader.prepare_env(process_env, deadline=deadline, purpose=purpose)
                payload["schema_version"] = LOADER_SCHEMA
                payload["loader_stdin"] = stdin_stream is not None
            from infrastructure.reporting.native_environment_custody import capture_native_environment

            _preflight_worker_phase("environment-begin", purpose, deadline)
            if hosted_route is not None:
                process_env, payload["environment_custody"] = hosted_route.capture(selected_env, bounded_env, run_token)
            else:
                payload["environment_custody"] = capture_native_environment(
                    env, selected_env, bounded_env, process_env, run_token, loader
                )
            _preflight_worker_phase("environment-end", purpose, deadline)
            _preflight_worker_phase("worker-popen-begin", purpose, deadline)
            process = subprocess.Popen(
                payload["command"],
                cwd=cwd,
                env=process_env,
                stdin=stdin_stream if stdin_stream is not None else subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
                start_new_session=True,
            )
            _preflight_worker_phase("worker-popen-returned", purpose, deadline, pid=process.pid)
            payload["pid"] = process.pid
            payload["launch_returned"] = _stamp()
            _preflight_worker_phase("arm-begin", purpose, deadline)
            guardian.arm(root_pid=process.pid, run_token=run_token, deadline_monotonic=deadline)
            _preflight_worker_phase("arm-end", purpose, deadline)
            cleanup["guardian_armed"] = guardian.armed
            monitor = threading.Thread(target=monitor_streams, name="native-tool-owned-streams", daemon=True)
            monitor.start()
            if loader is not None:
                loader_owner = NativeLiveToolProcess(
                    process,
                    guardian,
                    tuple(payload["command"]),
                    deadline,
                    key=_LIVE_OWNER_KEY,
                )
                context = contextvars.copy_context()
                loader_thread = threading.Thread(
                    target=lambda: context.run(collect_loader),
                    name="native-tool-source-loader-callbacks",
                    daemon=True,
                )
                loader_thread.start()
            if while_live is not None:
                interaction: dict[str, Any] = {
                    "begin": _stamp(),
                    "end": None,
                    "completed": False,
                }
                payload["live_interaction"] = interaction
                owner = NativeLiveToolProcess(
                    process,
                    guardian,
                    tuple(payload["command"]),
                    deadline,
                    key=_LIVE_OWNER_KEY,
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
            _preflight_worker_phase("wait-begin", purpose, deadline)
            process.wait(timeout=_remaining(deadline))
            _preflight_worker_phase("wait-end", purpose, deadline)
            payload["root_reaped"] = _stamp()
            if loader_thread is not None:
                loader_thread.join(timeout=_remaining(deadline))
                if loader_thread.is_alive():
                    raise TimeoutError("actual loader callbacks failed to finish in their original tool clock")
                if loader_errors:
                    raise loader_errors[0]
                if loader is None:
                    raise ValueError("actual loader thread lost its genuine observer")
                payload["loader_lifecycle"] = loader.finish({**payload, "original_exit_code": process.returncode})
        except BaseException as error:
            original_error = error
            payload["diagnostics"].append(f"{type(error).__name__}: {error}")
            payload["timed_out"] = isinstance(error, (TimeoutError, subprocess.TimeoutExpired))
        finally:
            _preflight_worker_phase("cleanup-begin", purpose, deadline)
            if loader_thread is not None and loader_thread.is_alive():
                if loader is not None:
                    loader.abort()
                loader_thread.join(timeout=max(0.0, deadline - time.monotonic()))
                if loader_thread.is_alive():
                    payload["diagnostics"].append("actual Source loader thread did not close inside original deadline")
            if loader_owner is not None:
                loader_owner._close_owner()
            if stdin_stream is not None:
                try:
                    if stdin_path is None:
                        raise ValueError("native stdin lost its actual prelaunch path")
                    payload["stdin_input_after"] = _stdin_observation(stdin_stream, stdin_path, deadline)
                    if payload["stdin_input_before"] != payload["stdin_input_after"]:
                        raise ValueError("native stdin changed while the actual child consumed it")
                except Exception as error:
                    payload["diagnostics"].append(f"original stdin custody {type(error).__name__}: {error}")
                    original_error = original_error or error
                finally:
                    stdin_stream.close()
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
                _preflight_worker_phase("cleanup-end", purpose, deadline)
    payload["cleanup"] = cleanup
    _preflight_worker_phase("retention-begin", purpose, deadline)
    if observed_processes is not None:
        # Direct independently reaped Popen/guardian facts survive later
        # executable/stream/JSON retention failure. They remain DATA and cannot
        # grant actual original-tool capability or successful completion.
        observed_processes.append(
            {
                key: payload.get(key)
                for key in ("pid", "owner_pid", "command", "original_exit_code", "timed_out", "diagnostics")
            }
        )
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
    _preflight_worker_phase("retention-end", purpose, deadline)
    return payload
