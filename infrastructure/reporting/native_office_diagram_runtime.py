"""Live Source-admitted PDFium provider and original inline-process observations.

Only a genuine source launcher calls the factory before either provider imports.
Portable readers authenticate retained events through an independently held
original launch; this module never constructs that authority from JSON.
"""

from __future__ import annotations

import os
import sys
import time
import types
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

from infrastructure.core.bytecode_audit import verify_executed_source_code
from infrastructure.project.public_acceptance_evidence import write_json
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_office_pdfium_provider import (
    PROVIDERS,
    _sha,
    _file,
    _wheel,
    _installed,
)
from infrastructure.reporting.native_office_pdfium_images import (
    _loaded_image as _loaded_image,
)
from infrastructure.reporting.native_source_external_admission import (
    NativeSourceContext,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

if TYPE_CHECKING:
    from infrastructure.reporting.native_full_worker_pdfium import NativePDFiumSelection


EVENT_SCHEMA = "template-office-original-inline-pdfium-event-v1"
_LIVE_ADMISSION = object()


def _runtime_seal(
    source: NativeSourceContext,
    scope: str,
    site: Path,
    wheel: Path,
    members: dict[str, bytes],
    wheel_observation: dict[str, Any],
    before: dict[str, Any],
    interpreter: dict[str, Any],
    owner_pid: int,
    prefix: Path,
    deadline: float,
    image_before_import: dict[str, Any],
) -> str:
    """Bind the already-observed live factory facts, including preimport absence."""
    return _sha(
        repr(
            (
                source.bindings.current_root,
                source.bindings.run_id,
                source.reference.commit,
                source.reference.source_identity,
                scope,
                site,
                wheel,
                members,
                wheel_observation,
                before,
                interpreter,
                owner_pid,
                prefix,
                deadline,
                image_before_import,
            )
        ).encode()
    )


class OriginalArtifactAuthenticator(Protocol):
    def __call__(
        self,
        binding: dict[str, Any],
        reader: SnapshotReader,
        *,
        run_id: str,
        required_sdk_modules: tuple[str, ...],
    ) -> dict[str, Any]: ...


@dataclass(frozen=True)
class PDFiumRuntimeAdmission:
    """Live Source/provider authority held by an original caller; never decoded."""

    source: NativeSourceContext
    scope: str
    site: Path
    wheel: Path
    members: dict[str, bytes]
    wheel_observation: dict[str, Any]
    before: dict[str, Any]
    owner_pid: int
    interpreter: dict[str, Any]
    prefix: Path
    deadline: float
    seal: str
    live_key: object
    authenticate_original: OriginalArtifactAuthenticator | None
    image_before_import: dict[str, Any]

    def verify(self, *, loaded: Path | None = None) -> dict[str, Any]:
        from infrastructure.reporting.native_pdfium_runtime_data import observe_runtime_data, validate_runtime_owner

        remaining(self.deadline)
        validate_runtime_owner(self)
        with self.source._correspondence_guard(
            self.source.reference,
            self.source.bindings.current_root,
            self.source.current_source_reader,
            self.deadline,
        ):
            after = observe_runtime_data(self, loaded=loaded)
        remaining(self.deadline)
        return after

    def event(
        self,
        root: Path,
        directory: Path,
        *,
        loaded: Path,
        inputs: dict[str, Any],
        outputs: dict[str, Any],
        image_before: dict[str, Any],
    ) -> dict[str, Any]:
        """Retain actual inline facts; outer supervisor supplies OS-exit authority."""
        after = self.verify(loaded=loaded)
        image_after = _loaded_image(loaded, self.deadline)
        if image_before != image_after:
            raise ValueError("PDFium selected original mapped image changed during actual paint")
        reference = self.source.reference
        value = {
            "schema_version": EVENT_SCHEMA,
            "run_id": self.source.bindings.run_id,
            "scope": self.scope,
            "owner_pid": self.owner_pid,
            "original_deadline_monotonic": self.deadline,
            "completed_monotonic": time.monotonic(),
            "interpreter_before": self.interpreter,
            "interpreter_after": self.interpreter,
            "source": {
                "commit": reference.commit,
                "source_identity": reference.source_identity,
            },
            "wheel": self.wheel_observation,
            "provider_before": self.before,
            "provider_after": after,
            "loaded_library": str(loaded),
            "mapped_image_before": image_before,
            "mapped_image_after": image_after,
            "mapped_image_before_import": self.image_before_import,
            "inputs": inputs,
            "outputs": outputs,
            "original_OS_exit_authority": "independently authenticated enclosing original supervisor",
        }
        binding = write_json(root, directory / "inline-pdfium-event.json", value)
        self.verify(loaded=loaded)
        remaining(self.deadline)
        return binding


def admit_pdfium_runtime(
    source: NativeSourceContext,
    *,
    scope: str,
    site: Path,
    wheel: Path,
    deadline: float,
    authenticate_original: OriginalArtifactAuthenticator | None = None,
) -> PDFiumRuntimeAdmission:
    """Genuine launcher factory: source-lock/wheel/RECORD and preimport audit."""
    remaining(deadline)
    if not isinstance(source, NativeSourceContext) or source.bindings.current_root != source.current_source_reader.root:
        raise ValueError("PDFium provider admission needs a genuine live original Source context")
    if authenticate_original is not None:
        from infrastructure.reporting.native_office_control_custody import (
            OfficeControlReaderOperation,
        )

        if (
            not isinstance(
                getattr(authenticate_original, "__self__", None),
                OfficeControlReaderOperation,
            )
            or getattr(authenticate_original, "__func__", None)
            is not OfficeControlReaderOperation.authenticate_artifact
        ):
            raise ValueError("PDFium original callback requires the genuine typed Office control custodian")
    from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

    if scope not in PUBLIC_PROJECT_NAMES:
        raise ValueError("PDFium provider admission requires the actual declared public Source scope")
    if any(name == package or name.startswith(package + ".") for name in sys.modules for package in PROVIDERS):
        raise ValueError("PDFium provider admission must precede its actual imports")
    prefix = source.fresh_pycache_prefix
    registry = getattr(sys, "_template_executed_bytecode_audit", None)
    if prefix is None or not isinstance(registry, types.MappingProxyType) or registry.get("prefix") != str(prefix):
        raise ValueError("PDFium original provider needs the launcher's real fresh preimport audit")
    site, wheel = site.absolute(), wheel.absolute()
    if any(
        not any((site / name).is_relative_to(Path(root)) for root in registry["source_roots"]) for name in PROVIDERS
    ):
        raise ValueError("PDFium selected providers were omitted from the original preimport audit roots")
    members, wheel_observation = _wheel(source, wheel, deadline)
    before = _installed(site, members, deadline)
    if before["selection"]["version"] != wheel_observation["version"]:
        raise ValueError("PDFium actually selected installed version differs from Source-nominated wheel")
    executable = Path(sys.executable).resolve(strict=True)
    body, identity = _file(executable, deadline)
    interpreter = {"path": str(executable), "sha256": _sha(body), "identity": identity}
    libraries = [
        site / name
        for name in members
        if name.startswith("pypdfium2_raw/") and Path(name).suffix.lower() in {".dylib", ".dll", ".so"}
    ]
    if len(libraries) != 1:
        raise ValueError("PDFium Source wheel has an ambiguous native library selection")
    image_before_import = _loaded_image(libraries[0], deadline, require=False)
    if image_before_import["images"]:
        raise ValueError("PDFium selected native library was loaded before genuine original provider admission")
    owner_pid = os.getpid()
    seal = _runtime_seal(
        source,
        scope,
        site,
        wheel,
        members,
        wheel_observation,
        before,
        interpreter,
        owner_pid,
        prefix,
        deadline,
        image_before_import,
    )
    result = PDFiumRuntimeAdmission(
        source,
        scope,
        site,
        wheel,
        members,
        wheel_observation,
        before,
        owner_pid,
        interpreter,
        prefix,
        deadline,
        seal,
        _LIVE_ADMISSION,
        authenticate_original,
        image_before_import,
    )
    result.verify()
    return result


def _pdfium_batch_runtime_observation(
    site: Path, members: dict[str, bytes], prefix: Path, deadline: float
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Observe local physical/audit DATA only; never mint a runtime capability."""
    installed = _installed(site, members, deadline)
    executable = Path(sys.executable).resolve(strict=True)
    body, identity = _file(executable, deadline)
    interpreter = {"path": str(executable), "sha256": _sha(body), "identity": identity}
    libraries = [
        site / name
        for name in members
        if name.startswith("pypdfium2_raw/") and Path(name).suffix.lower() in {".dylib", ".dll", ".so"}
    ]
    if len(libraries) != 1:
        raise ValueError("PDFium Source wheel has an ambiguous native library selection")
    image = _loaded_image(libraries[0], deadline, require=False)
    if image["images"]:
        raise ValueError("PDFium native library was loaded before batch provider admission")
    for name in PROVIDERS:
        verify_executed_source_code(site / name, prefix)
    return installed, interpreter, image


def admit_pdfium_runtimes(
    source: NativeSourceContext,
    selections: tuple[tuple[str, NativePDFiumSelection], ...],
    *,
    deadline: float,
) -> dict[str, PDFiumRuntimeAdmission]:
    """Hold actual preimport/audit facts for one fixed, wholly closed batch."""
    from infrastructure.reporting.native_pdfium_source_wheel import (
        _validate_pdfium_batch_inputs,
        inspect_pdfium_locked_wheel,
    )
    from infrastructure.reporting.native_preparation_progress import preparation_progress

    _validate_pdfium_batch_inputs(source, selections, deadline)
    owner_pid = os.getpid()
    if any(name == package or name.startswith(package + ".") for name in sys.modules for package in PROVIDERS):
        raise ValueError("PDFium runtime batch must precede actual namespace imports")
    prefix = source.fresh_pycache_prefix
    registry = getattr(sys, "_template_executed_bytecode_audit", None)
    if prefix is None or not isinstance(registry, types.MappingProxyType) or registry.get("prefix") != str(prefix):
        raise ValueError("PDFium batch needs the launcher's real fresh preimport audit")
    preparation_progress("pdfium-runtimes", "source-opening", deadline)
    # One lexical guard brackets this fixed synchronous DATA batch.
    # No result/capability escapes before its complete closing checks.
    with source._correspondence_guard(
        source.reference, source.bindings.current_root, source.current_source_reader, deadline
    ):
        lock = source.current_source_reader.read("uv.lock").content
        pending = []
        for scope, selection in selections:
            preparation_progress("pdfium-runtimes", "selection", deadline, scope)
            site, wheel = selection.site.absolute(), selection.wheel.absolute()
            if any(
                not any((site / name).is_relative_to(Path(root)) for root in registry["source_roots"])
                for name in PROVIDERS
            ):
                raise ValueError("PDFium batch providers are outside the original preimport audit roots")
            raw, identity = _file(wheel, deadline)
            members, declared = inspect_pdfium_locked_wheel(wheel.name, raw, lock, deadline=deadline)
            observation = {"path": str(wheel), **declared, "identity": identity}
            before, interpreter, image = _pdfium_batch_runtime_observation(site, members, prefix, deadline)
            if before["selection"]["version"] != observation["version"]:
                raise ValueError("PDFium selected installed version differs from Source-nominated wheel")
            pending.append((scope, site, wheel, members, observation, before, interpreter, image))
        for scope, site, wheel, members, observation, before, interpreter, image in pending:
            preparation_progress("pdfium-runtimes", "selection-closing", deadline, scope)
            raw, identity = _file(wheel, deadline)
            if (
                _sha(raw) != observation["sha256"]
                or identity != observation["identity"]
                or _pdfium_batch_runtime_observation(site, members, prefix, deadline) != (before, interpreter, image)
            ):
                raise ValueError("PDFium batch wheel/provider/interpreter/audit/image custody changed")
        if os.getpid() != owner_pid or any(
            name == package or name.startswith(package + ".") for name in sys.modules for package in PROVIDERS
        ):
            raise ValueError("PDFium batch lost its original PID or preimport namespace absence")
        preparation_progress("pdfium-runtimes", "source-closing", deadline)
    if os.getpid() != owner_pid or any(
        name == package or name.startswith(package + ".") for name in sys.modules for package in PROVIDERS
    ):
        raise ValueError("PDFium batch changed PID or namespace during final Source closing")
    remaining(deadline)
    result = {}
    for scope, site, wheel, members, observation, before, interpreter, image in pending:
        seal = _runtime_seal(
            source, scope, site, wheel, members, observation, before, interpreter, owner_pid, prefix, deadline, image
        )
        result[scope] = PDFiumRuntimeAdmission(
            source,
            scope,
            site,
            wheel,
            members,
            observation,
            before,
            owner_pid,
            interpreter,
            prefix,
            deadline,
            seal,
            _LIVE_ADMISSION,
            None,
            image,
        )
    preparation_progress("pdfium-runtimes", "completed", deadline)
    return result


def authenticate_original_pdfium_event(
    binding: dict[str, Any],
    reader: SnapshotReader,
    *,
    run_id: str,
    runtime: PDFiumRuntimeAdmission,
    required_sdk_modules: tuple[str, ...] = (
        "reporting/native_office_diagram_runtime.py",
        "reporting/native_office_diagram_pdfium.py",
    ),
) -> dict[str, Any]:
    """Preserve the public typed entry; portable readback lives in its own leaf."""
    from infrastructure.reporting.native_office_pdfium_event_replay import (
        authenticate_original_pdfium_event as admit_event,
    )

    return admit_event(
        binding,
        reader,
        run_id=run_id,
        runtime=runtime,
        required_sdk_modules=required_sdk_modules,
    )
