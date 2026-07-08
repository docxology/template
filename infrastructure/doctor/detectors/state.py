"""Doctor detectors — Optional services and doctor state."""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

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
    """Surface optional tools as info-only findings.

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


def _codex_home() -> Path:
    configured = os.environ.get("CODEX_HOME")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".codex"


def _load_toml(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        with path.open("rb") as handle:
            return tomllib.load(handle), None
    except OSError as exc:
        return None, str(exc)
    except tomllib.TOMLDecodeError as exc:
        return None, str(exc)


def _load_json_object(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, str(exc)
    if not isinstance(data, dict):
        return None, "top-level JSON value is not an object"
    return data, None


def _hook_file_has_active_hooks(path: Path) -> bool:
    data, error = _load_json_object(path)
    if error or data is None:
        return False
    hooks = data.get("hooks")
    return isinstance(hooks, dict) and bool(hooks)


def detect_codex_startup_config(repo_root: Path) -> list[Finding]:
    """Detect user-level Codex config issues that create noisy agent startup."""
    codex_home = _codex_home()
    config_path = codex_home / "config.toml"
    hooks_path = codex_home / "hooks.json"
    problems: list[str] = []
    invalid_hook_files: list[dict[str, Any]] = []
    scanned_hook_files = 0
    deprecated_codex_hooks = False
    duplicate_hook_sources = False
    config_hook_sections: list[str] = []

    if config_path.exists():
        config, config_error = _load_toml(config_path)
        if config_error or config is None:
            problems.append(f"{config_path} is not valid TOML")
        else:
            features = config.get("features")
            if isinstance(features, dict) and "codex_hooks" in features:
                deprecated_codex_hooks = True
                problems.append("remove deprecated [features].codex_hooks and use [features].hooks")
            hooks_table = config.get("hooks")
            if isinstance(hooks_table, dict):
                config_hook_sections = sorted(k for k in hooks_table if k != "state")
    elif hooks_path.exists():
        problems.append(f"{config_path} is missing while {hooks_path} is active")

    user_hooks_active = hooks_path.exists() and _hook_file_has_active_hooks(hooks_path)
    duplicate_hook_sources = bool(user_hooks_active and config_hook_sections)
    if duplicate_hook_sources:
        problems.append("keep startup hooks in either config.toml or hooks.json, not both")

    hook_paths = [hooks_path] if hooks_path.exists() else []
    plugin_hooks_root = codex_home / "plugins" / "cache"
    if plugin_hooks_root.exists():
        hook_paths.extend(sorted(plugin_hooks_root.glob("**/hooks/hooks.json"))[:128])
    for hook_path in hook_paths:
        scanned_hook_files += 1
        data, error = _load_json_object(hook_path)
        if error or data is None:
            invalid_hook_files.append({"path": str(hook_path), "error": error or "invalid JSON object"})
            continue
        unexpected = sorted(k for k in data if k != "hooks")
        if unexpected:
            invalid_hook_files.append({"path": str(hook_path), "unexpected_keys": unexpected})
    if invalid_hook_files:
        problems.append("hook JSON files must contain only the top-level hooks object")

    if problems:
        return [
            Finding(
                code="DOC505",
                title="Codex startup config warnings present",
                severity=Severity.WARN,
                healthy=False,
                description="; ".join(problems),
                evidence={
                    "codex_home": str(codex_home),
                    "config": str(config_path),
                    "hooks_json": str(hooks_path),
                    "deprecated_codex_hooks": deprecated_codex_hooks,
                    "duplicate_hook_sources": duplicate_hook_sources,
                    "config_hook_sections": config_hook_sections,
                    "invalid_hook_files": invalid_hook_files,
                    "scanned_hook_files": scanned_hook_files,
                },
            )
        ]
    return [
        Finding(
            code="DOC505",
            title="Codex startup config clean",
            severity=Severity.INFO,
            healthy=True,
            description=(
                "No deprecated Codex hook flag, duplicate user hook source, or invalid hook JSON metadata detected."
            ),
            evidence={
                "codex_home": str(codex_home),
                "config": str(config_path),
                "scanned_hook_files": scanned_hook_files,
            },
        )
    ]


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
