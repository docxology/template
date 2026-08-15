"""Single-read accessors for project ``pyproject.toml`` test/coverage settings."""

from __future__ import annotations

try:
    import tomllib
except ImportError:  # Python <3.11 — use backport
    import tomli as tomllib  # type: ignore[no-redef]
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class ProjectPyprojectConfig:
    """Coverage and dependency flags from a project ``pyproject.toml``."""

    path: Path
    coverage_fail_under: int | None
    has_coverage_run: bool
    declares_dev_extra: bool
    project_test_command: tuple[str, ...] | None
    project_test_command_error: str | None


@lru_cache(maxsize=128)
def load_project_pyproject(project_root: Path) -> ProjectPyprojectConfig | None:
    """Parse ``pyproject.toml`` once; return ``None`` when missing or invalid."""
    pyproject = project_root / "pyproject.toml"
    if not pyproject.is_file():
        return None
    try:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return None

    coverage = data.get("tool", {}).get("coverage", {})
    declared = coverage.get("report", {}).get("fail_under")
    fail_under: int | None = int(declared) if isinstance(declared, (int, float)) else None
    has_run = coverage.get("run") is not None
    optional = data.get("project", {}).get("optional-dependencies", {})
    dev_extra = isinstance(optional, dict) and "dev" in optional
    template = data.get("tool", {}).get("template", {})
    raw_test_command = template.get("project_test_command") if isinstance(template, dict) else None
    test_command: tuple[str, ...] | None = None
    test_command_error: str | None = None
    if raw_test_command is not None:
        if (
            not isinstance(raw_test_command, list)
            or not raw_test_command
            or any(not isinstance(part, str) or not part.strip() for part in raw_test_command)
        ):
            test_command_error = (
                "[tool.template].project_test_command must be a non-empty TOML array of non-empty strings"
            )
        else:
            test_command = tuple(raw_test_command)

    return ProjectPyprojectConfig(
        path=pyproject,
        coverage_fail_under=fail_under,
        has_coverage_run=has_run,
        declares_dev_extra=dev_extra,
        project_test_command=test_command,
        project_test_command_error=test_command_error,
    )


def project_declared_coverage_floor(project_root: Path) -> int | None:
    """Return a project's self-declared ``fail_under`` from ``pyproject.toml``, if any."""
    cfg = load_project_pyproject(project_root)
    return cfg.coverage_fail_under if cfg else None


def resolve_project_cov_config(project_root: Path) -> Path | None:
    """Return project ``pyproject.toml`` when it declares ``[tool.coverage.run]``."""
    cfg = load_project_pyproject(project_root)
    if cfg is None or not cfg.has_coverage_run:
        return None
    return cfg.path


def project_declares_dev_extra(project_root: Path) -> bool:
    """Return True when ``pyproject.toml`` lists a ``dev`` optional-dependency group."""
    cfg = load_project_pyproject(project_root)
    return bool(cfg and cfg.declares_dev_extra)


def project_declared_test_command(project_root: Path) -> tuple[str, ...] | None:
    """Return an explicit single-project Stage-01 verifier command.

    The declaration is deliberately opt-in. A malformed declaration fails
    closed instead of silently falling back to the generic pytest lane.
    """
    cfg = load_project_pyproject(project_root)
    if cfg is None:
        return None
    if cfg.project_test_command_error:
        raise ValueError(cfg.project_test_command_error)
    return cfg.project_test_command


__all__ = [
    "ProjectPyprojectConfig",
    "load_project_pyproject",
    "project_declared_coverage_floor",
    "project_declared_test_command",
    "project_declares_dev_extra",
    "resolve_project_cov_config",
]
