"""Coverage process policy for test runners and their subprocesses."""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Literal

from infrastructure.core.execution_boundary import BoundedSubprocessResult, build_bounded_env, run_bounded_subprocess

from infrastructure.core.runtime.environment import get_python_command

PYTEST_HELP_PROBE_TIMEOUT_SECONDS = 30
PYTEST_PROCESS_PLUGIN = "infrastructure.core.testing._pytest_smoke_coverage"
_METADATA_OPTION = "--template-pytest-metadata"
_METADATA_RESULT = "template-pytest-metadata:"


def coverage_free_subprocess_env(base_env: Mapping[str, str] | None = None) -> dict[str, str]:
    """Copy the environment without interpreter-startup coverage settings."""
    env = dict(os.environ if base_env is None else base_env)
    for name in (
        "COVERAGE_FILE",
        "COVERAGE_PROCESS_CONFIG",
        "COVERAGE_PROCESS_START",
        "COV_CORE_BRANCH",
        "COV_CORE_CONFIG",
        "COV_CORE_CONTEXT",
        "COV_CORE_DATAFILE",
        "COV_CORE_SOURCE",
    ):
        env.pop(name, None)
    return env


def run_pytest_metadata(
    command: Sequence[str],
    cwd: Path,
    env: Mapping[str, str] | None,
    *,
    mode: Literal["capability", "discovery"],
    timeout_seconds: float,
) -> BoundedSubprocessResult:
    """Run a nonmeasuring pytest child with the selected invocation's settings."""
    option_end = command.index("--") if "--" in command else len(command)
    options = ["-p", PYTEST_PROCESS_PLUGIN, f"{_METADATA_OPTION}={mode}"]
    if mode == "discovery":
        options.append("--collect-only")
    process_env = coverage_free_subprocess_env(env)
    # Raw python -m pytest callers can start outside the SDK checkout. The
    # audited -I launcher supplies its own source paths and ignores PYTHONPATH.
    root = str(Path(__file__).resolve().parents[3])
    pythonpath = process_env.get("PYTHONPATH")
    process_env["PYTHONPATH"] = os.pathsep.join((pythonpath, root)) if pythonpath else root
    return run_bounded_subprocess(
        [*command[:option_end], *options, *command[option_end:]],
        cwd=cwd,
        env=process_env,
        guardian_env=build_bounded_env(process_env),
        timeout=timeout_seconds,
    )


def pytest_metadata_value(result: BoundedSubprocessResult, *, mode: Literal["capability", "discovery"]) -> str | None:
    """Read one successful result emitted for the requested pytest metadata mode."""
    if result.returncode:
        return None
    records = [line for line in result.stdout.splitlines() if line.startswith(_METADATA_RESULT)]
    prefix = f"{_METADATA_RESULT}{mode}:"
    if len(records) == 1 and records[0].startswith(prefix):
        return records[0].removeprefix(prefix)
    return None


def check_cov_datafile_support(
    *,
    command: Sequence[str] | None = None,
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
    timeout_seconds: float = PYTEST_HELP_PROBE_TIMEOUT_SECONDS,
) -> bool:
    """Check the option registered by pytest plugins before initial conftests."""
    if command is None:
        command = [*get_python_command(), "-B", "-m", "pytest"]
    try:
        result = run_pytest_metadata(
            command,
            Path.cwd() if cwd is None else cwd,
            env,
            mode="capability",
            timeout_seconds=timeout_seconds,
        )
    except (OSError, ValueError):
        return False
    return pytest_metadata_value(result, mode="capability") == "yes"


__all__ = ["PYTEST_HELP_PROBE_TIMEOUT_SECONDS", "check_cov_datafile_support", "coverage_free_subprocess_env"]
