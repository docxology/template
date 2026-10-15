"""Bounded original auxiliary child supervision and raw OS observations."""

from __future__ import annotations

import hashlib
import os
import platform
import signal
import subprocess
import time
from pathlib import Path
from typing import Any

from infrastructure.project.public_acceptance_evidence import cell_environment, evidence_directory

PROCESS_SCHEMA = "template-auxiliary-process-v2"


def supervise(
    command: list[str],
    root: Path,
    directory: Path,
    deadline: float,
    *,
    environment: dict[str, str] | None = None,
    bootstrap_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Retain original exit and bounded raw streams; kill the owned group on timeout."""
    if environment is not None:
        from infrastructure.core.secrets import is_secret_env_name

        if any(is_secret_env_name(key) or key in {"SSH_AUTH_SOCK", "GPG_AGENT_INFO"} for key in environment):
            raise ValueError("explicit auxiliary child environment contains protected credential names")
    directory = evidence_directory(root, directory)
    directory.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    executable = Path(command[0]).resolve(strict=True)
    binary_hash = hashlib.sha256(executable.read_bytes()).hexdigest()
    stdout = directory / "stdout.txt"
    stderr = directory / "stderr.txt"
    timeout = False
    output_limit = False
    with stdout.open("xb") as out, stderr.open("xb") as err:
        environment = (
            cell_environment(Path(command[0]).absolute(), directory, repo_root=root)
            if environment is None
            else dict(environment)
        )
        environment["PYTHONPYCACHEPREFIX"] = str(directory / "bytecode")
        child = subprocess.Popen(
            command,
            cwd=root,
            env=environment,
            stdout=out,
            stderr=err,
            start_new_session=True,
        )
        try:
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise subprocess.TimeoutExpired(command, 0)
                if stdout.stat().st_size > 16 * 1024 * 1024 or stderr.stat().st_size > 16 * 1024 * 1024:
                    output_limit = True
                    os.killpg(child.pid, signal.SIGKILL)
                    code = child.wait(timeout=5)
                    break
                try:
                    code = child.wait(timeout=min(0.05, remaining))
                    break
                except subprocess.TimeoutExpired:
                    continue
        except subprocess.TimeoutExpired:
            timeout = True
            os.killpg(child.pid, signal.SIGKILL)
            code = child.wait(timeout=5)
        finally:
            # A successful leader is not permission to leave grandchildren.
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            child.wait(timeout=5)
    import shutil

    # The original fresh cache path is an observed runtime fact, not retained evidence.
    # Remove only this owned cache after child cleanup, before source inventory scans.
    shutil.rmtree(directory / "bytecode", ignore_errors=True)
    artifacts = {}
    for name, path in (("stdout", stdout), ("stderr", stderr)):
        if path.stat().st_size > 16 * 1024 * 1024:
            output_limit = True
            # Retain the bounded leading bytes and explicitly fail the cell.
            with path.open("r+b") as stream:
                stream.truncate(16 * 1024 * 1024)
        artifacts[name] = {
            "path": path.relative_to(root).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    if hashlib.sha256(executable.read_bytes()).hexdigest() != binary_hash:
        raise ValueError("selected executable changed during auxiliary execution")
    return {
        "schema_version": PROCESS_SCHEMA,
        "command": command,
        "cwd": str(root),
        "pid": child.pid,
        "executable": str(executable),
        "executable_sha256": binary_hash,
        "executable_sha256_before": binary_hash,
        "executable_sha256_after": hashlib.sha256(executable.read_bytes()).hexdigest(),
        "selected_interpreter": command[0],
        "producer_root": str(root),
        "host": {"system": platform.system(), "machine": platform.machine()},
        "exit_code": code,
        "timed_out": timeout,
        "output_limit_exceeded": output_limit,
        "duration_seconds": time.monotonic() - started,
        "streams": artifacts,
        **({"bootstrap_payload": bootstrap_payload} if bootstrap_payload is not None else {}),
    }
