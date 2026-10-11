"""Authenticate the actual full-worker PDFium namespace/Code/image event.

Original provider labels are never opened. The exact frozen Source wheel and
Code closure come from actual held original and independently selected reader
capabilities; the event's PID/exit/streams come from the original custodian.
Mapped-image facts grant no OS/shared-cache/kernel or library-memory authority.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_format_joint_source import (
    NativeOriginalLaunch,
    require_native_operation,
)
from infrastructure.reporting.native_full_worker_pdfium import (
    NativePDFiumProvider,
    retained_pdfium_code_sources,
)
from infrastructure.reporting.native_office_diagram_runtime import (
    PDFiumRuntimeAdmission,
    authenticate_original_pdfium_event,
)
from infrastructure.reporting.native_office_pdfium_provider import PROVIDERS
from infrastructure.reporting.native_tool_replay import (
    authenticate_original_native_artifact,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

REQUIRED_SDK = (
    "reporting/native_full_worker_pdfium.py",
    "reporting/native_office_diagram_runtime.py",
)


def validate_full_worker_pdfium_event(
    binding: object,
    reader: SnapshotReader,
    *,
    run_id: str,
    runtime: PDFiumRuntimeAdmission,
) -> dict[str, Any]:
    """Require genuine original native namespace execution before Office replay."""
    operation = require_native_operation(reader)
    if not isinstance(binding, dict) or set(binding) != {"path", "sha256"}:
        raise ValueError("full-worker PDFium execution requires its exact original event binding")
    if (
        not isinstance(runtime, PDFiumRuntimeAdmission)
        or runtime.source is not operation.source
        or runtime.deadline != operation.deadline
    ):
        raise ValueError("full-worker PDFium reader runtime belongs to another genuine Source/clock")
    authority = authenticate_original_native_artifact(binding, reader, run_id=run_id, required_sdk_modules=REQUIRED_SDK)
    original = authority["original"]
    if not isinstance(original, NativeOriginalLaunch) or authority["operation"] is not operation:
        raise ValueError("full-worker PDFium event requires the genuine separate full native-worker custodian")
    provider = original.pdfium_provider
    current = operation.pdfium_providers.get(original.scope)
    from infrastructure.reporting.native_authenticated_original_pdfium import (
        NativeAuthenticatedOriginalPDFium,
    )

    if not isinstance(provider, (NativePDFiumProvider, NativeAuthenticatedOriginalPDFium)) or not isinstance(
        current, NativePDFiumProvider
    ):
        raise ValueError("full-worker PDFium original and reader lack actual independently held provider capabilities")
    original_spec = reader.read(original.specification_relative).json_object()
    inputs = original_spec["source_inputs"]["pdfium"]
    retained_pdfium_code_sources(provider, current, inputs, scope=original.scope, deadline=operation.deadline)
    event = authenticate_original_pdfium_event(
        binding,
        reader,
        run_id=run_id,
        runtime=runtime,
        required_sdk_modules=REQUIRED_SDK,
    )
    if event["inputs"] != {"preimport_provider": provider.held_inputs()}:
        raise ValueError("full-worker PDFium event differs from actual original preimport Source admission")
    if event["provider_before"] != provider.installed or event["wheel"] != provider.wheel:
        raise ValueError(
            "full-worker PDFium enclosing event provider differs from genuine original body/physical custody"
        )
    expected_origins = {name: str(provider.selection.site / name / "__init__.py") for name in PROVIDERS}
    if event["outputs"] != {"actual_provider_imports": expected_origins}:
        raise ValueError(
            "full-worker PDFium actual namespace origin differs from independently admitted original paths"
        )
    expected_code = {
        *expected_origins.values(),
        str(provider.selection.site / "pypdfium2_raw" / "bindings.py"),
    }
    executions = authority["closure"]["executions"]
    if not expected_code <= {row["source_path"] for row in executions if row["runs"]}:
        raise ValueError(
            "full-worker PDFium top event lacks actual audited Code execution for both namespaces and bindings"
        )
    libraries = [
        name
        for name in provider.members
        if name.startswith("pypdfium2_raw/") and Path(name).suffix.lower() in {".dylib", ".dll", ".so"}
    ]
    if len(libraries) != 1 or event["loaded_library"] != str(provider.selection.site / libraries[0]):
        raise ValueError("full-worker PDFium mapped library differs from actual Source wheel nominee")
    physical = provider.installed["files"][libraries[0]]["identity"]
    image = event["mapped_image_before"]
    if image["platform"] == "darwin":
        if len(image["images"]) != 1 or any(
            set(row) != {"path", "header_address"}
            or type(row["header_address"]) is not int
            or row["header_address"] <= 0
            for row in image["images"]
        ):
            raise ValueError("full-worker original PDFium lacks exact actual Darwin image-header observation")
    elif image["platform"].startswith("linux"):
        for row in image["images"]:
            if (
                set(row) != {"range", "permissions", "offset", "path", "device", "inode"}
                or row["device"] != physical["device"]
                or row["inode"] != physical["inode"]
                or not isinstance(row["range"], str)
                or re.fullmatch(r"[0-9a-f]+-[0-9a-f]+", row["range"]) is None
                or not isinstance(row["permissions"], str)
                or re.fullmatch(r"[r-][w-][x-][ps]", row["permissions"]) is None
                or not isinstance(row["offset"], str)
                or re.fullmatch(r"[0-9a-f]+", row["offset"]) is None
            ):
                raise ValueError("full-worker original PDFium lacks physical OS mapping closure")
            start, end = (int(part, 16) for part in row["range"].split("-"))
            if start <= 0 or end <= start:
                raise ValueError("full-worker original PDFium mapping range is invalid")
    else:
        raise ValueError("full-worker original PDFium selected-image platform is unsupported")
    runtime.verify()
    operation.verify(reader)
    remaining(operation.deadline)
    return event
