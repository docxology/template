"""Immutable Current execution nominations held by the actual native reader.

Paths nominate data; the genuine Source contexts, installed SDK and enclosing
reader's unchanged clock establish custody. This object contains no completed
execution, accepted status, or reusable gate result.
"""

from __future__ import annotations

import os
import stat
import types
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TYPE_CHECKING

from infrastructure.project.public_reference_git import remaining
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.native_source_external_admission import NativeSourceContext, _physical_directory
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

if TYPE_CHECKING:
    from infrastructure.reporting.native_full_worker_pdfium import NativePDFiumProvider
    from infrastructure.reporting.native_office_diagram_runtime import PDFiumRuntimeAdmission


@dataclass(frozen=True)
class NativeCurrentAnalysisInputs:
    """Already admitted distinct Current Source and its fixed per-scope data."""

    source: NativeSourceContext
    deadline: float
    scope_directories: Mapping[str, Path]
    provider_wheels: Mapping[str, Path]
    failure_observations: list[dict[str, Any]] = field(default_factory=list, kw_only=True, repr=False)
    domain_failure_observations: list[dict[str, Any]] = field(default_factory=list, kw_only=True, repr=False)
    pdfium_providers: Mapping[str, NativePDFiumProvider] | None = field(default=None, kw_only=True, repr=False)
    pdfium_runtimes: Mapping[str, PDFiumRuntimeAdmission] | None = field(default=None, kw_only=True, repr=False)
    office_font_files: tuple[Path, ...] | None = field(default=None, kw_only=True, repr=False)
    observer_tools: Mapping[str, Path | None] | None = field(default=None, kw_only=True, repr=False)
    _directory_identities: Mapping[str, tuple[int, int]] = field(init=False, repr=False)
    _wheel_reader: SnapshotReader = field(init=False, repr=False)

    def nominees(
        self, scope: str
    ) -> tuple[NativePDFiumProvider, PDFiumRuntimeAdmission, tuple[Path, ...], Mapping[str, Path | None]]:
        """Return held typed nominations only; no path/JSON creates an owner."""
        from infrastructure.reporting.native_full_worker_pdfium import NativePDFiumProvider
        from infrastructure.reporting.native_office_diagram_runtime import PDFiumRuntimeAdmission

        providers, runtimes, fonts, tools = (
            self.pdfium_providers,
            self.pdfium_runtimes,
            self.office_font_files,
            self.observer_tools,
        )
        if (
            not isinstance(providers, Mapping)
            or not isinstance(runtimes, Mapping)
            or set(providers) != set(self.scope_directories)
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
            or provider.source is not self.source
            or runtime.source is not self.source
            or provider.scope != scope
            or runtime.scope != scope
            or provider.deadline != self.deadline
            or runtime.deadline != self.deadline
            or runtime.site != provider.selection.site
            or runtime.wheel != provider.selection.wheel
            or any(not isinstance(path, Path) for path in fonts)
            or any(path is not None and not isinstance(path, Path) for path in tools.values())
        ):
            raise ValueError("Current typed runtime nominees differ from their actual Source/scope/clock")
        provider.verify_current(deadline=self.deadline)
        runtime.verify()
        return provider, runtime, fonts, tools

    def retain_failure(self, error: BaseException) -> None:
        """Keep actual failed execution DATA before profile error normalization."""
        packet = getattr(error, "native_current_pipeline", None)
        if isinstance(packet, dict):
            self.failure_observations.append(packet)
        domain = getattr(error, "native_project_domain_attempt", None)
        if isinstance(domain, dict):
            self.domain_failure_observations.append(
                {
                    "attempt": domain,
                    "controller_exit_code": getattr(
                        error, "native_project_domain_exit_code", getattr(error, "code", None)
                    ),
                }
            )

    def terminal_failure_exit(self) -> int | None:
        """A failure can stop later execution; it can never admit any gate."""
        codes = [packet.get("observation", {}).get("execution_exit_code") for packet in self.failure_observations]
        for failure in self.domain_failure_observations:
            packet = failure["attempt"]
            codes.append(packet.get("observation", {}).get("cell_exit_code"))
            codes.append(failure.get("controller_exit_code"))
            for tool in packet.get("native_tools", []):
                observed = tool.get("observation", {})
                if observed.get("original_exit_code") in (130, -2):
                    codes.append(130)
                if observed.get("timed_out") is True:
                    codes.append(124)
        return 130 if 130 in codes else 124 if 124 in codes else None

    def __post_init__(self) -> None:
        remaining(self.deadline)
        if not isinstance(self.source, NativeSourceContext):
            raise ValueError("Current nominations need the genuinely admitted Source context")
        directories = dict(self.scope_directories)
        wheels = dict(self.provider_wheels)
        if not directories or not set(directories).issubset(PUBLIC_PROJECT_NAMES):
            raise ValueError("Current nominations need exact public per-scope evidence directories")
        root = self.source.bindings.current_root
        expected_parent = root / "output/readiness" / f"native-current-{self.source.bindings.run_id}"
        identities = {}
        for scope, directory in directories.items():
            remaining(self.deadline)
            if not isinstance(directory, Path) or directory != expected_parent / scope:
                raise ValueError("Current scope nomination differs from its Source-owned exact path")
            identities[scope] = _physical_directory(directory)
            metadata = directory.lstat()
            if metadata.st_uid != os.getuid() or stat.S_IMODE(metadata.st_mode) != 0o700:
                raise ValueError("Current scope evidence directory must remain private and owned")
        wheel_reader = SnapshotReader(root)
        for provider, wheel in wheels.items():
            remaining(self.deadline)
            if provider not in PUBLIC_PROJECT_NAMES or not isinstance(wheel, Path) or not wheel.is_relative_to(root):
                raise ValueError("Current provider wheel nomination differs from its confined public scope")
            if wheel_reader.read(wheel.relative_to(root).as_posix()).path != wheel:
                raise ValueError("Current provider wheel nomination is not its exact confined path")
        object.__setattr__(self, "scope_directories", types.MappingProxyType(directories))
        object.__setattr__(self, "provider_wheels", types.MappingProxyType(wheels))
        object.__setattr__(self, "_directory_identities", types.MappingProxyType(identities))
        object.__setattr__(self, "_wheel_reader", wheel_reader)
        for name in ("pdfium_providers", "pdfium_runtimes", "observer_tools"):
            value = getattr(self, name)
            if isinstance(value, Mapping):
                object.__setattr__(self, name, types.MappingProxyType(dict(value)))

    def verify(self, original: NativeSourceContext, scopes: set[str], deadline: float) -> None:
        """Reobserve the entire genuine nomination set in this actual use window."""
        from infrastructure.reporting.native_current_nomination_batch import verify_current_nomination_batch

        verify_current_nomination_batch(self, original, frozenset(scopes), deadline=deadline)

    def verified_nominees(
        self, original: NativeSourceContext, scopes: set[str], scope: str, deadline: float
    ) -> tuple[NativePDFiumProvider, PDFiumRuntimeAdmission, tuple[Path, ...], Mapping[str, Path | None]]:
        """Close whole-map and later selected-member checks together, without caching GO."""
        from infrastructure.reporting.native_current_nomination_batch import verify_current_nomination_batch

        result = verify_current_nomination_batch(self, original, frozenset(scopes), deadline=deadline, selected=scope)
        if result is None:
            raise ValueError("Current selected nominee lacks its closed fixed-batch observation")
        return result
