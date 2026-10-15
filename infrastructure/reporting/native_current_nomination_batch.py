"""Revalidate the entire fixed Current nomination map in each actual use window."""

from __future__ import annotations

import os
import stat
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Any

from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_full_worker_pdfium import NativePDFiumProvider
from infrastructure.reporting.native_office_diagram_runtime import PDFiumRuntimeAdmission
from infrastructure.reporting.native_pdfium_revalidation import runtime_current_data, validate_runtime_selection
from infrastructure.reporting.native_pdfium_provider_data import observe_provider_files
from infrastructure.reporting.native_revalidation_progress import RevalidationProgress
from infrastructure.reporting.native_source_external_admission import NativeSourceContext, _physical_directory

if TYPE_CHECKING:
    from infrastructure.reporting.native_current_reader_inputs import NativeCurrentAnalysisInputs

Nominees = tuple[NativePDFiumProvider, PDFiumRuntimeAdmission, tuple[Path, ...], Mapping[str, Path | None]]


def _current_source(
    inputs: NativeCurrentAnalysisInputs, original: NativeSourceContext, scopes: frozenset[str], deadline: float
) -> None:
    from infrastructure.reporting.native_current_reader_inputs import NativeCurrentAnalysisInputs

    remaining(deadline)
    if (
        not isinstance(inputs, NativeCurrentAnalysisInputs)
        or not isinstance(original, NativeSourceContext)
        or not isinstance(inputs.source, NativeSourceContext)
        or not isinstance(scopes, frozenset)
        or deadline != inputs.deadline
        or set(inputs.scope_directories) != scopes
    ):
        raise ValueError("Current nomination differs from the actual reader's clock or full scope selection")
    current, prior = inputs.source.bindings, original.bindings
    if (
        current.current_root_identity == prior.current_root_identity
        or current.run_id == prior.run_id
        or current.expected_commit != prior.expected_commit
        or current.expected_source_identity != prior.expected_source_identity
        or current.selected_sdk_package_root != prior.selected_sdk_package_root
        or current.expected_implementation_bytes != prior.expected_implementation_bytes
        or inputs.source.reference.commit != original.reference.commit
        or inputs.source.reference.source_identity != original.reference.source_identity
    ):
        raise ValueError("Current Source requires distinct physical ownership and the identical admitted Source/SDK")
    for protected in (prior.current_root, original.reference.root, prior.selected_sdk_package_root):
        if current.current_root.is_relative_to(protected) or protected.is_relative_to(current.current_root):
            raise ValueError("Current Source physically overlaps the original reader, reference or installed SDK")


def _nominees(inputs: NativeCurrentAnalysisInputs, scope: str) -> Nominees:
    """Check the exact typed map/selection shape; no I/O or authority minted."""
    providers, runtimes, fonts, tools = (
        inputs.pdfium_providers,
        inputs.pdfium_runtimes,
        inputs.office_font_files,
        inputs.observer_tools,
    )
    if (
        not isinstance(providers, Mapping)
        or not isinstance(runtimes, Mapping)
        or set(providers) != set(inputs.scope_directories)
        or set(runtimes) != set(providers)
        or not isinstance(fonts, tuple)
        or not isinstance(tools, Mapping)
        or set(tools) != {"epubcheck_jar", "java_executable", "frozen_epub_engine"}
    ):
        raise ValueError("Current native inputs lack their complete preimport held typed nomination maps")
    provider, runtime = providers[scope], runtimes[scope]
    if (
        not isinstance(provider, NativePDFiumProvider)
        or not isinstance(runtime, PDFiumRuntimeAdmission)
        or provider.source is not inputs.source
        or runtime.source is not inputs.source
        or provider.scope != scope
        or runtime.scope != scope
        or provider.deadline != inputs.deadline
        or runtime.deadline != inputs.deadline
        or runtime.site != provider.selection.site
        or runtime.wheel != provider.selection.wheel
        or any(not isinstance(path, Path) for path in fonts)
        or any(path is not None and not isinstance(path, Path) for path in tools.values())
    ):
        raise ValueError("Current typed runtime nominees differ from their actual Source/scope/clock")
    provider.held_inputs()
    validate_runtime_selection(inputs.source, runtime, inputs.deadline)
    return provider, runtime, fonts, tools


def observe_provider_data(
    provider: NativePDFiumProvider, lock: bytes, *, deadline: float
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Compare exact current wheel/lock/member/installed DATA with held facts."""
    provider.held_inputs()
    if deadline != provider.deadline:
        raise ValueError("Current provider observation cannot replace its original clock")
    return observe_provider_files(
        provider.selection.site,
        provider.selection.wheel,
        provider.members,
        provider.wheel,
        provider.installed,
        lock,
        deadline=deadline,
    )


def _directory(inputs: NativeCurrentAnalysisInputs, scope: str) -> tuple[int, int]:
    directory = inputs.scope_directories[scope]
    identity = _physical_directory(directory)
    if identity != inputs._directory_identities[scope]:
        raise ValueError("Current scope evidence directory was replaced after actual nomination")
    metadata = directory.lstat()
    if metadata.st_uid != os.getuid() or stat.S_IMODE(metadata.st_mode) != 0o700:
        raise ValueError("Current scope evidence directory lost private ownership")
    return identity


def _observation(inputs: NativeCurrentAnalysisInputs, scope: str, lock: bytes) -> tuple[Any, ...]:
    provider, runtime, fonts, tools = _nominees(inputs, scope)
    return (
        id(provider),
        id(runtime),
        fonts,
        tuple(sorted(tools.items())),
        observe_provider_data(provider, lock, deadline=inputs.deadline),
        runtime_current_data(runtime),
        _directory(inputs, scope),
    )


def verify_current_nomination_batch(
    inputs: NativeCurrentAnalysisInputs,
    original: NativeSourceContext,
    scopes: frozenset[str],
    *,
    deadline: float,
    selected: str | None = None,
) -> Nominees | None:
    """Close all members, with selected observed last, before any nominee return."""
    _current_source(inputs, original, scopes, deadline)
    fixed = tuple(inputs.scope_directories)
    if selected is not None and selected not in scopes:
        raise ValueError("Current native acceptance scope is absent from the complete actual selection")
    for scope in fixed:
        _nominees(inputs, scope)
    progress = RevalidationProgress(inputs.source, "current-nominations", fixed, deadline)
    owner = os.getpid()
    try:
        progress.source_check("source-opening")
        lock = inputs.source.current_source_reader.read("uv.lock").content
        pending = {}
        for scope in fixed:
            progress.member("selection", scope)
            pending[scope] = _observation(inputs, scope, lock)
        if not inputs._wheel_reader.unchanged():
            raise ValueError("Current provider wheel bodies changed after actual nomination")
        progress.source_check("source-middle")
        for scope in fixed:
            progress.member("selection-closing", scope)
            if _observation(inputs, scope, lock) != pending[scope]:
                raise ValueError("Current runtime/provider/directory physical custody changed during fixed batch")
        if not inputs._wheel_reader.unchanged():
            raise ValueError("Current provider wheel bodies changed during batch closing")
        _current_source(inputs, original, scopes, deadline)
        if tuple(inputs.scope_directories) != fixed or os.getpid() != owner:
            raise ValueError("Current nomination selection/process changed during batch closing")
        for scope in fixed:
            provider, runtime, _, _ = _nominees(inputs, scope)
            if (id(provider), id(runtime)) != pending[scope][:2]:
                raise ValueError("Current held capability selection changed during batch closing")
            _directory(inputs, scope)
        if not inputs._wheel_reader.unchanged():
            raise ValueError("Current provider wheel bodies changed during batch closing")
        # The selected nominee used to follow whole-map verify. Keep its actual
        # local observation at a later point than every other closing member.
        if selected is not None:
            progress.member("selected-closing", selected)
            if _observation(inputs, selected, lock) != pending[selected]:
                raise ValueError("Current selected nominee changed after whole-map closing")
        # This is the ultimate Source closure: no local filesystem observation
        # follows it. Only in-memory selection/seal/PID and clock checks remain.
        progress.source_check("source-closing")
        _current_source(inputs, original, scopes, deadline)
        if tuple(inputs.scope_directories) != fixed or os.getpid() != owner:
            raise ValueError("Current nomination selection/process changed during final Source closing")
        for scope in fixed:
            provider, runtime, _, _ = _nominees(inputs, scope)
            if (id(provider), id(runtime)) != pending[scope][:2]:
                raise ValueError("Current held capability selection changed during final Source closing")
        remaining(deadline)
        result = None if selected is None else _nominees(inputs, selected)
        progress.emit("completed")
        return result
    except BaseException:
        progress.emit("failed")
        raise
