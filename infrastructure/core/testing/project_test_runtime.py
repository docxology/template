"""Admission of an already prepared project test interpreter; never a resolver.

The receipt binds executable/prefix/metadata declarations and an actual version
probe. It does not claim custody of every installed dependency's member bytes.
"""

from __future__ import annotations

import json
import math
import os
import re
from collections.abc import Mapping
import time
from pathlib import Path

from infrastructure.core.execution_boundary import run_bounded_subprocess
from infrastructure.core.implementation_custody import bytecode_audit_bootstrap
from infrastructure.core.runtime.python_binding import (
    AnalysisRuntimeUnavailable,
    analysis_runtime_binding,
    select_analysis_python,
)
from infrastructure.core.testing.pytest_profiles import test_runner_dependency_specs


class ProjectTestRuntimeError(RuntimeError):
    """A typed configuration, missing-runtime, or deadline refusal."""

    def __init__(self, message: str, *, exit_code: int = 75, original_exit_code: int | None = None):
        super().__init__(message)
        self.exit_code = exit_code
        self.original_exit_code = original_exit_code


def remaining_test_budget(deadline: float) -> float:
    """Return remaining monotonic capacity, or the actual deadline outcome."""
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise ProjectTestRuntimeError("Project test whole-operation deadline expired", exit_code=124)
    return remaining


def project_test_deadline(timeout_seconds: float) -> float:
    """Validate the finite composed budget before any test side effect."""
    if (
        isinstance(timeout_seconds, bool)
        or not isinstance(timeout_seconds, (int, float))
        or not math.isfinite(timeout_seconds)
        or timeout_seconds <= 0
    ):
        raise ProjectTestRuntimeError("Project test timeout must be positive finite", exit_code=2)
    return time.monotonic() + timeout_seconds


def select_project_test_python(project_root: Path) -> Path:
    """Select an existing lexical interpreter without probing or preparing it."""
    try:
        return select_analysis_python(project_root)
    except AnalysisRuntimeUnavailable as exc:
        raise ProjectTestRuntimeError(str(exc)) from exc


def admit_project_test_runtime(
    project_root: Path,
    *,
    deadline: float | None = None,
    interpreter: Path | None = None,
    required_distributions: Mapping[str, str] | None = None,
) -> tuple[Path, dict[str, object]]:
    """Verify one selected existing runtime against the current exact runner stack.

    A nominated but unusable ``.venv`` never falls back to another interpreter.
    Explicit environment preparation belongs outside ordinary Stage 01.
    """
    if interpreter is not None and not isinstance(interpreter, Path):
        raise ProjectTestRuntimeError("Selected test interpreter must be a Path", exit_code=2)
    if required_distributions is not None and (
        not isinstance(required_distributions, Mapping)
        or any(
            not isinstance(name, str)
            or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", name) is None
            or not isinstance(value, str)
            or not value
            or any(char.isspace() for char in value)
            for name, value in required_distributions.items()
        )
    ):
        raise ProjectTestRuntimeError(
            "Required distributions must map actual names to exact version strings", exit_code=2
        )
    if deadline is not None and (
        isinstance(deadline, bool) or not isinstance(deadline, (int, float)) or not math.isfinite(deadline)
    ):
        raise ProjectTestRuntimeError("Project test deadline must be finite monotonic time", exit_code=2)
    operation_deadline = project_test_deadline(30.0) if deadline is None else deadline
    remaining_test_budget(operation_deadline)
    try:
        selected = select_project_test_python(project_root) if interpreter is None else interpreter.absolute()
        binding = analysis_runtime_binding(project_root, interpreter=selected)
    except AnalysisRuntimeUnavailable as exc:
        raise ProjectTestRuntimeError(str(exc)) from exc
    except ValueError as exc:
        raise ProjectTestRuntimeError(str(exc), exit_code=2) from exc
    major, minor = (int(part) for part in str(binding["python_minor"]).split("."))
    if major != 3 or minor < 12:
        raise ProjectTestRuntimeError("Selected prepared project tests require Python 3.12 or newer")
    expected: dict[str, str] = {}
    for spec in test_runner_dependency_specs():
        name, separator, pinned = spec.partition("==")
        if not separator or not pinned:
            raise ProjectTestRuntimeError(f"Workspace runner dependency is unavailable: {name}")
        expected[name] = pinned
    for name, required in (required_distributions or {}).items():
        if name in expected and expected[name] != required:
            raise ProjectTestRuntimeError(
                "Required distribution conflicts with the exact workspace runner", exit_code=2
            )
        expected[name] = required
    probe = (
        "import importlib.metadata as m,json,sys; "
        "expected=json.loads(sys.argv[1]); found={}; missing=[]; "
        "\nfor name in expected:\n"
        " try: found[name]=m.version(name)\n"
        " except m.PackageNotFoundError: missing.append(name)\n"
        "print(json.dumps({'executable':sys.executable,'prefix':sys.prefix,"
        "'python_minor':list(sys.version_info[:2]),'versions':found,'missing':missing}))"
    )
    try:
        result = run_bounded_subprocess(
            [str(selected), "-I", "-c", probe, json.dumps(expected, sort_keys=True)],
            cwd=project_root,
            env=os.environ.copy(),
            timeout=remaining_test_budget(operation_deadline),
        )
    except (FileNotFoundError, PermissionError) as exc:
        raise ProjectTestRuntimeError("Selected project test interpreter is unavailable") from exc
    if result.timed_out or result.returncode == 124:
        raise ProjectTestRuntimeError("Prepared test-runtime probe exhausted the whole deadline", exit_code=124)
    if result.returncode != 0:
        detail = result.command_error or result.stderr
        raise ProjectTestRuntimeError(
            f"Prepared test-runtime probe failed with exit {result.returncode}: {detail[-1000:]}",
            exit_code=130 if result.returncode == 130 else 75,
            original_exit_code=result.original_returncode,
        )
    try:
        actual = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ProjectTestRuntimeError("Prepared test-runtime probe returned invalid evidence") from exc
    if (
        not isinstance(actual, dict)
        or actual.get("executable") != str(selected)
        or actual.get("prefix") != binding["prefix"]
        or actual.get("python_minor") != [3, int(str(binding["python_minor"]).split(".")[1])]
        or actual.get("versions") != expected
        or actual.get("missing") != []
    ):
        raise ProjectTestRuntimeError("Selected prepared runtime differs from the required exact runner stack")
    if analysis_runtime_binding(project_root, interpreter=selected) != binding:
        raise ProjectTestRuntimeError("Selected project test runtime changed during admission")
    remaining_test_budget(operation_deadline)
    return selected, {"binding": binding, "probe": actual, "scope": "executable-prefix-metadata-versions"}


def project_test_audit_roots(project_root: Path) -> tuple[Path, ...]:
    """Nominate implementation roots and exact top-level project plugin files.

    Tests are deliberately excluded: pytest rewrites their assertions. The
    mature audit independently refuses linked roots/files before their code
    executes; this inventory does not replace that held-file admission.
    """
    platform_root = Path(__file__).absolute().parents[2]
    return (
        platform_root,
        project_root.absolute() / "src",
        project_root.absolute() / "scripts",
        *sorted(project_root.absolute().glob("*.py")),
    )


def build_audited_project_test_command(
    project_root: Path,
    selected: Path,
    args: tuple[str, ...],
    *,
    module: str | None = None,
    script: Path | None = None,
) -> tuple[str, ...]:
    """Freeze the mature pre-import audit into an isolated real child launch."""
    if (module is None) == (script is None):
        raise ValueError("Select exactly one module or script test entry point")
    roots = project_test_audit_roots(project_root)
    platform_root = roots[0]
    bootstrap = bytecode_audit_bootstrap(roots, None)
    target = (
        f"runpy.run_module({module!r},run_name='__main__')"
        if module is not None
        else f"runpy.run_path({str(script)!r},run_name='__main__')"
    )
    argv0 = module if module is not None else str(script)
    import_paths = [
        str(platform_root.parent),
        str(project_root.absolute()),
        str(project_root / "src"),
        str(project_root / "scripts"),
    ]
    source = (
        "import sys,tempfile,pathlib,runpy,traceback\n"
        f"sys.path[:0]={import_paths!r}\n"
        f"sys.argv=[{argv0!r},*sys.argv[1:]]\n"
        "with tempfile.TemporaryDirectory(prefix='template-test-bytecode-') as _cache:\n"
        " sys.pycache_prefix=str(pathlib.Path(_cache).resolve())\n"
        + "\n".join(" " + line for line in bootstrap.splitlines())
        + "\n _exit=0\n try:\n  "
        + target
        + "\n except SystemExit as _error:\n"
        "  _exit=_error.code if isinstance(_error.code,int) else (0 if _error.code is None else 1)\n"
        " except KeyboardInterrupt:\n  _exit=130\n"
        " except BaseException:\n  traceback.print_exc(); _exit=1\n"
        " finally:\n"
        "  try:\n"
        "   from infrastructure.core.implementation_custody import verify_fresh_module_bytecode\n"
        "   from infrastructure.core.testing.project_test_runtime import project_test_audit_roots\n"
        f"   _current_roots=project_test_audit_roots(pathlib.Path({str(project_root.absolute())!r}))\n"
        f"   if tuple(str(p) for p in _current_roots) != {tuple(str(root) for root in roots)!r}:\n"
        "    raise ValueError('Project plugin-root set changed during execution')\n"
        f"   for _root in {tuple(str(root) for root in roots)!r}:\n"
        "    verify_fresh_module_bytecode(pathlib.Path(_root),pathlib.Path(sys.pycache_prefix))\n"
        "  except (ValueError,OSError) as _error:\n"
        "   print('Project test executed-code custody refused: '+str(_error),file=sys.stderr)\n"
        "   if _exit in (0,75): _exit=75\n"
        " raise SystemExit(_exit)\n"
    )
    return (str(selected), "-I", "-c", source, *args)


__all__ = [
    "ProjectTestRuntimeError",
    "admit_project_test_runtime",
    "build_audited_project_test_command",
    "project_test_audit_roots",
    "project_test_deadline",
    "remaining_test_budget",
    "select_project_test_python",
]
