"""Closing custody checks after one native worker execution.

After the worker's own try/except, these checks close the outer custody: public
source digest, decoder library custody, installed providers, original Source
correspondence, host identity and interpreter identity. Failures are recorded
on the raw outcome; they never raise.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from infrastructure.project.public_acceptance_dependencies import capture_runtime_providers
from infrastructure.project.native_format_library_custody import (
    observe_native_library_custody,
    validate_native_library_custody,
)
from infrastructure.reporting.native_format_acceptance_contracts import public_source_digest
from infrastructure.reporting.native_format_portable_custody import executable_observation
from infrastructure.reporting.native_format_process_custody import native_host_observation
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

if TYPE_CHECKING:
    from infrastructure.reporting.native_source_external_admission import NativeSourceContext

__all__ = ["close_native_worker_custody"]


def close_native_worker_custody(
    raw: dict[str, Any],
    *,
    root: Path,
    before: str,
    formats: tuple[str, ...],
    directory: Path,
    specification: dict[str, Any],
    source_context: NativeSourceContext,
    native_reader: SnapshotReader,
    runtime: dict[str, str],
    deadline: float,
    host_before: dict[str, Any],
    interpreter_before: dict[str, Any],
) -> None:
    """Close every outer custody check and record any failure on ``raw``."""
    try:
        raw["source_digest_after"] = public_source_digest(root)
    except (OSError, ValueError) as error:
        raw["source_digest_after"] = ""
        raw["diagnostic"] = f"public source custody unavailable after native execution: {error}"
    if raw["source_digest_after"] != before:
        raw["status"], raw["execution_exit_code"], raw["diagnostic"] = (
            "fail",
            raw["execution_exit_code"] if raw["execution_exit_code"] in {130, 124} else 1,
            raw["diagnostic"] or "public source changed during native execution",
        )
    if raw["library_custody_before"]:
        try:
            raw["library_custody_after"] = observe_native_library_custody(formats, repo_root=root)
            validate_native_library_custody(
                raw["library_custody_before"],
                raw["library_custody_after"],
                formats=formats,
                reader=SnapshotReader(root),
                runtime=runtime,
            )
        except (OSError, ValueError) as error:
            raw["status"] = "fail"
            raw["execution_exit_code"] = raw["execution_exit_code"] if raw["execution_exit_code"] in {124, 130} else 1
            raw["diagnostic"] = f"native decoder custody unavailable or changed: {error}"
    try:
        provider_after, _ = capture_runtime_providers(
            root,
            specification["source_inputs"]["providers"],
            directory / "providers",
            retain_metadata=False,
        )
        raw["runtime_providers"]["after"] = provider_after
        if provider_after != raw["runtime_providers"]["before"]:
            raise ValueError("native installed providers changed during execution")
        source_context.verify_correspondence(
            source_context.reference,
            root,
            native_reader,
            deadline,
        )
    except (OSError, ValueError, RuntimeError) as error:
        raw["status"] = "fail"
        raw["execution_exit_code"] = raw["execution_exit_code"] if raw["execution_exit_code"] in {124, 130} else 1
        raw["diagnostic"] = f"native original source/provider closing custody failed: {error}"
    raw["host_after"] = native_host_observation()
    if raw["host_after"] != host_before:
        raw["status"] = "fail"
        raw["execution_exit_code"] = raw["execution_exit_code"] if raw["execution_exit_code"] in {124, 130} else 1
        raw["diagnostic"] = "native worker host changed during execution"
    raw["interpreter_observation_after"] = executable_observation(Path(sys.executable))
    if raw["interpreter_observation_after"] != interpreter_before:
        raw["status"] = "fail"
        raw["execution_exit_code"] = raw["execution_exit_code"] if raw["execution_exit_code"] in {124, 130} else 1
        raw["diagnostic"] = "native interpreter changed during execution"
