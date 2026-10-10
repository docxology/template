"""Live external native inputs and original launch custody, separate from JSON.

Only the original controller or independently authenticated reader supplies
these objects. Decoding receipts never constructs them or starts a clock.
"""

from __future__ import annotations

import hashlib
import re
import stat
import sys
import types
import math
import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from infrastructure.core.bytecode_audit import (
    MAX_CACHE_BYTES,
    MAX_EXECUTIONS,
    canonical_code,
)
from infrastructure.core.implementation_custody import source_file_bytes
from infrastructure.project.public_acceptance_dependencies import (
    admit_runtime_providers,
    runtime_provider_roots,
)
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_projection_contracts import (
    ProjectionSourceUnsupported,
)
from infrastructure.reporting.native_source_external_admission import (
    NativeSourceContext,
    _anchored_directory_identity,
    admit_explicitly_bound_native_source,
    validate_original_source_descriptor,
)
from infrastructure.reporting.native_source_provider_bootstrap import (
    CLOSURE_SCHEMA,
    format_selected_sdk_native_bootstrap,
)
from infrastructure.reporting.readiness_receipts import source_fingerprint
from infrastructure.reporting.release_readiness_profile import required_profile
from infrastructure.reporting.release_readiness_snapshot import (
    ArtifactSnapshot,
    SnapshotReader,
)
from infrastructure.reporting.release_readiness_snapshot import json_object_from_bytes

from infrastructure.reporting.native_full_worker_pdfium import (
    NativePDFiumSelection,
    NativePDFiumProvider,
    admit_full_worker_pdfium_provider,
    pdfium_worker_arguments,
    retained_pdfium_code_sources,
)

if TYPE_CHECKING:
    from infrastructure.reporting.native_authenticated_original_pdfium import NativeAuthenticatedOriginalPDFium
    from infrastructure.reporting.native_office_diagram_runtime import PDFiumRuntimeAdmission
    from infrastructure.reporting.native_office_full_worker_context import NativeOfficeReaderSelection
    from infrastructure.reporting.native_format_pdf_source_decode_bounds import SourceImageDecodeBudget
    from infrastructure.reporting.native_current_reader_inputs import NativeCurrentAnalysisInputs

JOINT_SCHEMA = "template-native-source-launch-inputs-v4"


@dataclass(frozen=True)
class NativeSDKSelection:
    """Independently nominated selected SDK and exact admitted custody input."""

    package_root: Path
    implementation_bytes: bytes


@dataclass(frozen=True)
class NativeOriginalLaunch:
    """Actual original supervisor observations, held outside producer receipts.

    Portable readers require their authenticated original-process custodian to
    supply these facts. A receipt parser or native worker must never mint them.
    """

    scope: str
    run_id: str
    specification_sha256: str
    specification_relative: str
    process_relative: str
    closure_relative: str
    native_execution_relative: str
    descriptor_sha256: str
    implementation_sha256: str
    process_sha256: str
    closure_sha256: str
    command: tuple[str, ...]
    source_binding: tuple[str, str, str]
    native_execution_sha256: str
    original_deadline: float
    observed_completion: float
    pdfium_provider: NativePDFiumProvider | NativeAuthenticatedOriginalPDFium | None = None


@dataclass(frozen=True)
class NativeReaderOperation:
    """One independently admitted current context and one already-live clock."""

    source: NativeSourceContext
    deadline: float
    originals: Mapping[str, NativeOriginalLaunch]
    pdfium_providers: Mapping[str, NativePDFiumProvider] = field(default_factory=dict)
    office_reader_selection: NativeOfficeReaderSelection | None = None
    pdfium_runtime_admissions: Mapping[str, PDFiumRuntimeAdmission] = field(default_factory=dict)
    office_decoded_pixel_budget: SourceImageDecodeBudget | None = None
    current_analysis: NativeCurrentAnalysisInputs | None = field(default=None, kw_only=True)

    def __post_init__(self) -> None:
        remaining(self.deadline)
        if self.current_analysis is not None:
            from infrastructure.reporting.native_current_reader_inputs import NativeCurrentAnalysisInputs

            if not isinstance(self.current_analysis, NativeCurrentAnalysisInputs):
                raise ValueError("native reader needs genuine typed Current Source nominations")
            self.current_analysis.verify(self.source, set(self.originals), self.deadline)
        if self.office_decoded_pixel_budget is not None:
            from infrastructure.reporting.native_format_pdf_source_decode_bounds import SourceImageDecodeBudget

            if not isinstance(self.office_decoded_pixel_budget, SourceImageDecodeBudget):
                raise ValueError("native reader requires its actual held shared decoded-pixel budget")
        if self.office_reader_selection is not None:
            from infrastructure.reporting.native_office_full_worker_context import NativeOfficeReaderSelection

            if not isinstance(self.office_reader_selection, NativeOfficeReaderSelection):
                raise ValueError("native reader requires an independently supplied typed Office selection")
        from infrastructure.reporting.native_office_diagram_runtime import PDFiumRuntimeAdmission

        for scope, runtime in self.pdfium_runtime_admissions.items():
            provider = self.pdfium_providers.get(scope)
            if (
                not isinstance(runtime, PDFiumRuntimeAdmission)
                or not isinstance(provider, NativePDFiumProvider)
                or runtime.source is not self.source
                or runtime.scope != scope
                or runtime.site != provider.selection.site
                or runtime.wheel != provider.selection.wheel
                or runtime.owner_pid != os.getpid()
                or runtime.deadline != self.deadline
            ):
                raise ValueError("native reader needs its actual per-scope preimport PDFium runtime owner")
            runtime.verify()
        object.__setattr__(self, "originals", types.MappingProxyType(dict(self.originals)))
        object.__setattr__(self, "pdfium_providers", types.MappingProxyType(dict(self.pdfium_providers)))
        object.__setattr__(
            self, "pdfium_runtime_admissions", types.MappingProxyType(dict(self.pdfium_runtime_admissions))
        )

    def verify(self, reader: SnapshotReader) -> None:
        remaining(self.deadline)
        _require_installed_sdk(self.source.bindings.expected_implementation_bytes)
        self.source.verify_correspondence(self.source.reference, reader.root, reader, self.deadline)


def require_native_operation(reader: SnapshotReader) -> NativeReaderOperation:
    operation = reader.native_operation
    if not isinstance(operation, NativeReaderOperation):
        raise ProjectionSourceUnsupported(
            "native replay requires externally admitted source and original launch custody"
        )
    operation.verify(reader)
    return operation


def admit_native_source_operation(
    root: Path,
    sdk: NativeSDKSelection,
    *,
    run_id: str,
    deadline: float,
    environment: Mapping[str, str],
) -> NativeSourceContext:
    """Call genuine Source/Git/SDK admission without transported expectations."""
    remaining(deadline)
    _require_installed_sdk(sdk.implementation_bytes)
    metadata = root.lstat()
    if not stat.S_ISDIR(metadata.st_mode):
        raise ValueError("native current root is not a real supervisor-nominated directory")
    context = admit_explicitly_bound_native_source(
        root,
        environment=environment,
        current_root_identity=(metadata.st_dev, metadata.st_ino),
        selected_sdk_package_root=sdk.package_root,
        expected_implementation_bytes=sdk.implementation_bytes,
        run_id=run_id,
        deadline=deadline,
        fresh_pycache_prefix=Path(sys.pycache_prefix) if sys.pycache_prefix else None,
    )
    if context is None:
        raise ProjectionSourceUnsupported("native execution requires the explicit original public reference binding")
    return context


def _require_installed_sdk(raw: bytes) -> None:
    selected = json_object_from_bytes(raw)
    distribution = selected.get("distribution")
    if selected.get("binding_kind") != "installed-distribution" or not isinstance(distribution, dict):
        raise ProjectionSourceUnsupported(
            "native joint source execution requires genuine selected installed SDK custody"
        )
    if distribution.get("name") != "research-project-template" or distribution.get("version") != "4.0.1":
        raise ValueError("native selected SDK distribution identity is invalid")


def _identity_pair(value: Any) -> tuple[int, int]:
    if (
        not isinstance(value, (list, tuple))
        or len(value) != 2
        or any(type(item) is not int or item < 0 for item in value)
    ):
        raise ValueError("native physical directory binding is invalid")
    return value[0], value[1]


def admit_native_reader_operation(
    root: Path,
    sdk: NativeSDKSelection,
    originals: Mapping[str, NativeOriginalLaunch],
    *,
    run_id: str,
    deadline: float,
    environment: Mapping[str, str],
    pdfium_selection: NativePDFiumSelection,
    office_reader_selection: NativeOfficeReaderSelection,
    office_decoded_pixel_budget: SourceImageDecodeBudget | None = None,
    current_analysis: NativeCurrentAnalysisInputs | None = None,
) -> NativeReaderOperation:
    """One outer reader factory; caller owns the existing 14,400 second clock.

    Originals must already be authenticated by the original-process custodian.
    This factory never derives them from receipt fields or starts a clock.
    """
    source = admit_native_source_operation(root, sdk, run_id=run_id, deadline=deadline, environment=environment)
    providers = {
        scope: admit_full_worker_pdfium_provider(pdfium_selection, source, scope=scope, deadline=deadline)
        for scope in originals
    }
    from infrastructure.reporting.native_office_diagram_runtime import admit_pdfium_runtime

    runtimes = {
        scope: admit_pdfium_runtime(
            source, scope=scope, site=provider.selection.site, wheel=provider.selection.wheel, deadline=deadline
        )
        for scope, provider in providers.items()
    }
    operation = NativeReaderOperation(
        source,
        deadline,
        originals,
        providers,
        office_reader_selection,
        runtimes,
        office_decoded_pixel_budget,
        current_analysis=current_analysis,
    )
    operation.verify(SnapshotReader(root))
    return operation


def admitted_native_providers(
    context: NativeSourceContext,
    scope: str,
    wheels: Mapping[str, Path],
    interpreter: Path,
    *,
    deadline: float,
) -> tuple[dict[str, Any], tuple[Path, ...]]:
    """Preserve existing genuine namespaced wheel/source/version admission."""
    remaining(deadline)
    root = context.bindings.current_root
    reader = context.current_source_reader
    context.verify_correspondence(context.reference, root, reader, deadline)
    requirements, faults = required_profile(root, reader, source_fingerprint(root))
    if faults:
        raise ValueError("native provider admission needs the complete current source profile")
    lookup = {row.id: row for row in requirements}
    providers = admit_runtime_providers(root, scope, wheels, lookup, reader)
    roots = runtime_provider_roots(root, providers, interpreter)
    context.verify_correspondence(context.reference, root, reader, deadline)
    return providers, roots


def _artifact_shape(value: object) -> None:
    if (
        not isinstance(value, dict)
        or set(value) != {"path", "sha256"}
        or not isinstance(value["path"], str)
        or not isinstance(value["sha256"], str)
        or re.fullmatch(r"[0-9a-f]{64}", value["sha256"]) is None
    ):
        raise ValueError("native source input requires a closed exact artifact binding")


def validate_joint_source_inputs(value: object) -> None:
    names = {
        "schema_version",
        "descriptor",
        "implementation",
        "providers",
        "provider_roots",
        "closure",
        "mermaid_runtime",
        "pdfium",
        "office_fonts",
    }
    if not isinstance(value, dict) or set(value) != names or value["schema_version"] != JOINT_SCHEMA:
        raise ValueError("native source launch requires the versioned closed joint input fields")
    from infrastructure.reporting.native_office_full_worker_context import validate_office_font_nomination_data

    validate_office_font_nomination_data(value["office_fonts"])
    pdfium = value["pdfium"]
    if (
        not isinstance(pdfium, dict)
        or pdfium.get("schema_version") != "template-full-worker-source-locked-pdfium-input-v1"
    ):
        raise ValueError("full native PDFium needs separately admitted Source-owned inputs")
    runtime = value["mermaid_runtime"]
    runtime_fields = {
        "schema_version",
        "package_root_path",
        "dependency_root_path",
        "node_executable_path",
        "chrome_executable_path",
        "runtime_content_digest",
    }
    from infrastructure.reporting.native_mermaid_runtime_selection import SELECTION_SCHEMA

    if (
        not isinstance(runtime, dict)
        or set(runtime) != runtime_fields
        or runtime["schema_version"] != SELECTION_SCHEMA
        or not isinstance(runtime["runtime_content_digest"], str)
        or re.fullmatch(r"[0-9a-f]{64}", runtime["runtime_content_digest"]) is None
    ):
        raise ValueError("native Source11 runtime requires exact Source-admitted nomination/digest DATA")
    for key in runtime_fields - {"schema_version", "runtime_content_digest"}:
        path = runtime[key]
        if (
            not isinstance(path, str)
            or not Path(path).is_absolute()
            or ".." in Path(path).parts
            or "\\" in path
            or "\0" in path
        ):
            raise ValueError("native Source11 runtime nomination label is invalid")
    for key in ("descriptor", "implementation"):
        _artifact_shape(value[key])
    if not isinstance(value["providers"], dict):
        raise ValueError("native installed providers must be a source-admitted mapping")
    for provider in value["providers"].values():
        if not isinstance(provider, dict) or set(provider) != {
            "package",
            "version",
            "wheel_artifact",
        }:
            raise ValueError("native provider declaration fields differ")
        if any(not isinstance(provider[key], str) or not provider[key] for key in ("package", "version")):
            raise ValueError("native provider package/version fields differ")
        _artifact_shape(provider["wheel_artifact"])
    roots = value["provider_roots"]
    if not isinstance(roots, list) or len(set(roots)) != len(roots):
        raise ValueError("native provider roots must be unique original path labels")
    for item in roots:
        if not isinstance(item, str) or not Path(item).is_absolute() or ".." in Path(item).parts:
            raise ValueError("native provider root label is invalid")
    closure = value["closure"]
    if not isinstance(closure, dict) or set(closure) != {"directory", "identity"}:
        raise ValueError("native closure requires its supervisor-bound directory and physical identity")
    if not isinstance(closure["directory"], str) or not Path(closure["directory"]).is_relative_to("output/readiness"):
        raise ValueError("native closure directory is outside readiness evidence")
    identity = closure["identity"]
    if (
        not isinstance(identity, list)
        or len(identity) != 2
        or any(type(item) is not int or item < 0 for item in identity)
    ):
        raise ValueError("native closure physical identity is invalid")


def bound_input(reader: SnapshotReader, binding: object) -> ArtifactSnapshot:
    _artifact_shape(binding)
    if not isinstance(binding, dict):
        raise ValueError("native source binding is not an object")
    snapshot = reader.read(binding["path"])
    if snapshot.sha256 != binding["sha256"]:
        raise ValueError("native source input differs from its admitted exact bytes")
    return snapshot


def source_environment(context: NativeSourceContext) -> dict[str, str]:
    reference = context.reference
    return {
        "TEMPLATE_PUBLIC_REFERENCE_ROOT": str(reference.root),
        "TEMPLATE_PUBLIC_REFERENCE_COMMIT": reference.commit,
        "TEMPLATE_PUBLIC_REFERENCE_FINGERPRINT": reference.source_identity,
    }


def worker_arguments(
    root: Path,
    spec: Path,
    spec_sha256: str,
    descriptor: ArtifactSnapshot,
    implementation: ArtifactSnapshot,
    closure: Path,
    closure_identity: tuple[int, int],
    current_root_identity: tuple[int, int],
    mermaid_runtime: Mapping[str, str],
    pdfium_provider: NativePDFiumProvider | NativeAuthenticatedOriginalPDFium,
    office_fonts: Mapping[str, Any],
) -> tuple[str, ...]:
    """Exact original input pins carried in the guardian-observed command."""
    return (
        "--root",
        str(root),
        "--spec",
        str(spec),
        "--spec-sha256",
        spec_sha256,
        "--source-descriptor",
        str(descriptor.path),
        "--source-descriptor-sha256",
        descriptor.sha256,
        "--implementation-input",
        str(implementation.path),
        "--implementation-sha256",
        implementation.sha256,
        "--audit-closure-directory",
        str(closure),
        "--audit-closure-identity",
        *map(str, closure_identity),
        "--current-root-identity",
        *map(str, current_root_identity),
        "--mermaid-package-root",
        mermaid_runtime["package_root_path"],
        "--mermaid-dependency-root",
        mermaid_runtime["dependency_root_path"],
        "--mermaid-node-executable",
        mermaid_runtime["node_executable_path"],
        "--mermaid-chrome-executable",
        mermaid_runtime["chrome_executable_path"],
        "--mermaid-runtime-digest",
        mermaid_runtime["runtime_content_digest"],
        *pdfium_worker_arguments(pdfium_provider),
        "--office-fonts-sha256",
        office_fonts["content_digest"],
        *(argument for row in office_fonts["files"] for argument in ("--office-font-file", row["path"])),
    )


def validate_original_joint_launch(
    specification: dict[str, Any],
    specification_file: ArtifactSnapshot,
    process_file: ArtifactSnapshot,
    closure_file: ArtifactSnapshot,
    reader: SnapshotReader,
    operation: NativeReaderOperation,
) -> tuple[list[str], dict[str, Any]]:
    """Reconstruct exact original argv from externally bound original facts."""
    remaining(operation.deadline)
    original = operation.originals.get(specification["scope"])
    if not isinstance(original, NativeOriginalLaunch):
        raise ProjectionSourceUnsupported("native replay lacks authenticated original supervisor launch bindings")
    if (
        original.scope != specification["scope"]
        or original.run_id != specification["run_id"]
        or original.specification_sha256 != specification_file.sha256
        or original.specification_relative != specification_file.relative
        or original.process_relative != process_file.relative
        or original.closure_relative != closure_file.relative
        or original.native_execution_relative != f"{specification['directory']}/native-execution.json"
        or original.process_sha256 != process_file.sha256
        or original.closure_sha256 != closure_file.sha256
    ):
        raise ValueError("native spec/process/closure differs from the original external launch custodian")
    process = process_file.json_object()
    if (
        original.original_deadline != specification["deadline_monotonic"]
        or type(original.observed_completion) is not float
        or not math.isfinite(original.observed_completion)
        or original.observed_completion >= original.original_deadline
        or process.get("completed_monotonic") != original.observed_completion
    ):
        raise ValueError("original native guardian completion exceeded or differs from its original operation deadline")
    inputs = specification["source_inputs"]
    validate_joint_source_inputs(inputs)
    descriptor = bound_input(reader, inputs["descriptor"])
    implementation = bound_input(reader, inputs["implementation"])
    if descriptor.sha256 != original.descriptor_sha256 or implementation.sha256 != original.implementation_sha256:
        raise ValueError("native source/SDK inputs differ from original external bindings")
    observation = validate_original_source_descriptor(
        descriptor.content,
        externally_bound_sha256=original.descriptor_sha256,
        run_id=original.run_id,
        scope=original.scope,
        deadline=operation.deadline,
    )
    reference = operation.source.reference
    observed_source = observation["original_source"]
    if (
        original.source_binding
        != (
            observed_source["root"],
            observed_source["commit"],
            observed_source["source_identity"],
        )
        or observed_source["commit"] != reference.commit
        or observed_source["source_identity"] != reference.source_identity
    ):
        raise ValueError("original native source binding differs from independently admitted current reference")
    root = Path(observation["current_mirror"]["root"])
    sdk = Path(observation["selected_sdk"]["package_root"])
    current = reader.root
    if observation["selected_sdk"]["implementation_sha256"] != implementation.sha256:
        raise ValueError("original descriptor and admitted selected SDK input differ")
    hook = source_file_bytes(operation.source.bindings.selected_sdk_package_root / "core/bytecode_audit.py")
    from infrastructure.reporting.native_authenticated_original_pdfium import NativeAuthenticatedOriginalPDFium

    if (
        not isinstance(original.pdfium_provider, (NativePDFiumProvider, NativeAuthenticatedOriginalPDFium))
        or original.pdfium_provider.held_inputs() != inputs["pdfium"]
    ):
        raise ValueError("native original lacks independently held prelaunch PDFium admission")
    args = worker_arguments(
        root,
        root / specification_file.relative,
        specification_file.sha256,
        ArtifactSnapshot(
            root / descriptor.relative,
            descriptor.relative,
            descriptor.content,
            descriptor.sha256,
            descriptor.identity,
        ),
        ArtifactSnapshot(
            root / implementation.relative,
            implementation.relative,
            implementation.content,
            implementation.sha256,
            implementation.identity,
        ),
        root / inputs["closure"]["directory"],
        _identity_pair(inputs["closure"]["identity"]),
        _identity_pair(observation["current_mirror"]["root_identity"]),
        inputs["mermaid_runtime"],
        original.pdfium_provider,
        inputs["office_fonts"],
    )
    runtime = process_file.json_object().get("selected_interpreter")
    if not isinstance(runtime, str) or not Path(runtime).is_absolute():
        raise ValueError("original native process lacks its exact selected launcher")
    command = [
        runtime,
        "-I",
        "-c",
        format_selected_sdk_native_bootstrap(
            hook,
            sdk,
            tuple(Path(item) for item in inputs["provider_roots"]),
            root / implementation.relative,
            implementation.sha256,
            root / inputs["closure"]["directory"],
            _identity_pair(inputs["closure"]["identity"]),
            specification["deadline_monotonic"],
        ),
        *args,
    ]
    if tuple(command) != original.command:
        raise ValueError("native original command differs from external guardian custody")
    from infrastructure.reporting.native_original_supervisor import validate_original_native_process

    validate_original_native_process(process, reader, original=original)
    operation.source.verify_correspondence(reference, current, reader, operation.deadline)
    return command, observation


def validate_retained_sdk_closure(
    closure: ArtifactSnapshot,
    specification: dict[str, Any],
    observation: dict[str, Any],
    reader: SnapshotReader,
    operation: NativeReaderOperation,
) -> None:
    """Read original retained bytes; never reopen original source/cache paths."""
    remaining(operation.deadline)
    held_directory = _anchored_directory_identity(closure.path.parent, operation.deadline)
    raw = closure.json_object()
    expected_fields = {
        "schema_version",
        "status",
        "worker_outcome",
        "native_os_exit_authority",
        "selected_sdk_package_root",
        "original_operation_deadline",
        "hook_sha256",
        "implementation_input",
        "executions",
        "errors",
        "prefix",
        "source_roots",
        "runtime",
        "raw_hook",
        "implementation_bytes",
        "retained_payload_bytes",
    }
    if (
        set(raw) != expected_fields
        or raw.get("schema_version") != CLOSURE_SCHEMA
        or raw.get("status") != "pass"
        or raw.get("errors") != []
        or raw.get("native_os_exit_authority") != "original external process guardian only"
    ):
        raise ValueError("native selected SDK closure is missing, incomplete or failed")
    original = operation.originals[specification["scope"]]
    original_process = reader.read(f"{specification['directory']}/process.json")
    if original_process.sha256 != original.process_sha256:
        raise ValueError("native closure worker result has a different original guardian record")
    native_exit = original_process.json_object().get("original_exit_code")
    if (
        type(native_exit) is not int
        or native_exit not in {0, 75}
        or raw.get("worker_outcome")
        != {
            "kind": "raised",
            "class": "SystemExit",
            "module": "builtins",
            "system_exit_code": native_exit,
        }
    ):
        raise ValueError("native retained SDK worker outcome differs from original observed OS exit")
    inputs = specification["source_inputs"]
    origin_root = Path(observation["current_mirror"]["root"])
    origin_sdk = Path(observation["selected_sdk"]["package_root"])
    prefix = raw.get("prefix")
    if (
        raw.get("selected_sdk_package_root") != str(origin_sdk)
        or raw.get("source_roots") != [str(origin_sdk), *inputs["provider_roots"]]
        or raw.get("original_operation_deadline") != specification["deadline_monotonic"]
        or not isinstance(prefix, str)
        or not Path(prefix).is_absolute()
    ):
        raise ValueError("native original executed closure selected different roots or operation")
    from infrastructure.reporting.native_code_runtime import validate_native_code_runtime

    runtime = validate_native_code_runtime(raw.get("runtime"))
    total_bytes = 0
    seen_payloads: set[str] = set()

    def payload(binding: object) -> bytes:
        nonlocal total_bytes
        remaining(operation.deadline)
        if not isinstance(binding, dict) or set(binding) != {"path", "sha256", "bytes"}:
            raise ValueError("native executed closure payload fields differ")
        name = binding["path"]
        if not isinstance(name, str) or re.fullmatch(r"payload-[0-9]{6}\.bin", name) is None or name in seen_payloads:
            raise ValueError("native executed closure payload is unsafe or repeated")
        seen_payloads.add(name)
        item = reader.read((closure.path.parent / name).relative_to(reader.root).as_posix())
        if (
            item.sha256 != binding["sha256"]
            or type(binding["bytes"]) is not int
            or len(item.content) != binding["bytes"]
        ):
            raise ValueError("native retained executed closure payload bytes differ")
        total_bytes += len(item.content)
        if total_bytes + len(closure.content) > MAX_CACHE_BYTES:
            raise ValueError("native retained closure exceeds the original aggregate byte ceiling")
        return item.content

    hook = payload(raw.get("raw_hook"))
    expected_hook = source_file_bytes(operation.source.bindings.selected_sdk_package_root / "core/bytecode_audit.py")
    implementation = bound_input(reader, inputs["implementation"])
    if hook != expected_hook or raw.get("hook_sha256") != hashlib.sha256(hook).hexdigest():
        raise ValueError("native original raw audit hook differs from admitted selected SDK")
    if payload(raw.get("implementation_bytes")) != implementation.content or raw.get("implementation_input") != {
        "path": str(origin_root / implementation.relative),
        "sha256": implementation.sha256,
    }:
        raise ValueError("native original SDK custody input payload differs")
    expected = operation.source.bindings.expected_implementation_bytes
    sdk_files = json_object_from_bytes(expected)["files"]
    expected_sources = {
        str(origin_sdk / key.removeprefix("infrastructure/")): digest
        for key, digest in sdk_files.items()
        if key.startswith("infrastructure/") and key.endswith(".py")
    }
    from infrastructure.project.installed_acceptance_artifacts import (
        inspect_wheel_bytes,
    )
    from infrastructure.reporting.release_readiness_profile import Requirement

    for scope, provider in inputs["providers"].items():
        wheel = bound_input(reader, provider["wheel_artifact"])
        requirement = Requirement(
            f"{scope}:installed",
            "installed",
            scope,
            provider["version"],
            "",
            "",
            package=provider["package"],
        )
        targets, members = inspect_wheel_bytes(reader.root, requirement, wheel.content, reader=reader)
        if len(targets) != 1:
            raise ValueError("native retained provider needs one genuine admitted namespace")
        for root in inputs["provider_roots"]:
            selected = Path(root)
            if selected.name == targets[0]:
                expected_sources.update(
                    {
                        str(selected / name.removeprefix(targets[0] + "/")): digest
                        for name, digest in members.items()
                        if name.startswith(targets[0] + "/") and name.endswith(".py")
                    }
                )
    current_pdfium = operation.pdfium_providers.get(specification["scope"])
    from infrastructure.reporting.native_authenticated_original_pdfium import NativeAuthenticatedOriginalPDFium

    if not isinstance(
        original.pdfium_provider, (NativePDFiumProvider, NativeAuthenticatedOriginalPDFium)
    ) or not isinstance(current_pdfium, NativePDFiumProvider):
        raise ValueError("native closure lacks actual external original and current PDFium provider capabilities")
    expected_sources.update(
        retained_pdfium_code_sources(
            original.pdfium_provider,
            current_pdfium,
            inputs["pdfium"],
            scope=specification["scope"],
            deadline=operation.deadline,
        )
    )
    required_pdfium_roots = list(map(str, original.pdfium_provider.audit_roots))
    if inputs["provider_roots"][-len(required_pdfium_roots) :] != required_pdfium_roots:
        raise ValueError("native original audit omitted independently admitted PDFium namespaces")
    executions = raw.get("executions")
    if not isinstance(executions, list) or not executions or len(executions) > MAX_EXECUTIONS:
        raise ValueError("native retained execution inventory is missing or excessive")
    seen_sources: set[str] = set()
    count = 0
    for row in executions:
        remaining(operation.deadline)
        if not isinstance(row, dict) or set(row) != {"source_path", "source", "runs"}:
            raise ValueError("native retained execution row fields differ")
        filename = row["source_path"]
        source = payload(row["source"])
        if (
            not isinstance(filename, str)
            or filename in seen_sources
            or expected_sources.get(filename) != hashlib.sha256(source).hexdigest()
        ):
            raise ValueError("native retained executed source differs from independently admitted SDK/provider bytes")
        seen_sources.add(filename)
        runs = row["runs"]
        if not isinstance(runs, list) or not runs:
            raise ValueError("native retained source has no actual code execution")
        expected_code = canonical_code(
            compile(source, filename, "exec", dont_inherit=True, optimize=sys.flags.optimize)
        )
        for run in runs:
            count += 1
            if count > MAX_EXECUTIONS or not isinstance(run, dict) or set(run) != {"executed_code", "cache"}:
                raise ValueError("native retained code execution fields or count differ")
            if payload(run["executed_code"]) != expected_code:
                raise ValueError("native actual executed code differs from admitted source compilation")
            cache = run["cache"]
            if cache is not None:
                if not isinstance(cache, dict) or set(cache) != {
                    "original_path",
                    "execution_sha256",
                    "bytes",
                }:
                    raise ValueError("native retained cache binding fields differ")
                cache_bytes = payload(cache["bytes"])
                if (
                    not Path(cache["original_path"]).is_absolute()
                    or ".." in Path(cache["original_path"]).parts
                    or not Path(cache["original_path"]).is_relative_to(prefix)
                    or len(cache_bytes) < 16
                    or cache_bytes[:4].hex() != runtime["magic_hex"]
                    or hashlib.sha256(cache_bytes).hexdigest() != cache["execution_sha256"]
                ):
                    raise ValueError("native retained cache differs from original prefix/execution-time bytes")
    if str(origin_sdk / "reporting/native_format_acceptance_worker.py") not in seen_sources:
        raise ValueError("native retained closure lacks actual selected worker execution")
    if raw.get("retained_payload_bytes") != total_bytes:
        raise ValueError("native retained closure aggregate payload count differs")
    expected_names = seen_payloads | {"receipt.json"}

    def verify_current_payload_directory() -> None:
        if _anchored_directory_identity(closure.path.parent, operation.deadline) != held_directory:
            raise ValueError("native current retained closure directory was physically replaced")
        actual_names: set[str] = set()
        with os.scandir(closure.path.parent) as entries:
            for entry in entries:
                remaining(operation.deadline)
                if entry.name not in expected_names or not entry.is_file(follow_symlinks=False):
                    raise ValueError("native retained closure has unexpected or nonregular payload membership")
                actual_names.add(entry.name)
                if len(actual_names) > len(expected_names):
                    raise ValueError("native retained closure exceeds its exact original payload entry bound")
        if actual_names != expected_names or not reader.unchanged():
            raise ValueError("native retained closure has missing or changed payloads")
        if _anchored_directory_identity(closure.path.parent, operation.deadline) != held_directory:
            raise ValueError("native retained closure directory changed during negative membership check")
        remaining(operation.deadline)

    verify_current_payload_directory()
    operation.verify(reader)
    # Source/Git closing calls may not mutate or physically replace evidence.
    verify_current_payload_directory()
