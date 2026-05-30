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

    return ProjectPyprojectConfig(
        path=pyproject,
        coverage_fail_under=fail_under,
        has_coverage_run=has_run,
        declares_dev_extra=dev_extra,
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


__all__ = [
    "ProjectPyprojectConfig",
    "load_project_pyproject",
    "project_declared_coverage_floor",
    "project_declares_dev_extra",
    "resolve_project_cov_config",
]
