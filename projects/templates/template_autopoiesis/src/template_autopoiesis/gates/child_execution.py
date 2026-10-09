"""Supervised execution of source-verified generated children in core mode."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from infrastructure.core.subprocess_policy import BoundedSubprocessResult

from .custody_paths import confined_path


class ChildCapabilityBlocked(RuntimeError):
    """The bound platform execution capability is unavailable; no fallback runs."""


_BOOTSTRAP = """
import json, os, resource, runpy, sys
timeout=int(sys.argv[1]); script=sys.argv[2]; arguments=sys.argv[3:]
resource.setrlimit(resource.RLIMIT_CPU, (timeout, timeout+1))
resource.setrlimit(resource.RLIMIT_FSIZE, (16777216, 16777216))
resource.setrlimit(resource.RLIMIT_NOFILE, (128, 128))
memory_enforced = sys.platform.startswith('linux')
if memory_enforced:
    resource.setrlimit(resource.RLIMIT_AS, (1073741824, 1073741824))
print(json.dumps({'mode':'core','python_version':sys.version.split()[0],
    'resource_limits':{'cpu_seconds':timeout,'file_bytes':16777216,
    'open_files':128,'memory_bytes':1073741824 if memory_enforced else None}}), flush=True)
sys.path.insert(0, os.getcwd())
sys.argv=[script, *arguments]
if script == '__pytest__':
    import pytest
    raise SystemExit(pytest.main(arguments))
runpy.run_path(script, run_name='__main__')
"""


def execute_child(
    child_root: Path,
    script: str,
    timeout: int = 60,
    *,
    arguments: tuple[str, ...] = (),
    cpu_seconds: int | None = None,
) -> BoundedSubprocessResult:
    """Strip credentials, constrain inputs, bound resources, and reap descendants.

    ``timeout`` bounds the entire supervised launch and execution. An explicit
    ``cpu_seconds`` bounds child CPU consumption separately; its default is
    the same finite budget. Startup refusal never proves a child resource limit.

    This boundary executes trusted generated source. It is not an OS filesystem
    or network sandbox, and no claim of hostile-code containment is made.
    """
    root = child_root.resolve()
    if child_root.is_symlink() or not root.is_dir():
        raise ValueError("child execution requires a real disposable directory")
    if type(timeout) is not int or not 1 <= timeout <= 60:
        raise ValueError("child timeout must be an integer in [1,60]")
    cpu_budget = timeout if cpu_seconds is None else cpu_seconds
    if type(cpu_budget) is not int or not 1 <= cpu_budget <= timeout:
        raise ValueError("child CPU seconds must be an integer within its whole timeout")
    if script != "__pytest__":
        confined_path(root, script)
    try:
        from infrastructure import __version__
        from infrastructure.core.subprocess_policy import SubprocessPolicy, run_with_policy
    except ImportError as exc:
        raise ChildCapabilityBlocked("child execution requires the installed or checkout platform 4.0.1") from exc
    if __version__ != "4.0.1":
        raise ChildCapabilityBlocked("child execution requires its bound platform version 4.0.1")
    return run_with_policy(
        [sys.executable, "-I", "-c", _BOOTSTRAP, str(cpu_budget), script, *arguments],
        cwd=root,
        env={
            "PATH": str(Path(sys.executable).parent),
            "OPENBLAS_NUM_THREADS": "1",
            "OMP_NUM_THREADS": "1",
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        },
        policy=SubprocessPolicy(
            policy_id="autopoiesis-child-core",
            source_path="projects/templates/template_autopoiesis/src/template_autopoiesis/gates/child_execution.py",
            timeout_seconds=timeout,
            credential_free=True,
            capture_output=True,
        ),
    )
