"""Source-owned complete job selection for the hosted CI aggregate."""

from __future__ import annotations

from pathlib import Path

import yaml

from infrastructure.core.files.secure_write import read_bytes_confined


def required_ci_jobs(repo_root: Path) -> tuple[str, ...]:
    """Require one aggregate covering every other declared workflow job."""
    root = repo_root.resolve(strict=True)
    try:
        workflow = yaml.safe_load(read_bytes_confined(root, root / ".github/workflows/ci.yml", max_bytes=256 * 1024))
    except yaml.YAMLError as error:
        raise ValueError("CI workflow contains invalid YAML") from error
    if not isinstance(workflow, dict) or not isinstance(workflow.get("jobs"), dict):
        raise ValueError("CI workflow requires its declared job map")
    jobs = workflow["jobs"]
    aggregate = jobs.get("ci-gate")
    if not isinstance(aggregate, dict) or aggregate.get("if") != "always()":
        raise ValueError("CI aggregate must evaluate every completion outcome")
    names = aggregate.get("needs")
    if (
        not isinstance(names, list)
        or not names
        or any(not isinstance(name, str) or not name for name in names)
        or len(set(names)) != len(names)
        or set(names) != set(jobs) - {"ci-gate"}
    ):
        raise ValueError("CI aggregate selection differs from the complete declared job set")
    return tuple(sorted(names))


__all__ = ["required_ci_jobs"]
