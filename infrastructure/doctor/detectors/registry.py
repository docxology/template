"""Detector registry and runner."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from infrastructure.doctor.detectors.hygiene import (
    detect_orphan_output_dirs,
    detect_pycache_clutter,
    detect_stale_coverage_files,
)
from infrastructure.doctor.detectors.layout import detect_manuscript_config, detect_project_structure
from infrastructure.doctor.detectors.state import (
    detect_doctor_state_writable,
    detect_lockfile_drift,
    detect_optional_services,
    detect_pre_commit_installed,
)
from infrastructure.doctor.detectors.tooling import (
    detect_python_version,
    detect_run_sh_executable,
    detect_uv_available,
)
from infrastructure.doctor.models import Finding, Severity

DetectorFn = Callable[[Path], list[Finding]]

DETECTORS: tuple[DetectorFn, ...] = (
    detect_doctor_state_writable,
    detect_uv_available,
    detect_python_version,
    detect_run_sh_executable,
    detect_project_structure,
    detect_manuscript_config,
    detect_pycache_clutter,
    detect_stale_coverage_files,
    detect_orphan_output_dirs,
    detect_pre_commit_installed,
    detect_lockfile_drift,
    detect_optional_services,
)

__all__ = [
    "DETECTORS",
    "DetectorFn",
    "run_detectors",
    "detect_doctor_state_writable",
    "detect_uv_available",
    "detect_python_version",
    "detect_run_sh_executable",
    "detect_project_structure",
    "detect_manuscript_config",
    "detect_pycache_clutter",
    "detect_stale_coverage_files",
    "detect_orphan_output_dirs",
    "detect_pre_commit_installed",
    "detect_lockfile_drift",
    "detect_optional_services",
]


def run_detectors(
    repo_root: Path,
    selected: tuple[DetectorFn, ...] | None = None,
) -> list[Finding]:
    """Run every detector (or only ``selected``) and return findings."""
    detectors = selected or DETECTORS
    out: list[Finding] = []
    for fn in detectors:
        try:
            out.extend(fn(repo_root))
        except Exception as exc:  # noqa: BLE001 — defensive isolation
            out.append(
                Finding(
                    code=f"DOC000[{fn.__name__}]",
                    title=f"detector {fn.__name__} crashed",
                    severity=Severity.CRITICAL,
                    healthy=False,
                    description=str(exc),
                    evidence={"detector": fn.__name__},
                )
            )
    out.sort(key=lambda f: f.code)
    return out
