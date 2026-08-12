"""Changed-surface guidance for bounded, non-vacuous test selection.

The planner is deliberately advisory: it recommends the smallest safe lane
from tracked paths, while release gates still run their declared full scopes.
It encodes the repository's important isolation rule that distinct exemplar
projects may run independently, but an outer project matrix must not be paired
with inner pytest-xdist workers.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Iterable


@dataclass(frozen=True)
class TestImpactPlan:
    """Stable recommendation for a changed path set."""

    changed_paths: tuple[str, ...]
    infrastructure_changed: bool
    documentation_changed: bool
    project_names: tuple[str, ...]
    local_only_changed: bool
    recommended_lanes: tuple[str, ...]
    outer_project_parallelism_allowed: bool
    repository_control_changed: bool = False
    resource_pool_changed: bool = False


def _project_name(path: PurePosixPath) -> str | None:
    """Return a qualified public exemplar name for a project path."""
    parts = path.parts
    if len(parts) >= 3 and parts[0:2] == ("projects", "templates"):
        return "/".join(parts[1:3])
    return None


def classify_changed_paths(paths: Iterable[str]) -> TestImpactPlan:
    """Classify changed paths into isolated project, infra, and docs lanes."""
    normalized = tuple(sorted({str(path).replace("\\", "/") for path in paths if str(path).strip()}))
    infrastructure_changed = False
    documentation_changed = False
    local_only_changed = False
    repository_control_changed = False
    resource_pool_changed = False
    projects: set[str] = set()

    for raw_path in normalized:
        path = PurePosixPath(raw_path)
        project_name = _project_name(path)
        if project_name is not None:
            projects.add(project_name)
        if path.parts and path.parts[0] in {"infrastructure", "scripts", "tests"}:
            infrastructure_changed = True
        if path.parts and path.parts[0] in {"docs", ".github"}:
            documentation_changed = True
        if path.as_posix() in {
            "pyproject.toml",
            "uv.lock",
            "bandit.yaml",
            ".pre-commit-config.yaml",
            ".gitignore",
            "mypy.ini",
        }:
            repository_control_changed = True
        if len(path.parts) >= 2 and path.parts[0] in {"fonds", "rules", "tools"} and path.parts[1] == "templates":
            resource_pool_changed = True
        if path.name in {"AGENTS.md", "README.md", "CLAUDE.md", "TO-DO.md", "TODO.md"}:
            documentation_changed = True
        if len(path.parts) >= 2 and path.parts[0] in {"projects", "fonds", "rules", "tools"}:
            if len(path.parts) > 1 and path.parts[1] in {
                "working",
                "ongoing",
                "archive",
                "active",
            }:
                local_only_changed = True

    lanes: list[str] = []
    if infrastructure_changed:
        lanes.append("infrastructure-serial")
    if documentation_changed:
        lanes.append("documentation-contract")
    if repository_control_changed:
        lanes.append("repository-control")
    if resource_pool_changed:
        lanes.append("resource-pool-contract")
    lanes.extend(f"project:{name}" for name in sorted(projects))
    if not lanes:
        lanes.append("repository-smoke")

    # Docs and infrastructure can affect every project. Independent exemplar
    # lanes may use outer workers only when neither global surface changed.
    outer_parallel = (
        len(projects) > 1
        and not infrastructure_changed
        and not documentation_changed
        and not repository_control_changed
        and not resource_pool_changed
    )
    return TestImpactPlan(
        changed_paths=normalized,
        infrastructure_changed=infrastructure_changed,
        documentation_changed=documentation_changed,
        project_names=tuple(sorted(projects)),
        local_only_changed=local_only_changed,
        recommended_lanes=tuple(lanes),
        outer_project_parallelism_allowed=outer_parallel,
        repository_control_changed=repository_control_changed,
        resource_pool_changed=resource_pool_changed,
    )


__all__ = ["TestImpactPlan", "classify_changed_paths"]
