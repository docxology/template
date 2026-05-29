"""Doctor detectors — Tooling probes."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from infrastructure.doctor.models import Finding, RepairLevel, Severity, TherapyLevel


def detect_uv_available(repo_root: Path) -> list[Finding]:
    """Verify ``uv`` is on PATH — required for every doctor remediation
    that touches dependencies."""
    uv_path = shutil.which("uv")
    if uv_path is None:
        return [
            Finding(
                code="DOC101",
                title="uv package manager not installed",
                severity=Severity.CRITICAL,
                healthy=False,
                description=(
                    "The repository's setup, testing, and rendering all run "
                    "via ``uv``. Install via `curl -LsSf https://astral.sh/uv/install.sh | sh`."
                ),
                evidence={"PATH": os.environ.get("PATH", "")},
                # No automatic fixer — installing system tooling is out of
                # scope for an automatic remediator.
            )
        ]
    return [
        Finding(
            code="DOC101",
            title="uv package manager present",
            severity=Severity.INFO,
            healthy=True,
            description=f"Found uv at {uv_path}.",
            evidence={"path": uv_path},
        )
    ]


def detect_python_version(repo_root: Path) -> list[Finding]:
    """Project requires Python 3.10+ (see pyproject.toml)."""
    import sys

    major, minor = sys.version_info[:2]
    healthy = (major, minor) >= (3, 10)
    return [
        Finding(
            code="DOC102",
            title="Python version compatible",
            severity=Severity.INFO if healthy else Severity.ERROR,
            healthy=healthy,
            description=(f"Project requires Python >= 3.10. Detected {major}.{minor}.{sys.version_info.micro}."),
            evidence={
                "version": f"{major}.{minor}.{sys.version_info.micro}",
                "executable": sys.executable,
            },
        )
    ]


def detect_run_sh_executable(repo_root: Path) -> list[Finding]:
    """``run.sh`` must be present and executable for ``./run.sh`` to work."""
    run_sh = repo_root / "run.sh"
    if not run_sh.is_file():
        return [
            Finding(
                code="DOC103",
                title="run.sh missing",
                severity=Severity.ERROR,
                healthy=False,
                description="run.sh is the canonical entry point but is missing.",
                evidence={"path": str(run_sh)},
            )
        ]
    is_executable = os.access(run_sh, os.X_OK)
    if is_executable:
        return [
            Finding(
                code="DOC103",
                title="run.sh executable",
                severity=Severity.INFO,
                healthy=True,
                description="run.sh is present and executable.",
                evidence={"path": str(run_sh)},
            )
        ]
    return [
        Finding(
            code="DOC103",
            title="run.sh not executable",
            severity=Severity.WARN,
            healthy=False,
            description=(
                "run.sh exists but lacks the executable bit. ``./run.sh`` will fail with 'permission denied'."
            ),
            evidence={"path": str(run_sh)},
            repair_levels=(
                RepairLevel(
                    level=TherapyLevel.CONSERVATIVE,
                    fix_id="fix_make_run_sh_executable",
                    description="chmod +x run.sh",
                ),
            ),
        )
    ]
