"""Cold installed SDK capture/controller invocation under the original clock."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from infrastructure.core.implementation_custody import _format_bytecode_audit_bootstrap, source_file_bytes
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_installed_preparation import NativePreparedRuntime
from infrastructure.reporting.native_prepared_code_readback import validate_prepared_code
from infrastructure.reporting.native_source_provider_bootstrap import (
    NATIVE_CAPTURE_MODULE,
    NATIVE_CONTROLLER_MODULE,
    NATIVE_READER_MODULE,
    format_selected_sdk_native_bootstrap,
)
from infrastructure.reporting.native_tool_process import run_native_tool_process


def capture_prepared_sdk(prepared: NativePreparedRuntime, *, environment: dict[str, str]) -> tuple[Path, bytes]:
    """Observe actual installed metadata/RECORD and close its genuine Code.

    Initial capture is DATA from a real supervised child of the independently
    Source-admitted install. Its hash is learned after observation. The parent
    checks Source-wheel membership and signed OS/Code before forwarding those
    bytes as its explicit nomination to the separate cold Source admission.
    """
    prepared.verify()
    destination = prepared.evidence / "implementation-input.json"
    closure = prepared.evidence / "capture-code"
    closure.mkdir(mode=0o700)
    identity = closure.stat().st_dev, closure.stat().st_ino
    hook = source_file_bytes(prepared.sdk_package_root / "core/bytecode_audit.py")
    audit = _format_bytecode_audit_bootstrap(
        hook, prepared.sdk_package_root / "core/bytecode_audit.py", (prepared.sdk_package_root,), None
    )
    sdk = str(prepared.sdk_package_root)
    body = (
        "import importlib.util,runpy,sys,tempfile,hashlib\nfrom pathlib import Path\n"
        "with tempfile.TemporaryDirectory(prefix='template-cold-sdk-capture-') as temporary:\n"
        " sys.pycache_prefix=str(Path(temporary).resolve())\n"
        + "\n".join(" " + line for line in audit.splitlines())
        + "\n"
        " outcome={'kind':'not_started'}\n"
        " try:\n"
        f"  selected=Path({sdk!r})\n"
        "  spec=importlib.util.spec_from_file_location('infrastructure',selected/'__init__.py',"
        "submodule_search_locations=[str(selected)])\n"
        "  package=importlib.util.module_from_spec(spec);sys.modules['infrastructure']=package;"
        "spec.loader.exec_module(package)\n"
        f"  runpy.run_module({NATIVE_CAPTURE_MODULE!r},run_name='__main__')\n"
        "  outcome={'kind':'returned_normally'}\n"
        " except BaseException as error:\n"
        "  outcome={'kind':'raised','class':type(error).__name__,'module':type(error).__module__}\n"
        "  if isinstance(error,SystemExit):outcome['system_exit_code']=error.code\n"
        "  raise\n"
        " finally:\n"
        "  try:\n"
        "   from infrastructure.reporting.native_source_provider_bootstrap "
        "import retain_selected_sdk_execution_closure\n"
        f"   observed=Path({str(destination)!r}).read_bytes()\n"
        "   retain_selected_sdk_execution_closure(_audit_scope,_audit_bytes,selected,(),"
        f"Path({str(destination)!r}),hashlib.sha256(observed).hexdigest(),Path({str(closure)!r}),{identity!r},outcome,"
        f"deadline={prepared.deadline!r},required_worker_module={NATIVE_CAPTURE_MODULE!r})\n"
        "  except BaseException as retention_error:\n"
        "   sys.stderr.write('actual capture Code retention failed: '+type(retention_error).__name__+'\\n')\n"
    )
    compile(body, "<actual-cold-installed-capture>", "exec")
    command = [
        "-I",
        "-c",
        body,
        "--root",
        str(prepared.current_root),
        "--core-wheel",
        str(prepared.core_wheel.path),
        "--core-wheel-sha256",
        prepared.core_wheel.sha256,
        "--destination",
        str(destination),
        "--deadline",
        str(prepared.deadline),
    ]
    result = run_native_tool_process(
        prepared.evidence,
        str(prepared.python),
        command,
        cwd=prepared.current_root,
        env=environment,
        deadline=prepared.deadline,
        purpose="actual-sdk-capture",
        preserve_nominated_launcher=True,
    )
    if result["accepted"] is not True or result["original_exit_code"] != 0:
        raise NativeInstalledInvocationFailure(result)
    raw = source_file_bytes(destination)
    validate_prepared_code(prepared, closure, raw, result, role=NATIVE_CAPTURE_MODULE, provider_sources={})
    prepared.verify()
    return destination, raw


class NativeInstalledInvocationFailure(RuntimeError):
    """Retain actual original result without overwriting a signed nonzero."""

    def __init__(self, result: dict[str, Any]) -> None:
        super().__init__("actual cold installed invocation refused or failed")
        self.result = result


def launch_prepared_native(
    prepared: NativePreparedRuntime,
    implementation: Path,
    raw: bytes,
    *,
    role: str,
    arguments: tuple[str, ...],
    pdfium_roots: tuple[Path, ...],
    pdfium_sources: dict[str, str],
    environment: dict[str, str],
) -> dict[str, Any]:
    """Run exactly the Source-owned original controller or independent reader."""
    if role not in (NATIVE_CONTROLLER_MODULE, NATIVE_READER_MODULE):
        raise ValueError("prepared launch permits only the exact controller or independent-reader role")
    prepared.verify()
    if source_file_bytes(implementation) != raw:
        raise ValueError("actual captured installed input changed before cold launch")
    runtime_wheels = prepared.selected_runtime_provider_wheels()
    roots = tuple(prepared.site / target for wheel in runtime_wheels.values() for target in wheel.targets)
    provider_sources = {
        str(prepared.site / name): digest
        for wheel in runtime_wheels.values()
        for name, digest in wheel.members.items()
        if name.endswith(".py")
    }
    provider_sources.update(pdfium_sources)
    roots = tuple(dict.fromkeys((*roots, *pdfium_roots)))
    closure = prepared.evidence / ("controller-code" if role == NATIVE_CONTROLLER_MODULE else "reader-code")
    closure.mkdir(mode=0o700)
    identity = closure.stat().st_dev, closure.stat().st_ino
    hook = source_file_bytes(prepared.sdk_package_root / "core/bytecode_audit.py")
    body = format_selected_sdk_native_bootstrap(
        hook,
        prepared.sdk_package_root,
        roots,
        implementation,
        hashlib.sha256(raw).hexdigest(),
        closure,
        identity,
        prepared.deadline,
        required_worker_module=role,
    )
    result = run_native_tool_process(
        prepared.evidence,
        str(prepared.python),
        ["-I", "-c", body, *arguments],
        cwd=prepared.current_root,
        env=environment,
        deadline=prepared.deadline,
        purpose="actual-native-controller" if role == NATIVE_CONTROLLER_MODULE else "actual-native-reader",
        preserve_nominated_launcher=True,
    )
    # A native refusal/nonzero remains the real observed result. A retention
    # failure can block OS0, but can never convert an original failure to OS0.
    if result["accepted"] is not True or result["original_exit_code"] != 0:
        raise NativeInstalledInvocationFailure(result)
    validate_prepared_code(prepared, closure, raw, result, role=role, provider_sources=provider_sources)
    remaining(prepared.deadline)
    prepared.verify()
    return result
