"""Compose original native launches only from the genuine hosted collector.

The collector is an actual authenticated API/download owner, held by the fresh
installed reader. Producer JSON is interpreted only inside this typed boundary,
then Source/SDK/executed-Code/process predicates independently check its bytes.
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from dataclasses import fields
from typing import Any

from infrastructure.project.public_reference_git import remaining
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.native_authenticated_original_pdfium import admit_authenticated_original_pdfium
from infrastructure.reporting.native_format_joint_source import (
    NativeOriginalLaunch,
    NativeReaderOperation,
    validate_original_joint_launch,
    validate_retained_sdk_closure,
)
from infrastructure.reporting.native_full_worker_pdfium import NativePDFiumProvider
from infrastructure.reporting.native_hosted_original_custody import NativeHostedArtifactCustodian, _hash, _path
from infrastructure.reporting.native_hosted_original_producer import _mutable_output
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader


def admit_authenticated_native_originals(
    custodian: NativeHostedArtifactCustodian,
    source: NativeSourceContext,
    *,
    current_pdfium_providers: Mapping[str, NativePDFiumProvider],
    deadline: float,
) -> dict[str, NativeOriginalLaunch]:
    """Validate exact original membership under the held current Source/clock.

    This factory has no retained-JSON-only entry. Every original is supplied by
    the authenticated Source workflow and exact artifact hashes, while current
    PDFium and SDK are independently admitted installed providers. Original and
    current native platform wheels remain distinct Source-listed selections.
    """
    remaining(deadline)
    if (
        not isinstance(custodian, NativeHostedArtifactCustodian)
        or not isinstance(source, NativeSourceContext)
        or deadline != custodian.deadline
        or set(current_pdfium_providers) != set(PUBLIC_PROJECT_NAMES)
    ):
        raise ValueError(
            "native original admission requires its real collector, installed providers and same reader clock"
        )
    originals: dict[str, NativeOriginalLaunch] = {}
    expected_fields = {field.name for field in fields(NativeOriginalLaunch)} - {"pdfium_provider"}
    for scope in PUBLIC_PROJECT_NAMES:
        custodian.verify_source(source, scope=scope)
        data = custodian.original_launch_data(scope)
        if set(data) != expected_fields or data["scope"] != scope:
            raise ValueError("authenticated original launch has a different closed Source-owned field set/scope")
        if not isinstance(data["run_id"], str) or re.fullmatch(r"[0-9a-f]{32}", data["run_id"]) is None:
            raise ValueError("authenticated native original run identity is invalid")
        for name in expected_fields:
            if name.endswith("sha256"):
                _hash(data[name])
            elif name.endswith("relative"):
                _path(data[name])
        command = data["command"]
        if not isinstance(command, list) or not command or any(not isinstance(arg, str) for arg in command):
            raise ValueError("authenticated native original command is invalid")
        for name in ("original_deadline", "observed_completion"):
            if type(data[name]) is not float or not math.isfinite(data[name]) or data[name] <= 0:
                raise ValueError("authenticated native original clock observation is invalid")
        if data["observed_completion"] >= data["original_deadline"]:
            raise ValueError("authenticated native original exhausted its actual original operation clock")
        binding = custodian.original_source_binding(scope)
        current_provider = current_pdfium_providers[scope]
        if not isinstance(current_provider, NativePDFiumProvider) or current_provider.source is not source:
            raise ValueError("native fresh reader provider was not independently admitted under the current Source")
        current_provider.verify_current(deadline=deadline)
        original_provider = admit_authenticated_original_pdfium(custodian, source, scope=scope, deadline=deadline)
        converted: dict[str, Any] = dict(data)
        converted["command"] = tuple(command)
        converted["source_binding"] = binding
        converted["pdfium_provider"] = original_provider
        original = NativeOriginalLaunch(**converted)
        reader = SnapshotReader(source.bindings.current_root)

        def artifact(path: str, digest: str) -> ArtifactSnapshot:
            raw = custodian.read_original_file(scope, {"path": path, "sha256": digest})
            snapshot = reader.read(path)
            if snapshot.content != raw or snapshot.sha256 != digest:
                raise ValueError("authenticated original artifact differs from exact retrieved bytes")
            return snapshot

        specification = artifact(original.specification_relative, original.specification_sha256)
        process = artifact(original.process_relative, original.process_sha256)
        closure = artifact(original.closure_relative, original.closure_sha256)
        native = artifact(original.native_execution_relative, original.native_execution_sha256)
        if native.json_object().get("execution_exit_code") != process.json_object().get("original_exit_code"):
            raise ValueError("authenticated original execution data differs from its independently retained OS result")
        operation = NativeReaderOperation(source, deadline, {scope: original}, {scope: current_provider})
        reader.native_operation = operation
        _, descriptor = validate_original_joint_launch(
            specification.json_object(), specification, process, closure, reader, operation
        )
        validate_retained_sdk_closure(closure, specification.json_object(), descriptor, reader, operation)
        # All original mutable payloads actually consumed by the validators must
        # be members of the exact retrieved producer graph, not local substitutes.
        for snapshot in tuple(reader.snapshots.values()):
            if _mutable_output(snapshot.relative):
                custodian.read_original_file(
                    scope, {"path": snapshot.relative, "sha256": snapshot.sha256, "bytes": len(snapshot.content)}
                )
        if not reader.unchanged():
            raise ValueError("authenticated original Source/Code/process graph changed during independent admission")
        custodian.verify_source(source, scope=scope)
        originals[scope] = original
    remaining(deadline)
    return originals
