"""Fast CI stays non-vacuous and fails when required work is absent or fails."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess

import pytest
import yaml

from infrastructure.core.ci_policy import required_ci_jobs
from infrastructure.core.testing.ci_smoke import project_smoke_matrix
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

REPO = Path(__file__).resolve().parents[3]


def test_every_public_project_has_real_behavioral_tests() -> None:
    matrix = project_smoke_matrix(REPO)
    assert {row["project"] for row in matrix["include"]} == set(PUBLIC_PROJECT_NAMES)
    assert len(matrix["include"]) == len(PUBLIC_PROJECT_NAMES)


@pytest.mark.parametrize("fault", ["missing-project", "extra-project", "empty-selection", "escape", "missing-test"])
def test_invalid_smoke_selection_fails_before_running_a_project(tmp_path: Path, fault: str) -> None:
    selection = json.loads((REPO / ".github/project-smoke.json").read_text())
    first = next(iter(selection))
    if fault == "missing-project":
        selection.pop(first)
    elif fault == "extra-project":
        selection["active/private"] = ["tests/test_private.py"]
    elif fault == "empty-selection":
        selection[first] = []
    elif fault == "escape":
        selection[first] = ["tests/../../private.py"]
    else:
        selection[first] = ["tests/nonexistent.py"]
    (tmp_path / ".github").mkdir()
    (tmp_path / ".github/project-smoke.json").write_text(json.dumps(selection))
    with pytest.raises(ValueError):
        project_smoke_matrix(tmp_path)


@pytest.mark.parametrize(
    ("coverage_requested", "fault"),
    [
        ("false", "none"),
        ("true", "none"),
        *(
            (request, fault)
            for request in ("false", "true")
            for fault in ("failure", "cancelled", "skipped", "omitted", "extra", "malformed")
        ),
        ("true", "coverage-failure"),
        ("true", "coverage-cancelled"),
        ("true", "coverage-skipped"),
        ("true", "coverage-omitted"),
        ("false", "coverage-success"),
        ("false", "coverage-failure"),
        ("false", "coverage-cancelled"),
        ("false", "coverage-omitted"),
        ("", "none"),
        ("invalid", "none"),
        ("TRUE", "none"),
        ("false\n", "none"),
        ("$(exit 0)", "none"),
    ],
)
def test_actual_fast_gate_requires_success_from_every_declared_job(
    tmp_path: Path, coverage_requested: str, fault: str
) -> None:
    workflow = yaml.safe_load((REPO / ".github/workflows/ci.yml").read_text())
    gate = workflow["jobs"]["ci-gate"]
    required = required_ci_jobs(REPO)
    values = {name: {"result": "success"} for name in required}
    values["own-exemplar-coverage"]["result"] = "skipped" if coverage_requested == "false" else "success"
    if fault == "omitted":
        values.pop("lint")
    elif fault == "extra":
        values["unrelated"] = {"result": "success"}
    elif fault == "coverage-omitted":
        values.pop("own-exemplar-coverage")
    elif fault.startswith("coverage-"):
        values["own-exemplar-coverage"]["result"] = fault.removeprefix("coverage-")
    elif fault not in {"none", "malformed"}:
        values["lint"]["result"] = fault
    step = gate["steps"][0]
    assert step["env"]["COVERAGE_REQUESTED"] == (
        "${{ github.event_name == 'workflow_dispatch' && inputs.coverage-project != '' }}"
    )
    result = subprocess.run(
        ["bash", "-e", "-o", "pipefail", "-c", step["run"]],
        env={
            **os.environ,
            "COVERAGE_REQUESTED": coverage_requested,
            "NEEDS_JSON": "null" if fault == "malformed" else json.dumps(values),
            "GITHUB_STEP_SUMMARY": str(tmp_path / "summary.md"),
        },
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert (result.returncode == 0) == (fault == "none" and coverage_requested in {"true", "false"}), result.stderr


def test_full_hardening_is_explicit_and_keeps_its_complete_aggregate() -> None:
    workflow = yaml.load((REPO / ".github/workflows/hardening.yml").read_text(), Loader=yaml.BaseLoader)
    assert set(workflow["on"]) == {"workflow_dispatch"}
    assert len(required_ci_jobs(REPO, "hardening.yml")) > len(required_ci_jobs(REPO))


def test_external_symlinked_public_project_roots_are_refused(tmp_path: Path) -> None:
    (tmp_path / ".github").mkdir()
    (tmp_path / ".github/project-smoke.json").write_bytes((REPO / ".github/project-smoke.json").read_bytes())
    templates = tmp_path / "projects/templates"
    templates.mkdir(parents=True)
    for project in PUBLIC_PROJECT_NAMES:
        (templates / Path(project).name).symlink_to(REPO / "projects" / project, target_is_directory=True)
    with pytest.raises(ValueError, match="project root is missing or noncanonical"):
        project_smoke_matrix(tmp_path)


def test_search_render_smoke_gets_converter_only_preparation_before_execution() -> None:
    workflow = yaml.safe_load((REPO / ".github/workflows/ci.yml").read_text())
    steps = workflow["jobs"]["test-project"]["steps"]
    preparations = [
        (index, step)
        for index, step in enumerate(steps)
        if step.get("uses") == "./.github/actions/setup-acceptance-documents"
    ]
    assert len(preparations) == 1
    index, preparation = preparations[0]
    assert preparation["if"] == "matrix.project == 'templates/template_search_project'"
    assert preparation["with"]["mode"] == "converter"
    execution = next(i for i, step in enumerate(steps) if step.get("name") == "Run focused behavioral tests")
    assert index < execution


@pytest.mark.parametrize(
    "project",
    [
        "templates/template_sia",
        "active/private",
        "templates/../template_sia",
        "/private/template_sia",
        "template_sia",
        "$(exit 0)",
        "templates/template_sia\nactive/private",
        "",
    ],
)
def test_requested_coverage_checks_public_input_before_environment_setup(project: str) -> None:
    workflow = yaml.safe_load((REPO / ".github/workflows/ci.yml").read_text())
    steps = workflow["jobs"]["own-exemplar-coverage"]["steps"]
    validation = next(i for i, step in enumerate(steps) if step.get("name") == "Validate the requested public project")
    setup = next(
        i for i, step in enumerate(steps) if step.get("name") == "Prepare the own locked development environment"
    )
    assert validation < setup
    result = subprocess.run(
        ["bash", "-e", "-o", "pipefail", "-c", steps[validation]["run"]],
        cwd=REPO,
        env={**os.environ, "COVERAGE_PROJECT": project},
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert (result.returncode == 0) == (project in PUBLIC_PROJECT_NAMES), result.stderr
