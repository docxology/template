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


_EVALUATION = "Evaluate upstream job results"
_SUMMARY = "Summarize CI gate outcomes"


def _workflow() -> dict:
    root = Path(__file__).resolve().parents[3]
    return yaml.safe_load((root / ".github/workflows/hardening.yml").read_text(encoding="utf-8"))


def _gate_steps() -> dict[str, dict]:
    """Return the CI Gate steps by name: one decision followed by one report."""
    steps = _workflow()["jobs"]["ci-gate"]["steps"]
    names = [step.get("name") for step in steps]
    assert names == [_EVALUATION, _SUMMARY], names
    return dict(zip(names, steps, strict=True))


def _success() -> dict[str, dict]:
    values = {name: {"result": "success"} for name in _workflow()["jobs"]["ci-gate"]["needs"]}
    values["detect"]["outputs"] = {"setup_hook": "false", "fep_lean": "false"}
    return values


def _run(values: object, event: str, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    assert shutil.which("jq"), "the declared CI aggregate policy requires real jq"
    return subprocess.run(
        ["bash", "-e", "-o", "pipefail", "-c", _gate_steps()[_EVALUATION]["run"]],
        cwd=tmp_path,
        env={
            "PATH": os.environ.get("PATH", os.defpath),
            "NEEDS_JSON": json.dumps(values),
            "EVENT_NAME": event,
            "REQUIRED_JOBS_JSON": json.dumps(required_ci_jobs(Path(__file__).resolve().parents[3], "hardening.yml")),
        },
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )


def _summarize(
    values: object, event: str, gate_outcome: str, tmp_path: Path
) -> tuple[subprocess.CompletedProcess[str], list[str]]:
    """Run the actual report step and return its process and table rows."""
    assert shutil.which("jq"), "the declared CI Gate report requires real jq"
    step = _gate_steps()[_SUMMARY]
    assert step["shell"] == "bash"
    summary = tmp_path / "step-summary.md"
    summary.write_text("", encoding="utf-8")
    result = subprocess.run(
        ["bash", "-e", "-o", "pipefail", "-c", step["run"]],
        cwd=tmp_path,
        env={
            "PATH": os.environ.get("PATH", os.defpath),
            "NEEDS_JSON": json.dumps(values),
            "EVENT_NAME": event,
            "GATE_OUTCOME": gate_outcome,
            "JOB_STATUS": gate_outcome,
            "GITHUB_SHA": "0" * 40,
            "GITHUB_STEP_SUMMARY": str(summary),
        },
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    rows = [line for line in summary.read_text(encoding="utf-8").splitlines() if line.startswith("| ")]
    return result, rows[2:]


def _job(values: dict[str, dict], event: str, tmp_path: Path) -> tuple[bool, bool, list[str]]:
    """Run decision then report as the hosted job does; return (decision, report ok, rows)."""
    decision = _run(values, event, tmp_path).returncode == 0
    report, rows = _summarize(values, event, "success" if decision else "failure", tmp_path)
    assert not report.stderr, report.stderr
    return decision, report.returncode == 0, rows


def test_gate_decision_precedes_a_report_that_cannot_mask_it() -> None:
    job = _workflow()["jobs"]["ci-gate"]
    steps = _gate_steps()
    evaluation, summary = steps[_EVALUATION], steps[_SUMMARY]
    assert "continue-on-error" not in job
    assert all("continue-on-error" not in step for step in steps.values())
    assert evaluation["id"] == "results" and "if" not in evaluation
    assert summary["if"] == "always()"
    assert summary["env"]["GATE_OUTCOME"] == "${{ steps.results.outcome }}"
    assert summary["env"]["NEEDS_JSON"] == evaluation["env"]["NEEDS_JSON"] == "${{ toJson(needs) }}"


def _skip(values: dict[str, dict], *names: str) -> dict[str, dict]:
    for name in names:
        values[name]["result"] = "skipped"
    return values


@pytest.mark.parametrize(
    "case,event,admitted",
    [
        ("success", "push", True),
        ("reasoned-skips", "pull_request", True),
        ("failed-lint", "push", False),
        ("skipped-lint", "push", False),
        ("scheduled-slow-skip", "schedule", False),
    ],
)
def test_actual_job_outcome_is_the_aggregate_decision(case: str, event: str, admitted: bool, tmp_path: Path) -> None:
    values = _success()
    if case == "reasoned-skips":
        _skip(values, "setup-hook-windows-smoke", "fep-lean", "test-infra-slow", "public-matrix-receipt")
    elif case == "failed-lint":
        values["lint"]["result"] = "failure"
    elif case == "skipped-lint":
        _skip(values, "lint")
    elif case == "scheduled-slow-skip":
        _skip(values, "test-infra-slow")
    decision, reported, rows = _job(values, event, tmp_path)
    assert reported, "the report step must not fail the job or hide a refusal"
    assert decision is admitted
    assert [row.split(" | ")[0].removeprefix("| ") for row in rows] == list(values)


def test_actual_report_labels_only_admitted_skips(tmp_path: Path) -> None:
    values = _skip(_success(), "setup-hook-windows-smoke", "fep-lean", "test-infra-slow")
    admitted, reported, rows = _job(values, "push", tmp_path)
    assert admitted and reported
    assert "| setup-hook-windows-smoke | skipped | detect: setup_hook=false |" in rows
    assert "| fep-lean | skipped | detect: fep_lean=false |" in rows
    assert "| test-infra-slow | skipped | schedule/manual lane on push |" in rows
    assert "| lint | success |  |" in rows
    admitted, reported, rows = _job(_skip(_success(), "lint"), "push", tmp_path)
    assert not admitted and reported
    assert "| lint | skipped | not admitted by CI Gate |" in rows


def test_aggregate_requires_every_declared_job_and_keeps_independent_checks() -> None:
    jobs = _workflow()["jobs"]
    assert set(jobs["ci-gate"]["needs"]) == set(jobs) - {"ci-gate"}
    assert jobs["ci-gate"]["if"] == "always()"
    assert set(required_ci_jobs(Path(__file__).resolve().parents[3], "hardening.yml")) == set(jobs) - {"ci-gate"}
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


@pytest.mark.parametrize("name", required_ci_jobs(Path(__file__).resolve().parents[3], "hardening.yml"))
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
    path = tmp_path / ".github/workflows/hardening.yml"
    path.parent.mkdir(parents=True)
    path.write_text(yaml.safe_dump(workflow))
    if fault == "invalid-yaml":
        path.write_text("jobs: [invalid\n")
    with pytest.raises(ValueError):
        required_ci_jobs(tmp_path, "hardening.yml")
