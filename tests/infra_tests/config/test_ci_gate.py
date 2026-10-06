"""Execute the actual workflow aggregate policy against discriminating inputs."""

from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from infrastructure.core.ci_policy import required_ci_jobs


def _workflow() -> dict:
    root = Path(__file__).resolve().parents[3]
    return yaml.safe_load((root / ".github/workflows/ci.yml").read_text(encoding="utf-8"))


def _success() -> dict[str, dict]:
    values = {name: {"result": "success"} for name in _workflow()["jobs"]["ci-gate"]["needs"]}
    values["detect"]["outputs"] = {"setup_hook": "false", "fep_lean": "false"}
    return values


def _run(values: object, event: str, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    assert shutil.which("jq"), "the declared CI aggregate policy requires real jq"
    steps = _workflow()["jobs"]["ci-gate"]["steps"]
    assert len(steps) == 1 and steps[0]["name"] == "Evaluate upstream job results"
    return subprocess.run(
        ["bash", "-e", "-o", "pipefail", "-c", steps[0]["run"]],
        cwd=tmp_path,
        env={
            "PATH": os.environ.get("PATH", os.defpath),
            "NEEDS_JSON": json.dumps(values),
            "EVENT_NAME": event,
            "REQUIRED_JOBS_JSON": json.dumps(required_ci_jobs(Path(__file__).resolve().parents[3])),
        },
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )


def test_aggregate_requires_every_declared_job_and_keeps_independent_checks() -> None:
    jobs = _workflow()["jobs"]
    assert set(jobs["ci-gate"]["needs"]) == set(jobs) - {"ci-gate"}
    assert jobs["ci-gate"]["if"] == "always()"
    assert set(required_ci_jobs(Path(__file__).resolve().parents[3])) == set(jobs) - {"ci-gate"}
    for name in ("health", "validate", "security", "docs-lint"):
        assert "needs" not in jobs[name]
        assert jobs[name]["steps"]


@pytest.mark.parametrize("event", ["push", "pull_request", "schedule", "workflow_dispatch"])
def test_actual_aggregate_accepts_success(event: str, tmp_path: Path) -> None:
    result = _run(_success(), event, tmp_path)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("event", ["push", "pull_request"])
def test_actual_aggregate_accepts_only_reason_bound_conditional_skips(event: str, tmp_path: Path) -> None:
    values = _success()
    for name in ("setup-hook-windows-smoke", "fep-lean", "test-infra-slow", "public-matrix-receipt"):
        values[name]["result"] = "skipped"
    result = _run(values, event, tmp_path)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("name", ["lint", "health", "validate", "security", "docs-lint", "test-infra", "test-project"])
@pytest.mark.parametrize("state", ["skipped", "failure", "cancelled", None])
def test_actual_aggregate_refuses_incomplete_required_jobs(name: str, state: str | None, tmp_path: Path) -> None:
    values = _success()
    values[name]["result"] = state
    assert _run(values, "push", tmp_path).returncode != 0


@pytest.mark.parametrize("name,flag", [("setup-hook-windows-smoke", "setup_hook"), ("fep-lean", "fep_lean")])
@pytest.mark.parametrize("flag_value", ["true", None, False])
def test_actual_aggregate_refuses_conditional_skip_without_exact_reason(
    name: str, flag: str, flag_value: object, tmp_path: Path
) -> None:
    values = _success()
    values[name]["result"] = "skipped"
    values["detect"]["outputs"][flag] = flag_value
    assert _run(values, "push", tmp_path).returncode != 0


@pytest.mark.parametrize("name", ["test-infra-slow", "public-matrix-receipt"])
@pytest.mark.parametrize("event", ["schedule", "workflow_dispatch", "unknown-event"])
def test_actual_aggregate_refuses_skipped_required_event_lane(name: str, event: str, tmp_path: Path) -> None:
    values = _success()
    values[name]["result"] = "skipped"
    assert _run(values, event, tmp_path).returncode != 0


@pytest.mark.parametrize("values", [{}, [], None])
def test_actual_aggregate_refuses_empty_or_malformed_results(values: object, tmp_path: Path) -> None:
    assert _run(copy.deepcopy(values), "push", tmp_path).returncode != 0


@pytest.mark.parametrize("name", required_ci_jobs(Path(__file__).resolve().parents[3]))
def test_actual_aggregate_refuses_each_missing_required_job(name: str, tmp_path: Path) -> None:
    values = _success()
    del values[name]
    assert _run(values, "push", tmp_path).returncode != 0


def test_actual_aggregate_refuses_an_undeclared_job(tmp_path: Path) -> None:
    values = _success()
    values["undeclared-job"] = {"result": "success"}
    assert _run(values, "push", tmp_path).returncode != 0


@pytest.mark.parametrize("fault", ["omitted-job", "duplicate-job", "missing-always", "invalid-yaml"])
def test_source_owned_aggregate_refuses_invalid_workflow_selection(tmp_path: Path, fault: str) -> None:
    workflow = _workflow()
    aggregate = workflow["jobs"]["ci-gate"]
    if fault == "omitted-job":
        aggregate["needs"].remove("lint")
    elif fault == "duplicate-job":
        aggregate["needs"].append("lint")
    else:
        aggregate["if"] = "success()"
    path = tmp_path / ".github/workflows/ci.yml"
    path.parent.mkdir(parents=True)
    path.write_text(yaml.safe_dump(workflow))
    if fault == "invalid-yaml":
        path.write_text("jobs: [invalid\n")
    with pytest.raises(ValueError):
        required_ci_jobs(tmp_path)
