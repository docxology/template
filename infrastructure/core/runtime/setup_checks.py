"""Environment setup checks for Stage 00."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from infrastructure.core.logging.utils import get_logger
from infrastructure.core.project_paths import resolve_project_root
from infrastructure.core.runtime.env_deps import (
    check_build_tools,
    check_dependencies,
)
from infrastructure.core.runtime.environment import (
    check_python_version,
    verify_source_structure,
)

from infrastructure.core.pipeline.outcomes import StageStatus
from infrastructure.core.runtime.prepared_runtime import (
    PreparedRuntimeUnavailable,
    check_prepared_packages,
    check_prepared_root_runtime,
)

logger = get_logger(__name__)


@dataclass(frozen=True)
class SetupCheckResult:
    """Check availability separately from malformed or failed local structure."""

    name: str
    status: StageStatus
    diagnostic: str = ""

    def __post_init__(self) -> None:
        if (
            not isinstance(self.name, str)
            or not self.name.strip()
            or not isinstance(self.status, StageStatus)
            or self.status not in {StageStatus.SUCCEEDED, StageStatus.BLOCKED, StageStatus.FAILED}
        ):
            raise ValueError("Setup checks require a named succeeded, blocked, or failed observation")


def check_setup_hook_prerequisites(repo_root: Path, project_name: str) -> bool:
    """Check declared prerequisites without executing a provisioning hook."""
    from infrastructure.project.setup_hook import preflight_setup_hook

    ok, messages = preflight_setup_hook(resolve_project_root(repo_root, project_name), strict=True)
    for message in messages:
        logger.info("Setup-hook prerequisite: %s", message)
    return ok


def run_environment_setup_checks(repo_root: Path, project_name: str) -> list[SetupCheckResult]:
    """Check already prepared requirements; never sync, install, or invoke hooks."""
    checks: tuple[tuple[str, Callable[[], bool], StageStatus], ...] = (
        ("Python version", check_python_version, StageStatus.BLOCKED),
        ("Dependencies", lambda: _check_prepared_dependencies(repo_root), StageStatus.BLOCKED),
        ("Build tools", check_build_tools, StageStatus.BLOCKED),
        ("Source structure", lambda: verify_source_structure(repo_root, project_name), StageStatus.FAILED),
        ("Project discovery", lambda: validate_project_discovery(repo_root, project_name), StageStatus.FAILED),
        (
            "Setup-hook prerequisites (no execution)",
            lambda: check_setup_hook_prerequisites(repo_root, project_name),
            StageStatus.BLOCKED,
        ),
    )
    results: list[SetupCheckResult] = []
    for name, check, unavailable in checks:
        try:
            passed = check()
            results.append(SetupCheckResult(name, StageStatus.SUCCEEDED if passed else unavailable))
        except PreparedRuntimeUnavailable as exc:
            results.append(SetupCheckResult(name, StageStatus.BLOCKED, str(exc)))
        except (OSError, ValueError, RuntimeError) as exc:
            logger.error("Error during %s: %s", name, exc)
            results.append(SetupCheckResult(name, StageStatus.FAILED, str(exc)))
    return results


def _check_prepared_dependencies(repo_root: Path) -> bool:
    check_prepared_root_runtime(repo_root)
    check_prepared_packages(["pytest>=7.0"])
    return check_dependencies()[0]


def aggregate_check_results(results: list[SetupCheckResult]) -> tuple[int, list[str]]:
    """Keep failed structure and unavailable preparation distinct in the exit code."""
    states = {result.status for result in results}
    code = 1 if not results or StageStatus.FAILED in states else (75 if StageStatus.BLOCKED in states else 0)
    lines = [
        f"{result.status.value.upper()}: {result.name}" + (f" — {result.diagnostic}" if result.diagnostic else "")
        for result in results
    ]
    return code, lines


def validate_project_discovery(
    repo_root: Path,
    project_name: str,
    *,
    project_discoverer: Callable[[Path], list[Any]] | None = None,
) -> bool:
    """Validate project discovery."""
    from infrastructure.core.project_paths import resolve_project_root
    from infrastructure.project.discovery import discover_projects
    from infrastructure.project.validation import validate_project_structure

    logger.info("Discovering available projects...")
    try:
        target_root = resolve_project_root(repo_root, project_name)
        target_valid, target_message = validate_project_structure(target_root)
        if not target_valid:
            logger.error("Target project is not runnable at %s: %s", target_root, target_message)
            return False
        logger.info("Target project resolved: %s", target_root)

        projects = (project_discoverer or discover_projects)(repo_root)
        if not projects:
            logger.warning("No valid projects found in projects/ directory")
            return False

        logger.info("Discovered %d valid project(s):", len(projects))
        for project in projects:
            marker = "→" if project.name == project_name else " "
            structure = []
            if project.has_src:
                structure.append("src")
            if project.has_tests:
                structure.append("tests")
            if project.has_scripts:
                structure.append("scripts")
            if project.has_manuscript:
                structure.append("manuscript")
            structure_str = ", ".join(structure) if structure else "minimal"
            logger.info("  %s %s: %s", marker, project.name, structure_str)
            if project.name == project_name:
                logger.info("    Setting up: %s", project.name)
        return True
    except OSError as exc:
        logger.error("Project discovery failed: %s", exc)
        return False
