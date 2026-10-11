"""Portable inline PDFium DATA admission through actual external custody.

No receipt constructs the original process or independently selected current
runtime. This leaf opens no producer provider/library/source path.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_office_diagram_runtime import (
    EVENT_SCHEMA,
    PDFiumRuntimeAdmission,
)
from infrastructure.reporting.native_office_pdfium_provider import SCHEMA, _sha
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


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
    """Bind a retained inline event to actual external original process custody."""
    from infrastructure.reporting.native_tool_replay import (
        authenticate_original_native_artifact,
    )

    runtime.verify()
    admitted = (
        authenticate_original_native_artifact(binding, reader, run_id=run_id, required_sdk_modules=required_sdk_modules)
        if runtime.authenticate_original is None
        else runtime.authenticate_original(binding, reader, run_id=run_id, required_sdk_modules=required_sdk_modules)
    )
    event = reader.read(binding["path"]).json_object()
    process = admitted["process"]
    original = admitted["original"]
    if event.get("schema_version") != EVENT_SCHEMA or event.get("run_id") != run_id:
        raise ValueError("PDFium original inline event has a different schema/run")
    if type(event.get("owner_pid")) is not int or event["owner_pid"] != process["pid"]:
        raise ValueError("PDFium inline event differs from its actual enclosing original PID")
    if (
        event.get("original_deadline_monotonic") != original.original_deadline
        or type(event.get("completed_monotonic")) not in (int, float)
        or not math.isfinite(event["completed_monotonic"])
        or not event["completed_monotonic"] < original.observed_completion <= original.original_deadline
    ):
        raise ValueError("PDFium inline event does not precede genuine original supervisor completion")
    reference = admitted["operation"].source.reference
    if event.get("source") != {
        "commit": reference.commit,
        "source_identity": reference.source_identity,
    }:
        raise ValueError("PDFium inline event Source identity differs from actual admitted Source")
    if event.get("provider_before") != event.get("provider_after") or event.get("interpreter_before") != event.get(
        "interpreter_after"
    ):
        raise ValueError("PDFium inline original provider/interpreter custody changed")
    if (
        event.get("scope") != runtime.scope
        or event["wheel"].get("source_lock_sha256") != runtime.wheel_observation["source_lock_sha256"]
    ):
        raise ValueError("PDFium original provider differs from independently admitted Source platform wheel")
    # The actual external full-worker custodian may hold a Source-listed
    # original platform wheel distinct from the independently selected current
    # platform wheel. Office-control0/1 retains its existing direct same-wheel
    # predicate; no callback/receipt DATA creates original provider authority.
    from infrastructure.reporting.native_format_joint_source import NativeOriginalLaunch
    from infrastructure.reporting.native_full_worker_pdfium import NativePDFiumProvider
    from infrastructure.reporting.native_authenticated_original_pdfium import (
        NativeAuthenticatedOriginalPDFium,
    )

    original_provider = original.pdfium_provider if isinstance(original, NativeOriginalLaunch) else None
    original_members: Mapping[str, bytes]
    if isinstance(original, NativeOriginalLaunch):
        if not isinstance(original_provider, (NativePDFiumProvider, NativeAuthenticatedOriginalPDFium)):
            raise ValueError(
                "PDFium full-worker original provider is not the genuine independently held input capability"
            )
        held = original_provider.held_inputs()
        if held["source_commit"] != reference.commit or held["source_identity"] != reference.source_identity:
            raise ValueError("PDFium original provider differs from independently admitted current Source")
        original_wheel, original_members = (
            original_provider.wheel,
            original_provider.members,
        )
    else:
        original_wheel, original_members = runtime.wheel_observation, runtime.members
    before = event["provider_before"]
    if (
        event.get("wheel", {}).get("sha256") != original_wheel["sha256"]
        or original_wheel["source_lock_sha256"] != runtime.wheel_observation["source_lock_sha256"]
    ):
        raise ValueError("PDFium original event wheel differs from actual held Source-listed platform admission")
    if (
        before.get("schema_version") != SCHEMA
        or before.get("selection", {}).get("version") != runtime.wheel_observation["version"]
    ):
        raise ValueError("PDFium original installed provider version differs from current Source wheel")
    for label, content in original_members.items():
        if label.endswith(".dist-info/RECORD"):
            continue
        observed = before.get("files", {}).get(label)
        if (
            not isinstance(observed, dict)
            or observed.get("sha256") != _sha(content)
            or observed.get("bytes") != len(content)
        ):
            raise ValueError("PDFium original installed provider body differs from Source-declared wheel")
    image = event.get("mapped_image_before")
    if (
        not isinstance(image, dict)
        or image != event.get("mapped_image_after")
        or image.get("owner_pid") != process["pid"]
        or not image.get("images")
        or any(row.get("path") != event["loaded_library"] for row in image["images"])
    ):
        raise ValueError("PDFium original selected mapped image lacks unchanged actual enclosing PID custody")
    preimport = event.get("mapped_image_before_import")
    if (
        not isinstance(preimport, dict)
        or preimport.get("owner_pid") != process["pid"]
        or preimport.get("images") != []
        or preimport.get("platform") != image["platform"]
    ):
        raise ValueError("PDFium original selected native library lacks genuine preimport absence observation")
    runtime.verify()
    remaining(runtime.deadline)
    return event
