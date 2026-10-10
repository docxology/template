"""One fixed crossref SDK role; serialized records cannot select another role."""

from __future__ import annotations

from typing import Any

from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def validate_crossref_child_closure(
    source: NativeSourceContext,
    specification: dict[str, Any],
    binding: dict[str, str],
    reader: SnapshotReader,
    *,
    deadline: float,
) -> dict[str, Any]:
    from infrastructure.reporting.native_print_child_custody import _ControlRole, _closure

    role = _ControlRole(
        "template-source-owned-crossref-filter-v2",
        "infrastructure.reporting.native_crossref_worker",
        "crossref-filter",
        "",
        "",
        False,
        (
            "reporting/native_crossref_worker.py",
            "reporting/native_crossref_protocol.py",
            "reporting/native_crossref_filter.py",
            "reporting/native_crossref_exit.py",
            "reporting/native_crossref_exit_dispatch.py",
            "reporting/native_crossref_linux_exit.py",
            "reporting/native_crossref_linux_abi.py",
            "reporting/native_pdf_citation_runtime.py",
            "reporting/native_tool_process.py",
            "reporting/native_source_external_admission.py",
        ),
    )
    return _closure(source, specification, binding, reader, deadline=deadline, role=role)
