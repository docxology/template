"""Bounded original auxiliary child supervision and raw OS observations."""

from __future__ import annotations

import hashlib
import math
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from infrastructure.core._bounded_kill import observe_bounded_run_processes
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
from infrastructure.project.public_acceptance_evidence import cell_environment, evidence_directory

PROCESS_SCHEMA = "template-auxiliary-process-v3"
MAX_STREAM_BYTES = 16 * 1024 * 1024
_CENSUS_DIAGNOSTIC_INTS = (
    ("pid", 1, 2**31 - 1),
    ("caller_uid", 0, 2**32 - 1),
    ("caller_euid", 0, 2**32 - 1),
    ("caller_gid", 0, 2**32 - 1),
    ("caller_egid", 0, 2**32 - 1),
    ("uid_real", 0, 2**32 - 1),
    ("uid_effective", 0, 2**32 - 1),
    ("uid_saved", 0, 2**32 - 1),
    ("uid_fs", 0, 2**32 - 1),
    ("gid_real", 0, 2**32 - 1),
    ("gid_effective", 0, 2**32 - 1),
    ("gid_saved", 0, 2**32 - 1),
    ("gid_fs", 0, 2**32 - 1),
    ("ppid", 0, 2**31 - 1),
    ("tracer_pid", 0, 2**31 - 1),
    ("cap_prm", 0, 2**64 - 1),
    ("cap_eff", 0, 2**64 - 1),
    ("environ_uid", 0, 2**32 - 1),
    ("environ_gid", 0, 2**32 - 1),
    ("environ_mode", 0, 0o7777),
)
_CENSUS_DIAGNOSTIC_ENUMS = (
    ("comm", frozenset({"python", "ps", "node", "Runner.Worker", "ssh-agent", "gpg-agent", "other"})),
    ("probe_status", frozenset({"collected", "partial", "unavailable", "deadline"})),
)


def complete_auxiliary_observation(process: Any) -> bool:
    """Check complete process DATA; source, original launch and artifact authority remain external."""
    return (
        isinstance(process, dict)
        and process.get("schema_version") == PROCESS_SCHEMA
        and process.get("accepted") is True
        and isinstance(process.get("cleanup"), dict)
        and process["cleanup"].get("verified") is True
        and process["cleanup"].get("final_census_succeeded") is True
        and process["cleanup"].get("final_census_matched_pids") == []
        and type(process.get("pid")) is int
        and process["pid"] > 0
        and type(process.get("exit_code")) is int
        and process.get("timed_out") is False
        and process.get("output_limit_exceeded") is False
    )


def _remaining(deadline: float) -> float:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("original auxiliary deadline exhausted before launch or completion")
    return remaining


def _census_error_diagnostic(error: BaseException, deadline: float) -> dict[str, Any]:
    """Retain optional post-refusal kernel DATA without granting census authority."""
    cause = error.__cause__ if error.__cause__ is not None else error
    result: dict[str, Any] = {
        "type": type(error).__name__,
        "cause": type(error.__cause__).__name__ if error.__cause__ is not None else None,
        "errno": getattr(cause, "errno", None),
    }
    filename = getattr(cause, "filename", None)
    match = re.fullmatch(r"/proc/([1-9][0-9]{0,9})/environ", filename) if type(filename) is str else None
    if sys.platform != "linux" or match is None or int(match[1]) >= 2**31:
        return result
    pid = int(match[1])
    facts: dict[str, Any] = {"pid": pid, "probe_status": "unavailable"}
    result["procfs"] = facts

    def read_leaf(name: str, limit: int) -> bytes:
        _remaining(deadline)
        descriptor = os.open(f"/proc/{pid}/{name}", os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            _remaining(deadline)
            if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                raise ValueError("diagnostic proc leaf is not regular")
            _remaining(deadline)
            raw = os.read(descriptor, limit)
            _remaining(deadline)
            if len(raw) == limit:
                raise ValueError("diagnostic proc leaf exceeds its bound")
            return raw
        finally:
            os.close(descriptor)

    failures = 0
    try:
        if type(deadline) not in (int, float) or not math.isfinite(deadline):
            return result
        _remaining(deadline)
        for name, getter in (("uid", os.getuid), ("euid", os.geteuid), ("gid", os.getgid), ("egid", os.getegid)):
            facts["caller_" + name] = getter()
        _remaining(deadline)
        try:
            raw = read_leaf("status", 16 * 1024)
            for line in raw.splitlines():
                key, _, value = line.partition(b":")
                words = value.split()
                if key in {b"Uid", b"Gid"} and len(words) == 4:
                    if all(re.fullmatch(rb"[0-9]{1,10}", word) and int(word) < 2**32 for word in words):
                        for suffix, word in zip(("real", "effective", "saved", "fs"), words, strict=True):
                            facts[key.decode().lower() + "_" + suffix] = int(word)
                elif key in {b"PPid", b"TracerPid"} and len(words) == 1:
                    if re.fullmatch(rb"[0-9]{1,10}", words[0]) and int(words[0]) < 2**31:
                        facts["ppid" if key == b"PPid" else "tracer_pid"] = int(words[0])
                elif key in {b"CapPrm", b"CapEff"} and len(words) == 1:
                    if re.fullmatch(rb"[0-9a-fA-F]{1,16}", words[0]):
                        facts["cap_prm" if key == b"CapPrm" else "cap_eff"] = int(words[0], 16)
            if not all(
                prefix + "_" + suffix in facts
                for prefix in ("uid", "gid")
                for suffix in ("real", "effective", "saved", "fs")
            ):
                failures += 1
        except TimeoutError:
            raise
        except Exception:
            failures += 1
        try:
            _remaining(deadline)
            metadata = os.stat(f"/proc/{pid}/environ", follow_symlinks=False)
            _remaining(deadline)
            facts.update(
                environ_uid=metadata.st_uid, environ_gid=metadata.st_gid, environ_mode=stat.S_IMODE(metadata.st_mode)
            )
        except TimeoutError:
            raise
        except Exception:
            failures += 1
        try:
            comm = read_leaf("comm", 64).rstrip(b"\n")
            categories = {
                b"python": "python",
                b"python3": "python",
                b"python3.12": "python",
                b"python3.13": "python",
                b"python3.14": "python",
                b"ps": "ps",
                b"node": "node",
                b"Runner.Worker": "Runner.Worker",
                b"ssh-agent": "ssh-agent",
                b"gpg-agent": "gpg-agent",
            }
            facts["comm"] = categories.get(comm, "other")
        except TimeoutError:
            raise
        except Exception:
            failures += 1
        _remaining(deadline)
        facts["probe_status"] = "partial" if failures else "collected"
    except TimeoutError:
        facts["probe_status"] = "deadline"
    except Exception:
        facts["probe_status"] = "partial" if len(facts) > 2 else "unavailable"
    return result


def _cleanup(
    child: subprocess.Popen[bytes] | None,
    guardian: BoundedRunGuardian | None,
    run_token: str,
    deadline: float,
) -> dict[str, Any]:
    """Retain actual cleanup facts; teardown cannot renew the admission clock."""
    cleanup: dict[str, Any] = {
        "guardian_pid": guardian.process.pid if guardian is not None else None,
        "guardian_armed": guardian.armed if guardian is not None else False,
        "guardian_finished": False,
        "guardian_exit_code": None,
        "root_reaped": False,
        "final_token_sweep_matched_pids": None,
        "final_census_succeeded": False,
        "final_census_matched_pids": None,
        "diagnostics": [],
        "verified": False,
    }
    try:
        if child is not None and child.poll() is None:
            terminate_process_tree(child.pid, group_id=child.pid)
        if guardian is not None and guardian.armed:
            _expect_status(
                guardian.status_fd,
                _DONE,
                timeout=_remaining(deadline),
                deadline_monotonic=deadline,
            )
            if guardian.process.wait(timeout=_remaining(deadline)) != 0:
                raise RuntimeError("auxiliary cleanup guardian returned an original nonzero exit")
            guardian.finished = True
    except (OSError, RuntimeError, TimeoutError, ValueError, subprocess.SubprocessError) as error:
        cleanup["diagnostics"].append(f"{type(error).__name__}: {error}")
        cleanup["guardian_error"] = {
            "type": type(error).__name__,
            "cause": type(error.__cause__).__name__ if error.__cause__ is not None else None,
            "errno": getattr(error.__cause__ if error.__cause__ is not None else error, "errno", None),
        }
    finally:
        try:
            cleanup["final_token_sweep_matched_pids"] = (
                sorted(terminate_bounded_run_processes(run_token)) if run_token else []
            )
        except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
            cleanup["diagnostics"].append(f"token cleanup {type(error).__name__}: {error}")
        finally:
            if guardian is not None:
                try:
                    # close() is mandatory emergency teardown, not a new acceptance budget.
                    guardian.close()
                except (OSError, RuntimeError, subprocess.SubprocessError) as error:
                    cleanup["diagnostics"].append(f"guardian close {type(error).__name__}: {error}")
                cleanup["guardian_finished"] = guardian.finished
                cleanup["guardian_exit_code"] = guardian.process.returncode
            if child is not None:
                try:
                    child.wait(timeout=max(0.0, deadline - time.monotonic()))
                except subprocess.TimeoutExpired:
                    cleanup["diagnostics"].append("original auxiliary child was not reaped inside its deadline")
                cleanup["root_reaped"] = child.returncode is not None
    if child is not None and run_token:
        try:
            cleanup["final_census_matched_pids"] = sorted(observe_bounded_run_processes(run_token, deadline=deadline))
            cleanup["final_census_succeeded"] = True
        except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
            cleanup["diagnostics"].append(f"final census {type(error).__name__}: {error}")
            cleanup["final_census_error"] = _census_error_diagnostic(error, deadline)
    cleanup["deadline_exceeded"] = time.monotonic() >= deadline
    cleanup["verified"] = (
        cleanup["root_reaped"]
        and cleanup["guardian_armed"]
        and cleanup["guardian_finished"]
        and cleanup["guardian_exit_code"] == 0
        and cleanup["final_token_sweep_matched_pids"] == []
        and cleanup["final_census_succeeded"]
        and cleanup["final_census_matched_pids"] == []
        and not cleanup["diagnostics"]
        and not cleanup["deadline_exceeded"]
    )
    return cleanup


def supervise(
    command: list[str],
    root: Path,
    directory: Path,
    deadline: float,
    *,
    environment: dict[str, str] | None = None,
    bootstrap_payload: dict[str, Any] | None = None,
    print_originals: list[Any] | None = None,
) -> dict[str, Any]:
    """Observe the original child and token-bound cleanup under one finite clock."""
    if type(deadline) not in (int, float) or not math.isfinite(deadline):
        raise ValueError("original auxiliary deadline must be finite")
    if environment is not None:
        from infrastructure.core.secrets import is_secret_env_name

        if any(is_secret_env_name(key) or key in {"SSH_AUTH_SOCK", "GPG_AGENT_INFO"} for key in environment):
            raise ValueError("explicit auxiliary child environment contains protected credential names")
    directory = evidence_directory(root, directory)
    directory.mkdir(parents=True, exist_ok=True)
    from infrastructure.project.auxiliary_print_code import nomination
    from infrastructure.project.public_acceptance_auxiliary_bootstrap import WORKER, PAYLOAD, _body
    from infrastructure.project.acceptance_payload import validate_acceptance_payload, format_acceptance_payload_loader

    print_held = nomination(root, tuple(command[-2:])) if len(command) == 8 and command[-3] == WORKER else None
    if print_held is not None:
        if print_held["deadline"] != deadline or print_originals is None or print_originals:
            raise ValueError("auxiliary print supervisor needs the actual original clock and fresh owned result holder")
        body, tail = _body(
            Path(command[0]),
            root,
            WORKER,
            tuple(command[-2:]),
            directory,
            original_root=root,
            print_nomination=print_held,
        )
        payload = validate_acceptance_payload(body, bootstrap_payload, expected_path=directory / PAYLOAD)
        if (directory / PAYLOAD).read_bytes() != body or command != [
            command[0],
            "-I",
            "-c",
            format_acceptance_payload_loader(payload),
            *tail,
        ]:
            raise ValueError("auxiliary print prelaunch fixed payload differs from parent-held spec/run")
    started = time.monotonic()
    executable = Path(command[0]).resolve(strict=True)
    binary_hash = hashlib.sha256(executable.read_bytes()).hexdigest()
    stdout = directory / "stdout.txt"
    stderr = directory / "stderr.txt"
    timeout = False
    output_limit = False
    child: subprocess.Popen[bytes] | None = None
    guardian: BoundedRunGuardian | None = None
    run_token = ""
    diagnostics: list[str] = []
    original_error: BaseException | None = None
    with stdout.open("xb") as out, stderr.open("xb") as err:
        environment = (
            cell_environment(Path(command[0]).absolute(), directory, repo_root=root)
            if environment is None
            else dict(environment)
        )
        environment["PYTHONPYCACHEPREFIX"] = str(directory / "bytecode")
        try:
            _remaining(deadline)
            environment = build_bounded_env(environment)
            child_environment, run_token = build_bounded_run_env(environment)
            guardian = start_bounded_run_guardian(
                environment,
                deadline_monotonic=deadline,
                startup_timeout_seconds=min(_remaining(deadline), 60.0),
            )
            if guardian is None:
                raise ValueError("auxiliary execution requires its independent POSIX cleanup guardian")
            _remaining(deadline)
            child = subprocess.Popen(
                command,
                cwd=root,
                env=child_environment,
                stdout=out,
                stderr=err,
                start_new_session=True,
            )
            guardian.arm(root_pid=child.pid, run_token=run_token, deadline_monotonic=deadline)
            while True:
                remaining = _remaining(deadline)
                if stdout.stat().st_size > MAX_STREAM_BYTES or stderr.stat().st_size > MAX_STREAM_BYTES:
                    output_limit = True
                    break
                try:
                    child.wait(timeout=min(0.05, remaining))
                    break
                except subprocess.TimeoutExpired:
                    continue
        except BaseException as error:
            original_error = error
            diagnostics.append(f"{type(error).__name__}: {error}")
            timeout = isinstance(error, (TimeoutError, subprocess.TimeoutExpired))
        finally:
            cleanup = _cleanup(child, guardian, run_token, deadline)

    # The original fresh cache path is an observed runtime fact, not retained evidence.
    # Remove only this owned cache after child cleanup, before source inventory scans.
    shutil.rmtree(directory / "bytecode", ignore_errors=True)
    artifacts = {}
    for name, path in (("stdout", stdout), ("stderr", stderr)):
        if path.stat().st_size > MAX_STREAM_BYTES:
            output_limit = True
            # Retain the bounded leading bytes and explicitly fail the cell.
            with path.open("r+b") as stream:
                stream.truncate(MAX_STREAM_BYTES)
        artifacts[name] = {
            "path": path.relative_to(root).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    binary_hash_after = hashlib.sha256(executable.read_bytes()).hexdigest()
    if binary_hash_after != binary_hash:
        raise ValueError("selected executable changed during auxiliary execution")
    timeout = timeout or time.monotonic() >= deadline
    observation = {
        "schema_version": PROCESS_SCHEMA,
        "command": command,
        "cwd": str(root),
        "pid": child.pid if child is not None else None,
        "executable": str(executable),
        "executable_sha256": binary_hash,
        "executable_sha256_before": binary_hash,
        "executable_sha256_after": binary_hash_after,
        "selected_interpreter": command[0],
        "producer_root": str(root),
        "host": {"system": platform.system(), "machine": platform.machine()},
        "exit_code": child.returncode if child is not None else None,
        "timed_out": timeout,
        "output_limit_exceeded": output_limit,
        "original_deadline_monotonic": deadline,
        "diagnostics": diagnostics,
        "cleanup": cleanup,
        "accepted": cleanup["verified"] and not timeout and not output_limit and not diagnostics,
        "duration_seconds": time.monotonic() - started,
        "streams": artifacts,
        **({"bootstrap_payload": bootstrap_payload} if bootstrap_payload is not None else {}),
        **(
            {"auxiliary_print_launch": print_held, "auxiliary_print_owner_pid": os.getpid()}
            if print_held is not None
            else {}
        ),
    }
    finished = time.monotonic()
    observation["duration_seconds"] = finished - started
    if print_held is not None:
        observation["auxiliary_print_completion_monotonic"] = finished
    if finished >= deadline:
        observation["timed_out"] = True
        observation["accepted"] = False
    if original_error is not None and not isinstance(original_error, Exception):
        raise original_error
    if print_held is not None and observation["accepted"] is True and observation["exit_code"] == 0:
        from infrastructure.reporting.native_auxiliary_print_custody import capture_supervised_print

        if child is None or guardian is None or print_originals is None:
            raise ValueError("auxiliary print lost actual original child/guardian ownership")
        print_originals.append(
            capture_supervised_print(root, print_held, child, guardian, directory, deadline, finished)
        )
    return observation
