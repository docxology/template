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
from typing import Any, Protocol

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
        remaining(self.deadline)
        if (
            self.live_key is not _LIVE_ADMISSION
            or _runtime_seal(
                self.source,
                self.scope,
                self.site,
                self.wheel,
                self.members,
                self.wheel_observation,
                self.before,
                self.interpreter,
                self.owner_pid,
                self.prefix,
                self.deadline,
                self.image_before_import,
            )
            != self.seal
        ):
            raise ValueError("PDFium runtime admission is not the launcher's unchanged live capability")
        if os.getpid() != self.owner_pid:
            raise ValueError("PDFium live provider admission was moved to another original process")
        self.source.verify_correspondence(
            self.source.reference,
            self.source.bindings.current_root,
            self.source.current_source_reader,
            self.deadline,
        )
        raw, identity = _file(self.wheel, self.deadline)
        if _sha(raw) != self.wheel_observation["sha256"] or identity != self.wheel_observation["identity"]:
            raise ValueError("PDFium Source-nominated wheel identity changed")
        after = _installed(self.site, self.members, self.deadline)
        if after != self.before:
            raise ValueError("PDFium actual selected installed provider/DLL changed")
        for name in PROVIDERS:
            root = self.site / name
            verify_executed_source_code(root, self.prefix)
            for key, module in tuple(sys.modules.items()):
                if key == name or key.startswith(name + "."):
                    location = getattr(module, "__file__", None)
                    if not isinstance(location, str) or not Path(location).absolute().is_relative_to(root):
                        raise ValueError("PDFium actual loaded Python provider escaped its admitted package")
        if loaded is not None:
            label = loaded.relative_to(self.site).as_posix()
            if label not in self.before["files"] or loaded.suffix.lower() not in {
                ".dylib",
                ".dll",
                ".so",
            }:
                raise ValueError("PDFium actual selected loaded library is outside admitted wheel/RECORD")
            body, facts = _file(loaded, self.deadline)
            held = self.before["files"][label]
            if _sha(body) != held["sha256"] or facts != held["identity"]:
                raise ValueError("PDFium actual loaded library body/physical identity changed")
        executable = Path(sys.executable).resolve(strict=True)
        body, facts = _file(executable, self.deadline)
        if self.interpreter != {
            "path": str(executable),
            "sha256": _sha(body),
            "identity": facts,
        }:
            raise ValueError("PDFium enclosing selected original interpreter changed")
        self.source.verify_correspondence(
            self.source.reference,
            self.source.bindings.current_root,
            self.source.current_source_reader,
            self.deadline,
        )
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
