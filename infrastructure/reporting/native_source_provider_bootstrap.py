"""Explicit admitted SDK package loading without a SourceDATA import root.

The actual supervisor uses these exact command bytes before its real Popen.
Source inputs, original guardian facts and portable command reproduction remain
separate authenticated custody boundaries.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import sys
import types
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from infrastructure.core.bytecode_audit import MAX_CACHE_BYTES, MAX_EXECUTIONS
from infrastructure.core.files.secure_write import (
    atomic_write_bytes_confined,
    read_bytes_confined,
)
from infrastructure.core.pipeline.fingerprint_files import (
    anchored_parent,
    open_directory,
)
from infrastructure.core.implementation_custody import (
    _format_bytecode_audit_bootstrap,
    source_file_bytes,
    verify_implementation_custody,
)
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_source_external_admission import (
    NativeSourceContext,
)
from infrastructure.reporting.release_readiness_snapshot import json_object_from_bytes

from infrastructure.reporting.native_code_runtime import observe_native_code_runtime

NATIVE_WORKER_MODULE = "infrastructure.reporting.native_format_acceptance_worker"
OFFICE_CONTROL_WORKER_MODULE = "infrastructure.reporting.native_office_diagram_control_worker"
MERMAID_SOURCE_WORKER_MODULE = "infrastructure.reporting.native_mermaid_all_source_worker"
NATIVE_CONTROLLER_MODULE = "infrastructure.reporting.native_format_acceptance"
NATIVE_READER_MODULE = "infrastructure.reporting.native_hosted_reader"
NATIVE_CAPTURE_MODULE = "infrastructure.reporting.native_installed_custody_capture"


def _worker_module(value: str) -> str:
    if value not in (
        NATIVE_WORKER_MODULE,
        OFFICE_CONTROL_WORKER_MODULE,
        MERMAID_SOURCE_WORKER_MODULE,
        NATIVE_CONTROLLER_MODULE,
        NATIVE_READER_MODULE,
        NATIVE_CAPTURE_MODULE,
    ):
        raise ValueError("selected SDK bootstrap requires an exact Source-owned worker role")
    return value


CLOSURE_SCHEMA = "template-native-selected-sdk-execution-closure-v3"


def _invalidate_retained_sdk_receipt(directory: Path, expected_identity: tuple[int, int]) -> None:
    """Remove only our receipt from the same actual held private directory.

    Invalidation is failure cleanup, never a fresh operation or a successful
    late completion. The original hard guardian deadline remains in force.
    """
    with anchored_parent(directory) as parent:
        if parent is None:
            raise ValueError("selected SDK failed receipt directory is no longer held")
        with open_directory(parent, directory.name) as descriptor:
            observed = os.fstat(descriptor)
            if (observed.st_dev, observed.st_ino) != expected_identity:
                raise ValueError("selected SDK failed receipt directory was replaced")
            try:
                receipt = os.stat("receipt.json", dir_fd=descriptor, follow_symlinks=False)
            except FileNotFoundError:
                return
            if not stat.S_ISREG(receipt.st_mode):
                raise ValueError("selected SDK refuses invalidating a substituted non-file receipt")
            os.unlink("receipt.json", dir_fd=descriptor)


def retain_selected_sdk_execution_closure(
    audit_scope: Mapping[str, Any],
    hook_bytes: bytes,
    sdk_package_root: Path,
    provider_audit_roots: tuple[Path, ...],
    implementation_binding_path: Path,
    externally_bound_implementation_sha256: str,
    closure_directory: Path,
    closure_directory_identity: tuple[int, int],
    worker_outcome: dict[str, Any],
    *,
    deadline: float,
    required_worker_module: str = NATIVE_WORKER_MODULE,
) -> None:
    """Retain actual hook/source/executed-code/cache bytes before prefix removal.

    Failure is retained as a failed closure and cannot approve execution. The
    launcher preserves the original worker result/exception; the enclosing
    guardian supplies the actual native OS exit independently. No receipt code
    or SystemExit value substitutes for that OS observation.
    """
    _worker_module(required_worker_module)
    observed = closure_directory.lstat()
    if (
        not stat.S_ISDIR(observed.st_mode)
        or closure_directory.absolute() != closure_directory.resolve(strict=True)
        or (observed.st_dev, observed.st_ino) != closure_directory_identity
        or any(closure_directory.iterdir())
    ):
        raise ValueError("selected SDK closure requires its supervisor-held fresh real directory")
    value: dict[str, Any] = {
        "schema_version": CLOSURE_SCHEMA,
        "status": "failed",
        "worker_outcome": worker_outcome,
        "native_os_exit_authority": "original external process guardian only",
        "selected_sdk_package_root": str(sdk_package_root),
        "original_operation_deadline": deadline,
        "hook_sha256": hashlib.sha256(hook_bytes).hexdigest(),
        "implementation_input": {
            "path": str(implementation_binding_path),
            "sha256": externally_bound_implementation_sha256,
        },
        "executions": [],
        "errors": [],
    }
    retained_bytes = 0
    payload_count = 0
    retained_bindings: list[dict[str, Any]] = []

    def retain(raw: bytes) -> dict[str, Any]:
        nonlocal retained_bytes, payload_count
        remaining(deadline)
        retained_bytes += len(raw)
        if retained_bytes > MAX_CACHE_BYTES:
            raise ValueError("selected SDK closure exceeds the existing 64 MiB byte ceiling")
        name = f"payload-{payload_count:06d}.bin"
        payload_count += 1
        atomic_write_bytes_confined(
            closure_directory,
            closure_directory / name,
            raw,
            mode=0o600,
            expected_root_identity=closure_directory_identity,
        )
        binding = {
            "path": name,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
        }
        retained_bindings.append(binding)
        return binding

    try:
        remaining(deadline)
        if sys.pycache_prefix is None:
            raise ValueError("selected SDK closure lost the original fresh bytecode prefix")
        prefix = Path(sys.pycache_prefix).absolute()
        registry = getattr(sys, "_template_executed_bytecode_audit", None)
        if not isinstance(registry, types.MappingProxyType):
            raise ValueError("selected SDK closure lacks the actual original audit registry")
        roots = (sdk_package_root, *provider_audit_roots)
        if (
            registry.get("schema_version") != "template/executed-bytecode-audit/1"
            or registry.get("prefix") != str(prefix)
            or registry.get("source_roots") != tuple(str(root.absolute()) for root in roots)
            or registry.get("hook_source_path") != str(sdk_package_root / "core/bytecode_audit.py")
            or registry.get("hook_source_sha256") != value["hook_sha256"]
        ):
            raise ValueError("selected SDK closure registry differs from original hook/root/prefix bindings")
        package = sys.modules.get("infrastructure")
        if (
            package is None
            or getattr(package, "__file__", None) != str(sdk_package_root / "__init__.py")
            or tuple(getattr(package, "__path__", ())) != (str(sdk_package_root),)
        ):
            raise ValueError("selected SDK closure imported a different package origin")
        implementation_bytes = source_file_bytes(implementation_binding_path)
        if hashlib.sha256(implementation_bytes).hexdigest() != externally_bound_implementation_sha256:
            raise ValueError("selected SDK closure implementation input changed from external supervisor binding")
        implementation = json_object_from_bytes(implementation_bytes)
        for root in roots:
            remaining(deadline)
            audit_scope["verify_executed_source_code"](root, prefix)
        verify_implementation_custody(implementation, fresh_pycache_prefix=prefix)
        value["prefix"] = str(prefix)
        value["source_roots"] = registry["source_roots"]
        value["runtime"] = observe_native_code_runtime()
        value["raw_hook"] = retain(hook_bytes)
        value["implementation_bytes"] = retain(implementation_bytes)
        snapshot = registry["snapshot"]()
        if not isinstance(snapshot, types.MappingProxyType) or len(snapshot) > MAX_EXECUTIONS:
            raise ValueError("selected SDK closure actual execution snapshot exceeds its existing bound")
        executions: list[dict[str, Any]] = value["executions"]
        total_executions = 0
        for filename, runs in sorted(snapshot.items()):
            remaining(deadline)
            if not isinstance(filename, str) or not any(Path(filename).is_relative_to(root) for root in roots):
                raise ValueError("selected SDK closure contains an execution outside admitted audit roots")
            raw_source = audit_scope["_read_cache"](Path(filename))
            source_binding = retain(raw_source)
            row: dict[str, Any] = {
                "source_path": filename,
                "source": source_binding,
                "runs": [],
            }
            for code, cache_path, cache_sha256 in runs:
                total_executions += 1
                if total_executions > MAX_EXECUTIONS or not isinstance(code, types.CodeType):
                    raise ValueError("selected SDK closure has invalid/excess actual code executions")
                canonical = audit_scope["canonical_code"](code)
                actual_run: dict[str, Any] = {
                    "executed_code": retain(canonical),
                    "cache": None,
                }
                if cache_path is not None:
                    cached = Path(cache_path)
                    if not cached.is_relative_to(prefix):
                        raise ValueError("selected SDK closure cache escaped the original prefix")
                    raw_cache = audit_scope["_read_cache"](cached)
                    if hashlib.sha256(raw_cache).hexdigest() != cache_sha256:
                        raise ValueError("selected SDK closure cache changed from actual execution-time bytes")
                    actual_run["cache"] = {
                        "original_path": cache_path,
                        "execution_sha256": cache_sha256,
                        "bytes": retain(raw_cache),
                    }
                row["runs"].append(actual_run)
            executions.append(row)
        worker_path = str(
            sdk_package_root / (required_worker_module.removeprefix("infrastructure.").replace(".", "/") + ".py")
        )
        if not any(row["source_path"] == worker_path and row["runs"] for row in executions):
            raise ValueError("selected SDK closure lacks actual selected native worker execution")
        # These closing checks occur while the original prefix still exists.
        verify_implementation_custody(implementation, fresh_pycache_prefix=prefix)
        for root in roots:
            remaining(deadline)
            audit_scope["verify_executed_source_code"](root, prefix)
        if registry["snapshot"]() != snapshot:
            raise ValueError("selected SDK execution closure changed during retention")
        if source_file_bytes(implementation_binding_path) != implementation_bytes:
            raise ValueError("selected SDK closure input changed during retention")
        for binding in retained_bindings:
            remaining(deadline)
            retained = read_bytes_confined(
                closure_directory,
                closure_directory / binding["path"],
                max_bytes=MAX_CACHE_BYTES,
                expected_root_identity=closure_directory_identity,
            )
            if hashlib.sha256(retained).hexdigest() != binding["sha256"]:
                raise ValueError("selected SDK retained closure payload bytes changed during retention")
        remaining(deadline)
        value["retained_payload_bytes"] = retained_bytes
        value["status"] = "pass"
    except BaseException as error:
        value["errors"].append({"class": type(error).__name__, "message": str(error)})
    try:
        remaining(deadline)
        receipt = (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()
        if retained_bytes + len(receipt) > MAX_CACHE_BYTES:
            raise ValueError("selected SDK closure receipt exceeds the existing byte ceiling")
        atomic_write_bytes_confined(
            closure_directory,
            closure_directory / "receipt.json",
            receipt,
            mode=0o600,
            expected_root_identity=closure_directory_identity,
        )
        # Serialization, complete atomic write and writer custody are included.
        # A passing JSON written after the original clock expires is invalid.
        remaining(deadline)
    except BaseException:
        _invalidate_retained_sdk_receipt(closure_directory, closure_directory_identity)
        raise


def format_selected_sdk_native_bootstrap(
    hook_bytes: bytes,
    sdk_package_root: Path,
    provider_audit_roots: tuple[Path, ...],
    implementation_binding_path: Path,
    externally_bound_implementation_sha256: str,
    closure_directory: Path,
    closure_directory_identity: tuple[int, int],
    deadline: float,
    *,
    required_worker_module: str = NATIVE_WORKER_MODULE,
) -> str:
    """Pure original command reconstruction from separately admitted hook bytes.

    provider_audit_roots must come from genuine existing runtime-provider
    admission. Audit coverage itself grants no provider/source authority.
    Original producer paths are labels here; current readers admit separately.
    """
    _worker_module(required_worker_module)
    worker_keyword = (
        "" if required_worker_module == NATIVE_WORKER_MODULE else f",required_worker_module={required_worker_module!r}"
    )
    audit = _format_bytecode_audit_bootstrap(
        hook_bytes,
        sdk_package_root / "core/bytecode_audit.py",
        (sdk_package_root, *provider_audit_roots),
        None,
    )
    package_root = str(sdk_package_root)
    office_seal = (
        ""
        if required_worker_module != OFFICE_CONTROL_WORKER_MODULE
        else (
            "   import hashlib\n"
            f"   _office_closure=Path({str(closure_directory / 'receipt.json')!r}).read_bytes()\n"
            "   sys.stdout.write('OFFICE_CLOSURE_V1 '+hashlib.sha256(_office_closure).hexdigest()+'\\n')\n"
            "   sys.stdout.flush()\n"
        )
    )
    body = (
        "import importlib.util,runpy,sys,tempfile\nfrom pathlib import Path\n"
        "with tempfile.TemporaryDirectory(prefix='template-native-sdk-bytecode-') as cache:\n"
        " sys.pycache_prefix=str(Path(cache).resolve())\n" + "\n".join(" " + line for line in audit.splitlines()) + "\n"
        " outcome={'kind':'not_started'}\n"
        " try:\n"
        "  if any(name=='infrastructure' or name.startswith('infrastructure.') for name in sys.modules):\n"
        "   raise ValueError('native SDK was imported before the original audited package selection')\n"
        f"  selected=Path({package_root!r})\n"
        "  spec=importlib.util.spec_from_file_location('infrastructure',selected/'__init__.py',"
        "submodule_search_locations=[str(selected)])\n"
        "  if spec is None or spec.loader is None:\n"
        "   raise ValueError('actual admitted SDK package cannot be loaded')\n"
        "  package=importlib.util.module_from_spec(spec)\n"
        "  sys.modules['infrastructure']=package\n"
        "  spec.loader.exec_module(package)\n"
        "  outcome={'kind':'started'}\n"
        f"  runpy.run_module({required_worker_module!r},run_name='__main__')\n"
        "  outcome={'kind':'returned_normally'}\n"
        " except BaseException as worker_error:\n"
        "  outcome={'kind':'raised','class':type(worker_error).__name__,'module':type(worker_error).__module__}\n"
        "  if isinstance(worker_error,SystemExit):\n"
        "   code=worker_error.code\n"
        "   outcome['system_exit_code']=code if type(code) in (int,str,type(None)) else {'type':type(code).__name__}\n"
        "  raise\n"
        " finally:\n"
        "  try:\n"
        "   from infrastructure.reporting.native_source_provider_bootstrap import "
        "retain_selected_sdk_execution_closure\n"
        "   retain_selected_sdk_execution_closure(\n"
        f"    _audit_scope,_audit_bytes,Path({package_root!r}),"
        f"tuple(Path(root) for root in {tuple(str(root) for root in provider_audit_roots)!r}),\n"
        f"    Path({str(implementation_binding_path)!r}),{externally_bound_implementation_sha256!r},\n"
        f"    Path({str(closure_directory)!r}),{closure_directory_identity!r},"
        f"outcome,deadline={deadline!r}{worker_keyword})\n"
        + office_seal
        + "  except BaseException as retention_error:\n"
        "   sys.stderr.write('selected SDK execution closure retention failed: '"
        "+type(retention_error).__name__+'\\n')\n"
    )
    return body


def selected_sdk_native_command(
    interpreter: Path,
    context: NativeSourceContext,
    worker_arguments: tuple[str, ...],
    *,
    provider_audit_roots: tuple[Path, ...],
    implementation_binding_path: Path,
    audit_closure_directory: Path,
    deadline: float,
) -> tuple[str, ...]:
    """Select the explicit already-admitted SDK while preserving the VENV launcher.

    worker_arguments must include supervisor-bound source/SDK input paths and
    hashes after Root's separately reviewed CLI/spec wiring. This function does
    not invent those bindings, launch a process or extend its deadline.
    """
    remaining(deadline)
    context.verify_correspondence(
        context.reference,
        context.bindings.current_root,
        context.current_source_reader,
        deadline,
    )
    expected = json_object_from_bytes(context.bindings.expected_implementation_bytes)
    runtime = expected.get("runtime_environment")
    if (
        not interpreter.is_absolute()
        or not isinstance(runtime, dict)
        or str(interpreter.resolve(strict=True)) != runtime.get("python_executable")
    ):
        raise ValueError("native launcher differs from the externally admitted actual SDK runtime")
    sdk_root = context.bindings.selected_sdk_package_root
    relative = implementation_binding_path.relative_to(context.bindings.current_root).as_posix()
    held = context.current_source_reader.read(relative)
    if held.content != context.bindings.expected_implementation_bytes:
        raise ValueError("native implementation input differs from externally admitted actual SDK bytes")
    closure_relative = audit_closure_directory.relative_to(context.bindings.current_root).as_posix()
    if not audit_closure_directory.is_relative_to(context.bindings.current_root / "output/readiness"):
        raise ValueError("native SDK closure destination is outside the supervisor runtime evidence plane")
    context.current_source_reader.public_path(closure_relative + "/.closure-directory-policy")
    metadata = audit_closure_directory.lstat()
    if not stat.S_ISDIR(metadata.st_mode) or any(audit_closure_directory.iterdir()):
        raise ValueError("native SDK closure destination must be the supervisor's fresh real directory")
    closure_identity = metadata.st_dev, metadata.st_ino
    hook = source_file_bytes(sdk_root / "core/bytecode_audit.py")
    files = expected.get("files")
    if (
        not isinstance(files, dict)
        or files.get("infrastructure/core/bytecode_audit.py") != hashlib.sha256(hook).hexdigest()
    ):
        raise ValueError("native SDK audit hook differs from its independently admitted implementation")
    command = (
        str(interpreter.absolute()),
        "-I",
        "-c",
        format_selected_sdk_native_bootstrap(
            hook,
            sdk_root,
            provider_audit_roots,
            implementation_binding_path,
            held.sha256,
            audit_closure_directory,
            closure_identity,
            deadline,
        ),
        *worker_arguments,
    )
    context.verify_correspondence(
        context.reference,
        context.bindings.current_root,
        context.current_source_reader,
        deadline,
    )
    remaining(deadline)
    return command
