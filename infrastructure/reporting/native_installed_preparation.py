"""Source-locked fresh wheel/runtime preparation for the genuine native launcher.

Preparation returns explicit nominations and retained real process observations.
It grants no NativeSourceContext, original completion, loaded-library or kernel
admission. The selected installed controller must independently admit those.
"""

from __future__ import annotations

import hashlib
import stat
import types
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from infrastructure.core.pipeline.artifacts._inventory import _is_ignored_output_relative
from infrastructure.core.pipeline.fingerprints import _ROOT_SOURCE_CONTROLS
from infrastructure.core.files.secure_write import read_bytes_confined
from infrastructure.core.implementation_custody import _format_bytecode_audit_bootstrap, source_file_bytes
from infrastructure.project.installed_acceptance_artifacts import AdmittedWheel, freeze_wheel_bytes, prepare_export
from infrastructure.project.installed_acceptance_runtime import freeze_locked_metadata, install_admitted_wheels
from infrastructure.project.public_acceptance_scope import RuntimeScope
from infrastructure.project.public_reference import _canonical_inventory
from infrastructure.project.public_reference_git import (
    GitReference,
    blob_identity,
    committed_blobs,
    inventory,
    remaining,
)
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.project.public_package_dependencies import local_dependency_closure
from infrastructure.project.locked_dependency_export import normalize_locked_dependency_export
from infrastructure.reporting.readiness_receipts import (
    _READINESS_SOURCE_METADATA_NAMES,
    _public_roots,
    source_fingerprint,
)
from infrastructure.reporting.release_readiness_profile import required_profile
from infrastructure.reporting.release_readiness_snapshot import (
    PUBLIC_ROOT_FILES,
    SnapshotReader,
    json_object_from_bytes,
)
from infrastructure.reporting.native_tool_process import run_native_tool_process

SCHEMA = "template-native-prepared-installed-runtime-v1"
MAX_WHEEL = 64 * 1024 * 1024
_LOCATION_PROBE = (
    "import importlib.util,importlib.metadata,json,sys,sysconfig;"
    "s=importlib.util.find_spec('infrastructure');"
    "print(json.dumps({'sdk':s.origin if s else None,'site':sysconfig.get_path('purelib'),"
    "'version':importlib.metadata.version('research-project-template'),"
    "'executable':sys.executable,'release':list(sys.version_info)}))"
)


class NativePreparationFailure(RuntimeError):
    """Retain genuine signed preparation failures for the actual outer caller."""

    def __init__(self, result: dict[str, Any]) -> None:
        super().__init__(f"native preparation refused: actual original OS exit {result['original_exit_code']}")
        self.result = result


@dataclass(frozen=True)
class NativePreparedRuntime:
    """Actual fresh nominated install, not a receipt-derived native capability."""

    source_root: Path
    current_root: Path
    source_commit: str
    source_identity: str
    python: Path
    sdk_package_root: Path
    site: Path
    core_wheel: AdmittedWheel
    provider_wheels: Mapping[str, AdmittedWheel]
    native_provider_scopes: tuple[str, ...]
    initial_source_files: Mapping[str, str]
    initial_source_reader: SnapshotReader
    deadline: float
    operation_started: float
    scratch: Path
    evidence: Path
    interpreter_release: tuple[Any, ...]

    def verify(self) -> None:
        """Recheck Source, installed bodies and the actual nominated SDK origin."""
        remaining(self.deadline)
        if not self.initial_source_reader.unchanged():
            raise ValueError("native preparation Source inputs changed")
        if RuntimeScope(self.source_root, "root").source_identity() != self.source_identity:
            raise ValueError("native preparation Source identity changed")
        inventory(self.source_root, self.source_commit, self.deadline)
        actual = {
            path.relative_to(self.sdk_package_root.parent).as_posix(): hashlib.sha256(
                source_file_bytes(path)
            ).hexdigest()
            for path in self.sdk_package_root.rglob("*.py")
        }
        expected = {
            name: digest
            for name, digest in self.core_wheel.members.items()
            if name.startswith("infrastructure/") and name.endswith(".py")
        }
        if actual != expected:
            raise ValueError("prepared selected installed SDK differs from its Source-admitted wheel")
        selected_scopes = tuple(
            dict.fromkeys(
                provider
                for scope in self.provider_wheels
                for provider in local_dependency_closure(self.source_root, scope, reader=self.initial_source_reader)
                if provider != "root"
            )
        )
        if self.native_provider_scopes != selected_scopes:
            raise ValueError("prepared installed provider scopes differ from the actual Source local closure")
        for scope in self.native_provider_scopes:
            if scope not in self.provider_wheels:
                raise ValueError("prepared selected runtime provider lacks its Source-admitted wheel")
            for name, digest in self.provider_wheels[scope].members.items():
                remaining(self.deadline)
                body = read_bytes_confined(self.site, self.site / name, max_bytes=MAX_WHEEL)
                if hashlib.sha256(body).hexdigest() != digest:
                    raise ValueError("prepared installed provider body differs from its Source-admitted wheel")
        for wheel in (self.core_wheel, *self.provider_wheels.values()):
            if (
                hashlib.sha256(read_bytes_confined(self.scratch, wheel.path, max_bytes=MAX_WHEEL)).hexdigest()
                != wheel.sha256
            ):
                raise ValueError("prepared admitted wheel changed")
        if not self.initial_source_reader.unchanged():
            raise ValueError("native preparation Source local provider closure changed during verification")
        remaining(self.deadline)

    def selected_runtime_provider_wheels(self) -> Mapping[str, AdmittedWheel]:
        """Return only Source-required, genuinely installed provider nominations.

        Frozen wheels for the other public scopes remain DATA. The selected
        controller/reader independently admits actual runtime custody; neither
        this mapping nor its audit coverage grants a native capability.
        """
        self.verify()
        return types.MappingProxyType({scope: self.provider_wheels[scope] for scope in self.native_provider_scopes})


def _regular_directory(path: Path) -> None:
    if (
        not path.is_absolute()
        or ".." in path.parts
        or path != path.resolve(strict=True)
        or not stat.S_ISDIR(path.lstat().st_mode)
    ):
        raise ValueError("native preparation requires explicit real absolute directories")


def _execute(
    directory: Path,
    command: tuple[str, ...],
    *,
    cwd: Path,
    env: dict[str, str],
    deadline: float,
    label: str,
    preserve_python: bool = False,
) -> dict[str, Any]:
    remaining(deadline)
    result = run_native_tool_process(
        directory,
        command[0],
        list(command[1:]),
        cwd=cwd,
        env=env,
        deadline=deadline,
        purpose=label,
        preserve_nominated_launcher=preserve_python,
    )
    if result["accepted"] is not True or result["original_exit_code"] != 0:
        # The helper already retained the genuine signed OS outcome/raw bytes.
        # A failed preparation never installs a replacement or calls native.
        raise NativePreparationFailure(result)
    remaining(deadline)
    return result


def _committed_public_bodies(source_root: Path, reference: GitReference, deadline: float) -> set[str]:
    """Select committed paths lexically, including deleted canonical bodies.

    Reuse the canonical source/output exclusions before any public read. The
    current filesystem cannot nominate which committed bodies are required.
    """
    roots, excluded = _public_roots(source_root)
    prefixes = tuple(root.relative_to(source_root).as_posix() + "/" for root in roots)
    exclusions = {root.relative_to(source_root).as_posix() for root in excluded}
    excluded_prefixes = tuple(root + "/" for root in exclusions)
    outputs = tuple("projects/" + scope + "/output/" for scope in PUBLIC_PROJECT_NAMES)
    selected = set()
    for relative in committed_blobs(reference):
        remaining(deadline)
        if relative in PUBLIC_ROOT_FILES:
            selected.add(relative)
            continue
        output = next((prefix for prefix in outputs if relative.startswith(prefix)), None)
        if output is not None:
            if not _is_ignored_output_relative(Path(relative[len(output) :])):
                selected.add(relative)
            continue
        base = next((prefix for prefix in prefixes if relative.startswith(prefix)), None)
        if base is None or relative in exclusions or relative.startswith(excluded_prefixes):
            continue
        parts = relative[len(base) :].split("/")
        if (
            any(part in _READINESS_SOURCE_METADATA_NAMES | {"__pycache__"} for part in parts)
            or any(Path(part).suffix in {".pyc", ".pyo"} for part in parts)
            or parts[0] in _ROOT_SOURCE_CONTROLS
            or len(parts) >= 2
            and parts[0] == "src"
            and parts[1].endswith(".egg-info")
        ):
            continue
        selected.add(relative)
    return selected


def admitted_source_files(
    source_root: Path,
    reader: SnapshotReader,
    reference: GitReference,
    deadline: float,
) -> dict[str, str]:
    """Bind every canonical public source body to its committed blob.

    Only the canonical public inventory is read through the public reader, as
    the public reference admission does. Tracked files outside that policy
    (agent, editor and resource-root documents) are never public DATA here;
    an untracked, substituted or edited public body refuses preparation.
    """
    committed = committed_blobs(reference)
    records = _canonical_inventory(source_root)
    observed = {relative for relative, kind, _ in records if kind in {"file", "deliverable"}}
    expected = _committed_public_bodies(source_root, reference, deadline)
    if expected - observed:
        raise ValueError("native preparation Source is missing a committed canonical body")
    source_files: dict[str, str] = {}
    for relative, kind, digest in records:
        remaining(deadline)
        if kind == "missing":
            raise ValueError("native preparation Source has a missing canonical source root")
        if kind not in {"file", "deliverable"}:
            continue
        binding = committed.get(relative)
        if binding is None:
            raise ValueError("native preparation Source body is untracked or differs from the committed blob")
        record, object_format = binding
        snapshot = reader.read(relative)
        if kind == "file" and snapshot.sha256 != digest:
            raise ValueError("native preparation Source body changed between inventory and admission")
        if blob_identity(snapshot.content, object_format) != record.oid:
            raise ValueError("native preparation Source body differs from its original committed blob")
        source_files[relative] = snapshot.sha256
    if not source_files:
        raise ValueError("native preparation requires a nonempty canonical public source inventory")
    return source_files


def prepare_native_installed_runtime(
    source_root: Path,
    current_root: Path,
    scratch: Path,
    evidence: Path,
    *,
    python: Path,
    uv: Path,
    source_commit: str,
    source_identity: str,
    operation_started: float,
    deadline: float,
    env: dict[str, str],
    scopes: tuple[str, ...] = PUBLIC_PROJECT_NAMES,
) -> NativePreparedRuntime:
    """Build exact4.0.1 plus actual public provider wheels, then offline install.

    The outer Source harness nominates both real full-Git roots, exact commit,
    Source fingerprint and already-live clock. This function never computes and
    self-approves those expectations. It performs no Source checkout mutation.
    Each UV step retains its real PID/signed OS/raw streams/guardian identity.
    """
    remaining(deadline)
    for path in (source_root, current_root, scratch, evidence):
        _regular_directory(path)
    if current_root == source_root or scratch.is_relative_to(source_root) or scratch.is_relative_to(current_root):
        raise ValueError("native preparation requires a separate Source mirror and outside-Source fresh install")
    if any(scratch.iterdir()) or any(evidence.iterdir()):
        raise ValueError("native preparation directories must be fresh")
    if not python.is_absolute() or not uv.is_absolute() or not 0 < operation_started < deadline:
        raise ValueError("native preparation requires actual explicitly nominated tools and original clock")
    if not scopes or len(set(scopes)) != len(scopes) or any(scope not in PUBLIC_PROJECT_NAMES for scope in scopes):
        raise ValueError("native preparation requires unique canonical provider scopes")
    reader = SnapshotReader(source_root)
    reference = inventory(source_root, source_commit, deadline)
    inventory(current_root, source_commit, deadline)
    if (
        RuntimeScope(source_root, "root").source_identity() != source_identity
        or RuntimeScope(current_root, "root").source_identity() != source_identity
    ):
        raise ValueError("native preparation roots differ from the external Source fingerprint")
    rows, faults = required_profile(source_root, reader, source_fingerprint(source_root))
    if faults:
        raise ValueError("native preparation requires the complete valid source-owned release profile")
    lookup = {row.scope: row for row in rows if row.kind == "installed"}
    if lookup["root"].version != "4.0.1" or lookup["root"].package != "research-project-template":
        raise ValueError("native preparation requires genuine intended Source4.0.1 metadata")
    source_files = admitted_source_files(source_root, reader, reference, deadline)
    metadata = freeze_locked_metadata(source_root, scratch)
    selected_env = dict(env, UV_LINK_MODE="copy")
    for key in ("PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV", "PYTHONPYCACHEPREFIX", "PYTHONDONTWRITEBYTECODE"):
        selected_env.pop(key, None)

    def run(command: tuple[str, ...], label: str) -> dict[str, Any]:
        if not metadata.unchanged() or not reader.unchanged():
            raise ValueError("native preparation locked Source changed before actual tool execution")
        result = _execute(evidence, command, cwd=scratch, env=selected_env, deadline=deadline, label=label)
        if not metadata.unchanged() or not reader.unchanged():
            raise ValueError("native preparation locked Source changed after actual tool execution")
        return result

    build_requirements = scratch / "build-requirements.txt"
    run(
        (
            str(uv),
            "export",
            "--directory",
            str(metadata.root),
            "--locked",
            "--offline",
            "--only-group",
            "installed-build",
            "--no-emit-project",
            "--no-header",
            "--no-annotate",
            "--output-file",
            str(build_requirements),
        ),
        "build-lock",
    )
    build_env = scratch / "build-environment"
    run(
        (str(uv), "venv", "--no-project", "--no-python-downloads", "--python", str(python), str(build_env)),
        "build-venv",
    )
    run(
        (
            str(uv),
            "pip",
            "sync",
            "--offline",
            "--no-config",
            "--no-build",
            "--require-hashes",
            "--python",
            str(build_env / "bin/python"),
            str(build_requirements),
        ),
        "build-tools",
    )
    wheels: dict[str, AdmittedWheel] = {}
    for ordinal, scope in enumerate(("root", *scopes)):
        cell = scratch / f"scope-{ordinal:03d}"
        cell.mkdir(mode=0o700)
        cell_evidence = evidence / f"scope-{ordinal:03d}"
        cell_evidence.mkdir(mode=0o700)
        source, _ = prepare_export(
            current_root,
            lookup[scope],
            cell,
            current_root / "output/readiness" / f"native-preparation-{scratch.name}" / f"scope-{ordinal:03d}",
            deadline_monotonic=deadline,
        )
        wheel_dir = cell / "wheels"
        run(
            (
                str(uv),
                "build",
                "--wheel",
                "--offline",
                "--no-config",
                "--no-python-downloads",
                "--no-build-isolation",
                "--python",
                str(build_env / "bin/python"),
                "--out-dir",
                str(wheel_dir),
                str(source),
            ),
            f"wheel-build-{ordinal:03d}",
        )
        actual = tuple(wheel_dir.glob("*.whl"))
        if len(actual) != 1:
            raise ValueError("native Source build did not produce exactly one candidate wheel")
        wheels[scope] = freeze_wheel_bytes(
            source_root,
            lookup[scope],
            read_bytes_confined(scratch, actual[0], max_bytes=MAX_WHEEL),
            scratch,
            actual[0].name,
            reader=reader,
        )
    runtime_requirements = scratch / "runtime-requirements.txt"
    run(
        (
            str(uv),
            "export",
            "--directory",
            str(metadata.root),
            "--locked",
            "--offline",
            "--no-default-groups",
            "--group",
            "public-exemplars",
            "--group",
            "rendering",
            "--group",
            "rendering-pptx",
            "--no-emit-project",
            "--no-emit-local",
            "--no-header",
            "--no-annotate",
            "--output-file",
            str(runtime_requirements),
        ),
        "runtime-lock",
    )
    normalize_locked_dependency_export(metadata.root, runtime_requirements)
    if not metadata.unchanged():
        raise ValueError("native preparation locked Source changed during dependency export normalization")
    # This runtime observes native formats with the Root SDK. It is not the
    # independent installed/export/runtime project matrix. Keep every project
    # wheel frozen as Source DATA; install only the actual Source-declared
    # namespaced local providers required by native callers. Never combine the
    # independent project's third-party lock pins or resolve a precedence.
    native_provider_scopes = tuple(
        dict.fromkeys(
            provider
            for scope in scopes
            for provider in local_dependency_closure(source_root, scope, reader=reader)
            if provider != "root"
        )
    )
    runtime = scratch / "native-environment"
    run(
        (str(uv), "venv", "--no-project", "--no-python-downloads", "--python", str(python), str(runtime)),
        "runtime-venv",
    )
    installed_python = runtime / "bin/python"
    run(
        (
            str(uv),
            "pip",
            "sync",
            "--offline",
            "--no-config",
            "--no-build",
            "--require-hashes",
            "--allow-empty-requirements",
            "--python",
            str(installed_python),
            str(runtime_requirements),
        ),
        "runtime-dependencies",
    )
    install_admitted_wheels(
        scratch,
        installed_python,
        str(uv),
        [wheels["root"], *(wheels[scope] for scope in native_provider_scopes)],
        run,
    )
    run((str(uv), "pip", "check", "--python", str(installed_python)), "runtime-dependency-check")
    location = _execute(
        evidence,
        (str(installed_python), "-I", "-c", _LOCATION_PROBE),
        cwd=scratch,
        env=selected_env,
        deadline=deadline,
        label="actual-installed-location",
        preserve_python=True,
    )
    observed = json_object_from_bytes(location["stdout"].encode())
    if observed["version"] != "4.0.1" or observed["executable"] != str(installed_python):
        raise ValueError("prepared Python selected another distribution/launcher")
    sdk = Path(observed["sdk"]).parent
    site = Path(observed["site"])
    if sdk != site / "infrastructure" or not sdk.is_relative_to(runtime):
        raise ValueError("prepared selected SDK is outside the independently installed runtime")
    value = NativePreparedRuntime(
        source_root,
        current_root,
        source_commit,
        source_identity,
        installed_python,
        sdk,
        site,
        wheels["root"],
        types.MappingProxyType({scope: wheels[scope] for scope in scopes}),
        native_provider_scopes,
        types.MappingProxyType(source_files),
        reader,
        deadline,
        operation_started,
        scratch,
        evidence,
        tuple(observed["release"]),
    )
    value.verify()
    return value


def format_prepared_implementation_capture(
    prepared: NativePreparedRuntime, *, prefix: Path, destination: Path
) -> tuple[str, ...]:
    """Construct the genuine stdlib-first installed-SDK nomination observation.

    The parent validates actual selected wheel bodies before launch. The cold
    native controller subsequently re-admits Source/SDK/runtime independently.
    This bootstrap never puts Source ROOT DATA or PYTHONPATH on sys.path.
    """
    prepared.verify()
    if any(prefix.iterdir()) or not prefix.is_absolute() or not destination.is_relative_to(prepared.scratch):
        raise ValueError("implementation capture requires a fresh owned prefix and outside-Source output")
    hook = source_file_bytes(prepared.sdk_package_root / "core/bytecode_audit.py")
    expected_hook = prepared.core_wheel.members["infrastructure/core/bytecode_audit.py"]
    if hashlib.sha256(hook).hexdigest() != expected_hook:
        raise ValueError("implementation capture hook differs from Source-admitted wheel")
    audit = _format_bytecode_audit_bootstrap(
        hook, prepared.sdk_package_root / "core/bytecode_audit.py", (prepared.sdk_package_root,), prefix
    )
    body = audit + (
        "import importlib.util,json,sys\nfrom pathlib import Path\n"
        f"selected=Path({str(prepared.sdk_package_root)!r})\n"
        "spec=importlib.util.spec_from_file_location('infrastructure',selected/'__init__.py',submodule_search_locations=[str(selected)])\n"
        "package=importlib.util.module_from_spec(spec);sys.modules['infrastructure']=package;spec.loader.exec_module(package)\n"
        "from infrastructure.core.implementation_custody import "
        "capture_implementation_custody,verify_implementation_custody\n"
        "from infrastructure.core.files.secure_write import atomic_write_bytes_confined\n"
        "value=capture_implementation_custody(fresh_pycache_prefix=Path(sys.pycache_prefix))\n"
        "if value['binding_kind']!='installed-distribution' or value['distribution']['version']!='4.0.1':"
        "raise ValueError('actual installed4.0.1 required')\n"
        f"atomic_write_bytes_confined(Path({str(prepared.scratch)!r}),Path({str(destination)!r}),(json.dumps(value,sort_keys=True,separators=(',',':'))+'\\n').encode(),mode=0o600)\n"
        "verify_implementation_custody(value,fresh_pycache_prefix=Path(sys.pycache_prefix))\n"
    )
    compile(body, "<prepared-installed-implementation-capture>", "exec")
    return str(prepared.python), "-I", "-X", f"pycache_prefix={prefix}", "-c", body
