"""Source-owned PDFium preimport selection and held original/reader Code inputs.

A provider inventory is not native execution authority. Real inline execution
still requires the genuine installed/audited runtime and original supervisor.
No DATA decoder constructs the provider or runtime capabilities below.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import sys
import time
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Iterator

from infrastructure.project.public_reference_git import remaining
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.native_office_diagram_runtime import (
    PDFiumRuntimeAdmission,
    admit_pdfium_runtime,
)
from infrastructure.reporting.native_office_pdfium_provider import (
    PROVIDERS,
    _installed,
    _wheel,
)
from infrastructure.reporting.native_office_pdfium_images import _loaded_image
from infrastructure.reporting.native_format_acceptance_contracts import (
    create_private_native_directory,
)
from infrastructure.reporting.native_source_external_admission import (
    NativeSourceContext,
)

if TYPE_CHECKING:
    from infrastructure.reporting.native_authenticated_original_pdfium import (
        NativeAuthenticatedOriginalPDFium,
    )

SCHEMA = "template-full-worker-source-locked-pdfium-input-v1"
_KEY = object()
_CURRENT: ContextVar[PDFiumRuntimeAdmission | None] = ContextVar("template_full_worker_pdfium", default=None)


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


@dataclass(frozen=True)
class NativePDFiumSelection:
    """Independently nominated physical site/wheel, never receipt-discovered."""

    site: Path
    wheel: Path

    def __post_init__(self) -> None:
        if any(not isinstance(p, Path) or not p.is_absolute() or ".." in p.parts for p in (self.site, self.wheel)):
            raise ValueError("PDFium selection requires independently nominated absolute paths")


@dataclass(frozen=True)
class NativePDFiumProvider:
    """Preimport Source/wheel/RECORD authority; distinct from executed runtime."""

    source: NativeSourceContext
    scope: str
    selection: NativePDFiumSelection
    members: MappingProxyType[str, bytes]
    wheel: dict[str, Any]
    installed: dict[str, Any]
    seal: str
    observed_monotonic: float
    deadline: float
    _key: object

    def held_inputs(self) -> dict[str, Any]:
        value = {
            "schema_version": SCHEMA,
            "scope": self.scope,
            "site": str(self.selection.site),
            "wheel_path": str(self.selection.wheel),
            "wheel": self.wheel,
            "installed": self.installed,
            "source_commit": self.source.reference.commit,
            "source_identity": self.source.reference.source_identity,
            "member_hashes": {name: hashlib.sha256(raw).hexdigest() for name, raw in self.members.items()},
        }
        if self._key is not _KEY or _digest(value) != self.seal:
            raise ValueError("PDFium provider is not the unchanged externally held Source factory result")
        return value

    @property
    def audit_roots(self) -> tuple[Path, ...]:
        self.held_inputs()
        return tuple(self.selection.site / name for name in PROVIDERS)

    def verify_current(self, *, deadline: float) -> None:
        remaining(deadline)
        self.held_inputs()
        if deadline > self.deadline:
            raise ValueError("PDFium provider cannot renew its original caller clock")
        self.source.verify_correspondence(
            self.source.reference,
            self.source.bindings.current_root,
            self.source.current_source_reader,
            deadline,
        )
        members, wheel = _wheel(self.source, self.selection.wheel, deadline)
        if (
            dict(self.members) != members
            or self.wheel != wheel
            or self.installed != _installed(self.selection.site, members, deadline)
        ):
            raise ValueError("PDFium actual selected namespace/wheel/RECORD/physical closure changed")
        remaining(deadline)


def admit_full_worker_pdfium_provider(
    selection: NativePDFiumSelection,
    source: NativeSourceContext,
    *,
    scope: str,
    deadline: float,
) -> NativePDFiumProvider:
    """Real parent/current factory before either selected PDFium namespace import."""
    remaining(deadline)
    if (
        not isinstance(selection, NativePDFiumSelection)
        or not isinstance(source, NativeSourceContext)
        or scope not in PUBLIC_PROJECT_NAMES
    ):
        raise ValueError("full-worker PDFium requires typed independent nomination and genuine public Source")
    if any(name == package or name.startswith(package + ".") for name in sys.modules for package in PROVIDERS):
        raise ValueError("full-worker PDFium provider admission must precede actual namespace imports")
    members, wheel = _wheel(source, selection.wheel, deadline)
    installed = _installed(selection.site, members, deadline)
    if installed["selection"]["version"] != wheel["version"]:
        raise ValueError("actual selected installed PDFium version differs from the Source locked wheel")
    value = {
        "schema_version": SCHEMA,
        "scope": scope,
        "site": str(selection.site),
        "wheel_path": str(selection.wheel),
        "wheel": wheel,
        "installed": installed,
        "source_commit": source.reference.commit,
        "source_identity": source.reference.source_identity,
        "member_hashes": {name: hashlib.sha256(raw).hexdigest() for name, raw in members.items()},
    }
    result = NativePDFiumProvider(
        source,
        scope,
        selection,
        MappingProxyType(members),
        wheel,
        installed,
        _digest(value),
        time.monotonic(),
        deadline,
        _KEY,
    )
    result.verify_current(deadline=deadline)
    return result


def pdfium_worker_arguments(
    provider: NativePDFiumProvider | NativeAuthenticatedOriginalPDFium,
) -> tuple[str, ...]:
    """Carry independent nomination and exact Source body pins in actual argv."""
    value = provider.held_inputs()
    return (
        "--pdfium-site",
        value["site"],
        "--pdfium-wheel",
        value["wheel_path"],
        "--pdfium-wheel-sha256",
        value["wheel"]["sha256"],
        "--pdfium-input-sha256",
        _digest(value),
    )


def readmit_full_worker_pdfium_provider(
    selection: NativePDFiumSelection,
    source: NativeSourceContext,
    expected: object,
    *,
    scope: str,
    wheel_sha256: str,
    input_sha256: str,
    deadline: float,
) -> NativePDFiumProvider:
    """Child re-admits independent argv nominees; expected JSON grants no roots."""
    if not isinstance(expected, dict) or _digest(expected) != input_sha256:
        raise ValueError("PDFium spec differs from original command-pinned exact input bytes")
    current = admit_full_worker_pdfium_provider(selection, source, scope=scope, deadline=deadline)
    if current.held_inputs() != expected or current.wheel["sha256"] != wheel_sha256:
        raise ValueError("PDFium child actual provider differs from independently pinned original Source selection")
    return current


@dataclass
class NativePDFiumExecution:
    """Actual live invocation completion; JSON binding below is only evidence."""

    runtime: PDFiumRuntimeAdmission
    completed_binding: dict[str, Any] | None = None


@contextmanager
def full_worker_pdfium_execution(
    provider: NativePDFiumProvider,
    *,
    directory: Path,
    deadline: float,
    runtime_admission: PDFiumRuntimeAdmission | None = None,
) -> Iterator[NativePDFiumExecution]:
    """Activate actual SDK/provider audit, not inventory-based execution authority."""
    provider.verify_current(deadline=deadline)
    if runtime_admission is None:
        runtime = admit_pdfium_runtime(
            provider.source,
            scope=provider.scope,
            site=provider.selection.site,
            wheel=provider.selection.wheel,
            deadline=deadline,
        )
    else:
        runtime = runtime_admission
        if (
            not isinstance(runtime, PDFiumRuntimeAdmission)
            or runtime.source is not provider.source
            or runtime.scope != provider.scope
            or runtime.site != provider.selection.site
            or runtime.wheel != provider.selection.wheel
            or runtime.prefix != provider.source.fresh_pycache_prefix
            or runtime.owner_pid != os.getpid()
            or runtime.deadline != deadline
            or runtime.image_before_import.get("owner_pid") != os.getpid()
            or runtime.image_before_import.get("images") != []
        ):
            raise ValueError(
                "PDFium scope needs its exact genuine preimport Source/runtime admission and unchanged clock"
            )
        runtime.verify()
    # A held map admission was genuinely made before ANY PDFium namespace
    # import. Reusing it observes actual loaded Code/maps and each scope's body
    # before/after on the same caller clock; it never calls a post-import factory.
    # Genuine import/Code execution and OS image observation in this actual PID.
    importlib.import_module("pypdfium2")
    raw: Any = importlib.import_module("pypdfium2_raw.bindings")
    loaded = Path(raw._libs["pdfium"]._name).resolve(strict=True)
    runtime.verify(loaded=loaded)
    image_before = _loaded_image(loaded, deadline)
    origins: dict[str, str] = {}
    for name in PROVIDERS:
        location = getattr(sys.modules[name], "__file__", None)
        if not isinstance(location, str):
            raise ValueError("actual PDFium namespace has no independently admitted file origin")
        origins[name] = str(Path(location).absolute())
    root = provider.source.bindings.current_root
    create_private_native_directory(root, directory)
    execution = NativePDFiumExecution(runtime)
    token = _CURRENT.set(runtime)
    try:
        yield execution
        runtime.verify(loaded=loaded)
        provider.verify_current(deadline=deadline)
        execution.completed_binding = runtime.event(
            root,
            directory,
            loaded=loaded,
            inputs={"preimport_provider": provider.held_inputs()},
            outputs={"actual_provider_imports": origins},
            image_before=image_before,
        )
        remaining(deadline)
    finally:
        _CURRENT.reset(token)


def current_full_worker_pdfium_runtime() -> PDFiumRuntimeAdmission | None:
    """Return only the active actual typed execution factory, never DATA."""
    current = _CURRENT.get()
    if current is not None:
        current.verify()
    return current


def retained_pdfium_code_sources(
    original: NativePDFiumProvider | NativeAuthenticatedOriginalPDFium,
    current: NativePDFiumProvider,
    inputs: object,
    *,
    scope: str,
    deadline: float,
) -> dict[str, str]:
    """Extend full closure only with actual held original and current admissions.

    Original paths are compilation labels. This predicate opens no original
    producer DLL, source or cache, and grants no loaded library/kernel custody.
    The shared closure still checks each actual canonical Code/cache payload.
    """
    remaining(deadline)
    from infrastructure.reporting.native_authenticated_original_pdfium import (
        NativeAuthenticatedOriginalPDFium,
    )

    if not isinstance(original, (NativePDFiumProvider, NativeAuthenticatedOriginalPDFium)) or not isinstance(
        current, NativePDFiumProvider
    ):
        raise ValueError("PDFium original/reader require genuinely externally held typed provider admissions")
    previous, reader_inputs = original.held_inputs(), current.held_inputs()
    current.verify_current(deadline=deadline)
    if inputs != previous or scope != original.scope or scope != current.scope:
        raise ValueError("PDFium original spec differs from genuine prelaunch held provider")
    if (previous["source_commit"], previous["source_identity"]) != (
        reader_inputs["source_commit"],
        reader_inputs["source_identity"],
    ):
        raise ValueError("PDFium original and current Source identities differ")
    if (
        original.wheel["source_lock_sha256"] != current.wheel["source_lock_sha256"]
        or original.wheel["version"] != current.wheel["version"]
    ):
        raise ValueError("PDFium original and current selections differ from the same Source lock/version")
    # Each actual platform wheel is independently exact filename/hash/size
    # Source-listed. Retained original Code/cache is compiled from the original
    # authenticated wheel bytes below; fresh current execution is independently
    # audited against its current wheel. No original path or DLL is opened.
    # Shared closure canonical-Code/PYC comparison remains unchanged.
    remaining(deadline)
    return {
        str(original.selection.site / name): hashlib.sha256(raw).hexdigest()
        for name, raw in original.members.items()
        if name.endswith(".py")
    }


@contextmanager
def admitted_native_reader_pdfium(operation: Any, *, scope: str, directory: Path) -> Iterator[NativePDFiumExecution]:
    """Execute the independently selected reader provider under genuine Source.

    Caller bootstrap must already cover the selected namespace roots. Missing
    preimport coverage refuses before the native library import; no fallback.
    """
    from infrastructure.reporting.native_format_joint_source import (
        NativeReaderOperation,
    )
    from infrastructure.reporting.native_tool_producer import (
        current_native_producer_operation,
        native_producer_operation,
    )
    from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

    if not isinstance(operation, NativeReaderOperation):
        raise ValueError("PDFium reader requires actual external native operation")
    operation.verify(SnapshotReader(operation.source.bindings.current_root))
    provider = operation.pdfium_providers.get(scope)
    if not isinstance(provider, NativePDFiumProvider) or provider.source is not operation.source:
        raise ValueError("PDFium reader requires its independently selected current Source provider")
    admissions = getattr(operation, "pdfium_runtime_admissions", None)
    from collections.abc import Mapping

    if not isinstance(admissions, Mapping):
        raise ValueError("PDFium current reader requires its genuinely held whole-operation preimport runtime map")
    runtime = admissions.get(scope)
    if not isinstance(runtime, PDFiumRuntimeAdmission):
        raise ValueError("PDFium current reader scope lacks its actual preimport runtime capability")
    owner = current_native_producer_operation()
    if owner is not None:
        if owner.source is not operation.source:
            raise ValueError("PDFium reader has a different currently active Source owner")
        with full_worker_pdfium_execution(
            provider,
            directory=directory,
            deadline=operation.deadline,
            runtime_admission=runtime,
        ) as execution:
            yield execution
    else:
        with native_producer_operation(
            operation.source,
            run_id=operation.source.bindings.run_id,
            deadline=operation.deadline,
        ):
            with full_worker_pdfium_execution(
                provider,
                directory=directory,
                deadline=operation.deadline,
                runtime_admission=runtime,
            ) as execution:
                yield execution
    operation.verify(SnapshotReader(operation.source.bindings.current_root))
    remaining(operation.deadline)
