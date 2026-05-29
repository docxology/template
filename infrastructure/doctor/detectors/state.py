"""Doctor detectors — Optional services and doctor state."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from infrastructure.doctor.models import Finding, RepairLevel, Severity, TherapyLevel


def detect_pre_commit_installed(repo_root: Path) -> list[Finding]:
    """``.git/hooks/pre-commit`` should reference ``pre-commit`` when the
    repo has a ``.pre-commit-config.yaml``."""
    config = repo_root / ".pre-commit-config.yaml"
    if not config.is_file():
        return [
            Finding(
                code="DOC401",
                title="no pre-commit configuration",
                severity=Severity.INFO,
                healthy=True,
                description="Repo does not declare pre-commit hooks; nothing to install.",
            )
        ]
    hook = repo_root / ".git" / "hooks" / "pre-commit"
    if not hook.is_file():
        return [
            Finding(
                code="DOC401",
                title="pre-commit hook not installed",
                severity=Severity.WARN,
                healthy=False,
                description=(
                    "The repo declares pre-commit hooks but the git hook is not "
                    "installed locally. CI will still run them, but local commits "
                    "won't be gated."
                ),
                evidence={"config": str(config), "expected_hook": str(hook)},
                repair_levels=(
                    RepairLevel(
                        level=TherapyLevel.CONSERVATIVE,
                        fix_id="fix_install_pre_commit_hook",
                        description="Run `pre-commit install`",
                    ),
                ),
            )
        ]
    return [
        Finding(
            code="DOC401",
            title="pre-commit hook installed",
            severity=Severity.INFO,
            healthy=True,
            description="Local pre-commit hook is in place.",
            evidence={"hook": str(hook)},
        )
    ]


def detect_lockfile_drift(repo_root: Path) -> list[Finding]:
    """``uv.lock`` should be at least as new as ``pyproject.toml``."""
    pyproject = repo_root / "pyproject.toml"
    lock = repo_root / "uv.lock"
    if not pyproject.is_file():
        return [
            Finding(
                code="DOC402",
                title="pyproject.toml missing at repo root",
                severity=Severity.CRITICAL,
                healthy=False,
                description="No root pyproject.toml — uv cannot manage the workspace.",
                evidence={"path": str(pyproject)},
            )
        ]
    if not lock.is_file():
        return [
            Finding(
                code="DOC402",
                title="uv.lock missing",
                severity=Severity.WARN,
                healthy=False,
                description=(
                    "uv.lock is missing — runs will resolve dependencies fresh "
                    "every time. Run `uv sync` to generate it."
                ),
                evidence={"path": str(lock)},
                repair_levels=(
                    RepairLevel(
                        level=TherapyLevel.MODERATE,
                        fix_id="fix_run_uv_sync",
                        description="Run `uv sync` to regenerate uv.lock",
                    ),
                ),
            )
        ]
    py_mtime = pyproject.stat().st_mtime
    lock_mtime = lock.stat().st_mtime
    drift = py_mtime - lock_mtime
    if drift > 1.0:
        return [
            Finding(
                code="DOC402",
                title="uv.lock older than pyproject.toml",
                severity=Severity.WARN,
                healthy=False,
                description=(
                    f"uv.lock is {drift:.0f}s older than pyproject.toml — "
                    "dependencies may have changed since the last sync."
                ),
                evidence={
                    "pyproject_mtime": py_mtime,
                    "lock_mtime": lock_mtime,
                    "drift_seconds": drift,
                },
                repair_levels=(
                    RepairLevel(
                        level=TherapyLevel.MODERATE,
                        fix_id="fix_run_uv_sync",
                        description="Run `uv sync` to refresh uv.lock",
                    ),
                ),
            )
        ]
    return [
        Finding(
            code="DOC402",
            title="uv.lock up to date",
            severity=Severity.INFO,
            healthy=True,
            description="uv.lock is at least as new as pyproject.toml.",
            evidence={"drift_seconds": drift},
        )
    ]


def detect_optional_services(repo_root: Path) -> list[Finding]:
    """Surface optional tools (Ollama, Docker, LaTeX) as info-only findings.

    These never reduce the overall score by themselves — they're listed
    so an agent reading ``--json`` can plan which LLM/render stages to
    skip on this machine.
    """
    findings: list[Finding] = []
    for tool, label, code in [
        ("ollama", "Ollama", "DOC501"),
        ("docker", "Docker", "DOC502"),
        ("xelatex", "XeLaTeX", "DOC503"),
        ("pandoc", "Pandoc", "DOC504"),
    ]:
        path = shutil.which(tool)
        found = path is not None
        findings.append(
            Finding(
                code=code,
                title=f"{label} {'available' if found else 'not installed'}",
                severity=Severity.INFO if found else Severity.WARN,
                healthy=found,
                description=(f"{label} is required by some optional pipeline stages."),
                evidence={"path": path or ""},
            )
        )
    return findings


def detect_doctor_state_writable(repo_root: Path) -> list[Finding]:
    """``.doctor/`` parent must be writable; diagnose-only runs must not create state."""
    doctor_dir = repo_root / ".doctor"
    probe_target = doctor_dir if doctor_dir.exists() else repo_root
    if not os.access(probe_target, os.W_OK):
        return [
            Finding(
                code="DOC601",
                title="doctor state directory not writable",
                severity=Severity.CRITICAL,
                healthy=False,
                description=("Cannot write to .doctor/ — no fix can be applied safely without a backup target."),
                evidence={"path": str(doctor_dir), "probe": str(probe_target)},
            )
        ]
    return [
        Finding(
            code="DOC601",
            title="doctor state directory writable",
            severity=Severity.INFO,
            healthy=True,
            description="Backups and journal can be written.",
            evidence={"path": str(doctor_dir)},
        )
    ]
