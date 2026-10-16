"""Fixed runtime revalidation preserving every caller's live Source window."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from infrastructure.project.public_reference_git import remaining
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.native_office_diagram_runtime import PDFiumRuntimeAdmission
from infrastructure.reporting.native_office_pdfium_images import _loaded_image
from infrastructure.reporting.native_pdfium_runtime_data import observe_runtime_data, validate_runtime_owner
from infrastructure.reporting.native_revalidation_progress import RevalidationProgress
from infrastructure.reporting.native_source_external_admission import NativeSourceContext


def runtime_current_data(runtime: PDFiumRuntimeAdmission) -> tuple[dict[str, Any], dict[str, Any]]:
    """Observe actual physical/code/mapped-image DATA; never return authority."""
    observed = observe_runtime_data(runtime)
    libraries = tuple(
        runtime.site / name
        for name in runtime.members
        if name.startswith("pypdfium2_raw/") and Path(name).suffix.lower() in {".dylib", ".dll", ".so"}
    )
    if len(libraries) != 1:
        raise ValueError("PDFium revalidation requires its one held native library")
    return observed, _loaded_image(libraries[0], runtime.deadline, require=False)


def validate_runtime_selection(source: NativeSourceContext, runtime: PDFiumRuntimeAdmission, deadline: float) -> None:
    """Check genuine existing seals and owner; this does not validate disk state."""
    if not isinstance(source, NativeSourceContext) or not isinstance(runtime, PDFiumRuntimeAdmission):
        raise ValueError("PDFium revalidation requires genuine Source/runtime capabilities")
    validate_runtime_owner(runtime)
    if runtime.source is not source or runtime.scope not in PUBLIC_PROJECT_NAMES or runtime.deadline != deadline:
        raise ValueError("PDFium revalidation differs from the exact Source/scope/original clock")


def validate_reader_runtime_binding(
    source: NativeSourceContext, provider: object, runtime: object, *, scope: str, deadline: float
) -> None:
    """Preserve the constructor's exact typed per-scope provider/runtime binding."""
    from infrastructure.reporting.native_full_worker_pdfium import NativePDFiumProvider

    if (
        not isinstance(runtime, PDFiumRuntimeAdmission)
        or not isinstance(provider, NativePDFiumProvider)
        or runtime.source is not source
        or runtime.scope != scope
        or runtime.site != provider.selection.site
        or runtime.wheel != provider.selection.wheel
        or runtime.owner_pid != os.getpid()
        or runtime.deadline != deadline
    ):
        raise ValueError("native reader needs its actual per-scope preimport PDFium runtime owner")


def verify_reader_runtime_batch(
    source: NativeSourceContext, runtimes: tuple[PDFiumRuntimeAdmission, ...], *, deadline: float
) -> None:
    """Recheck every existing runtime twice; never skip or renew a later-use guard."""
    if not isinstance(runtimes, tuple) or not runtimes:
        raise ValueError("reader runtime revalidation requires a nonempty fixed tuple")
    for runtime in runtimes:
        validate_runtime_selection(source, runtime, deadline)
    scopes = tuple(runtime.scope for runtime in runtimes)
    observation = RevalidationProgress(source, "reader-runtimes", scopes, deadline)
    owner = os.getpid()
    try:
        observation.source_check("source-opening")
        pending = []
        for runtime in runtimes:
            observation.member("selection", runtime.scope)
            pending.append(runtime_current_data(runtime))
        observation.source_check("source-middle")
        for runtime, before in zip(runtimes, pending, strict=True):
            observation.member("selection-closing", runtime.scope)
            validate_runtime_selection(source, runtime, deadline)
            if runtime_current_data(runtime) != before:
                raise ValueError("PDFium reader runtime physical/audit/image custody changed during batch")
        observation.source_check("source-closing")
        for runtime in runtimes:
            validate_runtime_selection(source, runtime, deadline)
        if os.getpid() != owner:
            raise ValueError("reader runtime revalidation lost its actual process owner")
        remaining(deadline)
        observation.emit("completed")
    except BaseException:
        observation.emit("failed")
        raise
