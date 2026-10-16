"""Confined evidence and whole-collection accounting for public runtime cells."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
from collections import Counter
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import TYPE_CHECKING, Any

from infrastructure.core.files.secure_write import atomic_write_text_confined, read_bytes_confined
from infrastructure.core.testing.pytest_profiles import TEST_RUNNER_BASE_DEPS

if TYPE_CHECKING:
    from infrastructure.reporting.release_readiness_profile import Requirement

ARTIFACT_SCHEMA = "template-required-acceptance-v1"

PYTEST_RECEIPT_SCHEMA = "template-public-pytest-v2"
RUNTIME_SCHEMA = "template-public-runtime-v1"
CELL_SCHEMA = "template-public-runtime-cell-v2"


def evidence_directory(root: Path, directory: Path, *, fresh: bool = False) -> Path:
    """Refuse traversal and symlinks before touching the ignored evidence lane."""
    lexical_root = root.absolute()
    root = root.resolve()
    candidate = directory.absolute()
    if candidate.is_relative_to(lexical_root):
        candidate = root / candidate.relative_to(lexical_root)
    if (
        ".." in candidate.parts
        or "\\" in str(candidate)
        or "\0" in str(candidate)
        or not candidate.is_relative_to(root / "output/readiness")
    ):
        raise ValueError("matrix evidence must use a canonical path below output/readiness")
    current = root
    for part in candidate.relative_to(root).parts:
        current /= part
        if current.is_symlink():
            raise ValueError("matrix evidence refuses symlink components")
    if candidate.resolve() != candidate or fresh and candidate.exists():
        raise ValueError("matrix evidence directory must be canonical and fresh")
    return candidate


# This preflight deliberately needs only the selected interpreter's standard
# library. Missing pytest/Coverage cannot prevent a typed missing-tool receipt.
RUNTIME_PROBE_SCRIPT = """
import hashlib, importlib.metadata, json, platform, pathlib, sys
packages, missing = {}, []
for name in json.loads(sys.argv[1]):
    try: packages[name] = importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError: missing.append(name)
print(json.dumps({'schema_version':'template-public-runtime-v1',
 'python_version':f'{sys.version_info.major}.{sys.version_info.minor}',
 'python_full_version':platform.python_version(), 'implementation':platform.python_implementation(),
 'executable':sys.executable,
 'interpreter_sha256':hashlib.sha256(pathlib.Path(sys.executable).read_bytes()).hexdigest(),
 'packages':packages, 'missing':missing}, sort_keys=True))
sys.exit(75 if missing else 0)
"""


def write_json(
    root: Path,
    path: Path,
    payload: object,
    *,
    expected_root_identity: tuple[int, int] | None = None,
    compact: bool = False,
) -> dict[str, str]:
    """Write exact local evidence without following a symlink or escaping its root."""
    path = evidence_directory(root, path.parent) / path.name
    root = root.resolve()
    text = (
        json.dumps(
            payload,
            indent=None if compact else 2,
            separators=(",", ":") if compact else None,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    )
    atomic_write_text_confined(root, path, text, expected_root_identity=expected_root_identity)
    return {"path": path.relative_to(root).as_posix(), "sha256": hashlib.sha256(text.encode()).hexdigest()}


def read_json(root: Path, path: Path) -> dict[str, Any]:
    """Read one bounded, regular, confined JSON object."""
    value = json.loads(read_bytes_confined(root, path, max_bytes=32 * 1024 * 1024))
    if not isinstance(value, dict):
        raise ValueError("runtime evidence is not an object")
    return value


def runtime_identity() -> dict[str, Any]:
    """Observe the selected interpreter and installed test stack, without acquisition."""
    packages = {}
    missing = []
    for name in (*TEST_RUNNER_BASE_DEPS, "coverage"):
        try:
            packages[name] = version(name)
        except PackageNotFoundError:
            missing.append(name)
    return {
        "schema_version": RUNTIME_SCHEMA,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
        "python_full_version": platform.python_version(),
        "implementation": platform.python_implementation(),
        "executable": sys.executable,
        "interpreter_sha256": hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest(),
        "packages": packages,
        "missing": missing,
    }


def cell_environment(interpreter: Path, directory: Path, *, repo_root: Path | None = None) -> dict[str, str]:
    """Isolate selection and transport the nominated candidate's build policy."""
    env = os.environ.copy()
    for key in (
        "PYTEST_ADDOPTS",
        "PYTEST_PLUGINS",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD",
        "PYTHONPATH",
        "PYTHONHOME",
        "COVERAGE_PROCESS_START",
        "COVERAGE_RCFILE",
        "VIRTUAL_ENV",
        "UV_PROJECT_ENVIRONMENT",
        "PYTEST_XDIST_WORKERS",
    ):
        env.pop(key, None)
    # A matrix child is not a descendant of a pipeline holding its project lock.
    for key in tuple(env):
        if key.startswith("TEMPLATE_PROJECT_LOCK_"):
            env.pop(key)
    env.update(
        COVERAGE_FILE=str(directory / ".coverage"),
        HYPOTHESIS_STORAGE_DIRECTORY=str(directory / ".hypothesis"),
        MPLBACKEND="Agg",
        PYTHONUNBUFFERED="1",
        UV_NO_SYNC="1",
        UV_OFFLINE="1",
        UV_NO_MANAGED_PYTHON="1",
        UV_PYTHON_DOWNLOADS="never",
        UV_PYTHON=str(interpreter),
        UV_PROJECT_ENVIRONMENT=str(interpreter.parent.parent),
        VIRTUAL_ENV=str(interpreter.parent.parent),
        PYTEST_XDIST_WORKERS="1",
        OMP_NUM_THREADS="1",
        OPENBLAS_NUM_THREADS="1",
        MKL_NUM_THREADS="1",
    )
    env["PATH"] = str(interpreter.parent) + os.pathsep + env.get("PATH", "")
    if repo_root is None:
        return env
    from infrastructure.core.execution_policy import apply_execution_policy

    return apply_execution_policy(env, repo_root, mode="core")


def project_python_roots(project: Path) -> tuple[Path, ...]:
    """Admit owned source lanes and exact root Python files, including conftest."""
    return project / "src", project / "scripts", project / "tests", *sorted(project.glob("*.py"))


def bootstrap_command(
    interpreter: Path,
    root: Path,
    module: str,
    *args: str,
    audit_roots: tuple[Path, ...] = (),
    command_root: Path | None = None,
    implementation_root: Path | None = None,
    command_audit_roots: tuple[Path, ...] | None = None,
    fresh_pycache_prefix: Path | None = None,
) -> tuple[str, ...]:
    """Use the exact interpreter with isolated startup and explicit trusted source."""
    from infrastructure.core.implementation_custody import bytecode_audit_bootstrap, _format_bytecode_audit_bootstrap
    from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

    # Editable .pth launch helpers have already executed at interpreter startup.
    # Bind actual public implementation/provider packages, rather than treating
    # the entire third-party installation as a pre-import public source root.
    roots = (
        Path(__file__).absolute().parents[1],
        root / "infrastructure",
        root / "scripts",
        root / "tests",
        *sorted(root.glob("*.py")),
        *(source for scope in PUBLIC_PROJECT_NAMES for source in project_python_roots(root / "projects" / scope)),
        *audit_roots,
    )
    implementation = Path(__file__).absolute().parents[1]
    if command_root is None:
        audit = bytecode_audit_bootstrap(roots, None)
    else:
        # Enumerate current admitted source, but preserve original launch paths.
        origin = implementation_root or command_root / "infrastructure"
        implementation = origin
        if command_audit_roots is not None and (
            len(command_audit_roots) != len(audit_roots)
            or any(not path.is_absolute() or ".." in path.parts for path in command_audit_roots)
        ):
            raise ValueError("portable provider audit labels differ from actual admitted namespace arity")
        owned_count = len(roots) - len(audit_roots)
        projected = tuple(
            origin if index == 0 else command_root / path.relative_to(root)
            for index, path in enumerate(roots[:owned_count])
        ) + (command_audit_roots if command_audit_roots is not None else audit_roots)
        hook = Path(__file__).absolute().parents[1] / "core/bytecode_audit.py"
        raw = read_bytes_confined(hook.parent, hook, max_bytes=1024 * 1024)
        audit = _format_bytecode_audit_bootstrap(raw, origin / "core/bytecode_audit.py", projected, None)
        root = command_root
    cache_header = (
        "import runpy,sys,tempfile\nfrom pathlib import Path\n"
        "with tempfile.TemporaryDirectory(prefix='template-acceptance-bytecode-') as cache:\n"
    )
    if fresh_pycache_prefix is not None:
        if (
            not isinstance(fresh_pycache_prefix, Path)
            or not fresh_pycache_prefix.is_absolute()
            or ".." in fresh_pycache_prefix.parts
            or str(fresh_pycache_prefix) != os.path.normpath(str(fresh_pycache_prefix))
        ):
            raise ValueError("fresh bytecode prefix requires an absolute canonical path")
        # Generation is also used for portable readback after cleanup. Only the
        # actual child checks physical freshness; a path string grants no custody.
        cache_header = (
            "import runpy,sys,os,stat\nfrom pathlib import Path\n"
            f"cache={str(fresh_pycache_prefix)!r}\n"
            "if True:\n"
            " prefix=Path(cache); metadata=prefix.lstat()\n"
            " if prefix.resolve(strict=True)!=prefix or not stat.S_ISDIR(metadata.st_mode) "
            "or metadata.st_uid!=os.getuid() or stat.S_IMODE(metadata.st_mode)!=0o700 "
            "or any(prefix.iterdir()):\n"
            "  raise ValueError('fresh bytecode prefix is not an empty private owned directory')\n"
        )
    bootstrap = (
        cache_header
        + " sys.pycache_prefix=str(Path(cache).resolve())\n"
        + "\n".join(" " + line for line in audit.splitlines())
        + "\n"
        # A wheel-backed caller must keep its admitted implementation when the
        # public checkout is added for tests. Bind every SDK submodule before
        # executing any SDK initializer; editable finders cannot select a sibling.
        + " import importlib.abc,importlib.util\n"
        + " if any(n=='infrastructure' or n.startswith('infrastructure.') for n in sys.modules):\n"
        + "  raise ValueError('public SDK was loaded before its audited bootstrap')\n"
        + " class _SelectedSDKFinder(importlib.abc.MetaPathFinder):\n"
        + "  def find_spec(self,fullname,path,target=None):\n"
        + "   if fullname!='infrastructure' and not fullname.startswith('infrastructure.'): return None\n"
        + f"   base=Path({str(implementation.parent)!r}).joinpath(*fullname.split('.'))\n"
        + "   package=base/'__init__.py'; ordinary=base.with_suffix('.py')\n"
        + "   selected=package if package.is_file() else ordinary\n"
        + "   if not selected.is_file(): raise ImportError('selected public SDK member is absent: '+fullname)\n"
        + "   return importlib.util.spec_from_file_location(fullname,selected,\n"
        + "    submodule_search_locations=[str(base)] if selected==package else None)\n"
        + " sys.meta_path.insert(0,_SelectedSDKFinder())\n"
        + " import infrastructure\n"
        + " sys.path.insert(0,sys.argv.pop(1))\n"
        + " runpy.run_module(sys.argv.pop(1),run_name='__main__')\n"
    )
    return str(interpreter), "-I", "-c", bootstrap, str(root), module, *args


def verify_runtime_execution(project: Path, *, root: Path | None = None, scope: str | None = None) -> None:
    """Verify actual audited platform/domain code before a passing child receipt."""
    from infrastructure.core.implementation_custody import verify_fresh_module_bytecode

    if not sys.pycache_prefix:
        raise ValueError("runtime child lacks its launcher's fresh prefix")
    if root is not None and scope is not None:
        from infrastructure.project.public_acceptance_scope import RuntimeScope

        roots = RuntimeScope(root, scope).python_roots()
        if scope == "root":
            from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

            roots += tuple(
                path for name in PUBLIC_PROJECT_NAMES for path in project_python_roots(root / "projects" / name)
            )
    else:
        roots = project_python_roots(project)
    for source in (Path(__file__).absolute().parents[1], *roots):
        verify_fresh_module_bytecode(source, Path(sys.pycache_prefix))


def aggregate_pytest(baseline: dict[str, Any], groups: list[dict[str, Any]], run_id: str) -> dict[str, Any]:
    """Require the executed node-ID union to equal an independent full collection."""
    receipts = [baseline, *groups]
    for receipt in receipts:
        if receipt.get("schema_version") != PYTEST_RECEIPT_SCHEMA or receipt.get("run_id") != run_id:
            raise ValueError("missing, stale or malformed pytest receipt")
    expected = baseline.get("nodeids")
    if (
        not isinstance(expected, list)
        or not expected
        or any(not isinstance(node, str) for node in expected)
        or len(set(expected)) != len(expected)
        or baseline.get("exit_code") != 0
        or baseline.get("collection_errors")
        or baseline.get("deselected")
        or baseline.get("collection_skips")
    ):
        raise ValueError("full collection is empty, partial or unsuccessful")
    actual = [node for receipt in groups for node in receipt.get("nodeids", [])]
    if Counter(actual) != Counter(expected):
        raise ValueError("executed chunks omit, duplicate or invent collected cases")
    counts = {key: 0 for key in ("passed", "failed", "errors", "skipped", "deselected")}
    for receipt in groups:
        results = receipt.get("outcomes")
        if not isinstance(results, dict) or set(results) != set(receipt["nodeids"]):
            raise ValueError("pytest case outcomes are missing or unbound")
        if receipt.get("collection_errors") or receipt.get("collection_skips"):
            raise ValueError("pytest execution collection is incomplete")
        counts["deselected"] += len(receipt.get("deselected", []))
        for outcome in results.values():
            if outcome not in {"passed", "failed", "errors", "skipped"}:
                raise ValueError("pytest case has no complete terminal outcome")
            counts[outcome] += 1
    return {"collected": len(expected), **counts, "nodeids": expected}


def gate_payload(
    requirement: Requirement,
    fingerprint: str,
    status: str,
    details: dict[str, Any],
    blockers: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Serialize the source-owned required-profile shape without granting other gates."""
    payload: dict[str, Any] = {
        "schema_version": ARTIFACT_SCHEMA,
        "gate": requirement.id,
        "status": status,
        "scope": requirement.scope,
        "version": requirement.version,
        "platform_version": requirement.platform_version,
        "source_fingerprint": fingerprint,
        "source_identity": requirement.source_identity,
        "details": details,
    }
    if requirement.scope != "root":
        payload["deliverables_identity"] = requirement.deliverables_identity
    if blockers:
        payload["blockers"] = blockers
    return payload
