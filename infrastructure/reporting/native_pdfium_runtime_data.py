"""Physical runtime observations from genuine held capabilities; DATA only.

These helpers never admit Source, mint a runtime, skip an outer guard or confer
successful execution. Fixed public callers always close their own Source window.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from infrastructure.core.bytecode_audit import verify_executed_source_code
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_office_pdfium_provider import PROVIDERS, _file, _installed, _sha

if TYPE_CHECKING:
    from infrastructure.reporting.native_office_diagram_runtime import PDFiumRuntimeAdmission


def validate_runtime_owner(runtime: PDFiumRuntimeAdmission) -> None:
    """Refuse unissued, changed or foreign-PID observations before any I/O."""
    from infrastructure.reporting.native_office_diagram_runtime import (
        PDFiumRuntimeAdmission,
        _LIVE_ADMISSION,
        _runtime_seal,
    )

    if not isinstance(runtime, PDFiumRuntimeAdmission):
        raise ValueError("PDFium local observation requires a genuine typed runtime")
    remaining(runtime.deadline)
    if (
        runtime.live_key is not _LIVE_ADMISSION
        or _runtime_seal(
            runtime.source,
            runtime.scope,
            runtime.site,
            runtime.wheel,
            runtime.members,
            runtime.wheel_observation,
            runtime.before,
            runtime.interpreter,
            runtime.owner_pid,
            runtime.prefix,
            runtime.deadline,
            runtime.image_before_import,
        )
        != runtime.seal
    ):
        raise ValueError("PDFium runtime admission is not the launcher's unchanged live capability")
    if os.getpid() != runtime.owner_pid:
        raise ValueError("PDFium live provider admission was moved to another original process")


def observe_runtime_data(runtime: PDFiumRuntimeAdmission, *, loaded: Path | None = None) -> dict[str, Any]:
    """Repeat the unchanged actual wheel/site/code/interpreter body, no Source role."""
    validate_runtime_owner(runtime)
    raw, identity = _file(runtime.wheel, runtime.deadline)
    if _sha(raw) != runtime.wheel_observation["sha256"] or identity != runtime.wheel_observation["identity"]:
        raise ValueError("PDFium Source-nominated wheel identity changed")
    after = _installed(runtime.site, runtime.members, runtime.deadline)
    if after != runtime.before:
        raise ValueError("PDFium actual selected installed provider/DLL changed")
    for name in PROVIDERS:
        root = runtime.site / name
        verify_executed_source_code(root, runtime.prefix)
        for key, module in tuple(sys.modules.items()):
            if key == name or key.startswith(name + "."):
                location = getattr(module, "__file__", None)
                if not isinstance(location, str) or not Path(location).absolute().is_relative_to(root):
                    raise ValueError("PDFium actual loaded Python provider escaped its admitted package")
    if loaded is not None:
        label = loaded.relative_to(runtime.site).as_posix()
        if label not in runtime.before["files"] or loaded.suffix.lower() not in {
            ".dylib",
            ".dll",
            ".so",
        }:
            raise ValueError("PDFium actual selected loaded library is outside admitted wheel/RECORD")
        body, facts = _file(loaded, runtime.deadline)
        held = runtime.before["files"][label]
        if _sha(body) != held["sha256"] or facts != held["identity"]:
            raise ValueError("PDFium actual loaded library body/physical identity changed")
    executable = Path(sys.executable).resolve(strict=True)
    body, facts = _file(executable, runtime.deadline)
    if runtime.interpreter != {
        "path": str(executable),
        "sha256": _sha(body),
        "identity": facts,
    }:
        raise ValueError("PDFium enclosing selected original interpreter changed")
    remaining(runtime.deadline)
    return after
