"""Bind a native worker to its supervisor's actual original PID and host."""

from __future__ import annotations

import platform
from typing import Any


def native_host_observation() -> dict[str, str]:
    """Observe the current host directly in the process holding the record."""
    return {"system": platform.system(), "machine": platform.machine()}


def require_native_platform(expected: object) -> str:
    """Require an explicit supported platform chosen before worker launch."""
    if not isinstance(expected, str) or expected not in {"Linux", "Darwin"}:
        raise ValueError("native execution requires explicit expected platform Linux or Darwin")
    return expected


def validate_native_worker_process(
    specification: dict[str, Any],
    process: dict[str, Any],
    worker: dict[str, Any],
    *,
    hosted_origin: object | None = None,
) -> None:
    """Portable readers use the admitted original host, never the reader host."""
    expected = require_native_platform(specification.get("expected_platform"))
    if hosted_origin is not None and expected != "Linux":
        raise ValueError("authenticated hosted native-original evidence requires Linux")
    pid = process.get("pid")
    if type(pid) is not int or pid <= 0 or type(worker.get("pid")) is not int or worker["pid"] != pid:
        raise ValueError("native worker PID differs from its supervisor's actual launched process")
    observations = [
        process.get("host_before"),
        process.get("host_after"),
        worker.get("host_before"),
        worker.get("host_after"),
    ]
    for host in observations:
        if (
            not isinstance(host, dict)
            or set(host) != {"system", "machine"}
            or host["system"] != expected
            or not isinstance(host["machine"], str)
            or not host["machine"]
        ):
            raise ValueError("native original process host differs from the prelaunch platform obligation")
    if any(host != observations[0] for host in observations[1:]):
        raise ValueError("native original worker or supervisor host changed")
