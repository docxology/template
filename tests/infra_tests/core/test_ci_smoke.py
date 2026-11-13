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


def test_every_public_project_has_confined_nonempty_smoke_selection() -> None:
    matrix = project_smoke_matrix(REPO)
    assert {row["project"] for row in matrix["include"]} == set(PUBLIC_PROJECT_NAMES)
    assert len(matrix["include"]) == len(PUBLIC_PROJECT_NAMES)


@pytest.mark.parametrize("fault", ["missing-project", "extra-project", "empty-selection", "escape", "missing-test"])
def test_invalid_smoke_selection_fails_before_running_a_project(tmp_path: Path, fault: str) -> None:
    selection = json.loads((REPO / ".github/project-smoke.json").read_text())
    (tmp_path / ".github").mkdir()
    manifest = tmp_path / ".github/project-smoke.json"
    manifest.write_text(json.dumps(selection))
    for project, paths in selection.items():
        for relative in paths:
            path = tmp_path / "projects" / project / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
    assert {row["project"] for row in project_smoke_matrix(tmp_path)["include"]} == set(PUBLIC_PROJECT_NAMES)
    first = next(iter(selection))
    if fault == "missing-project":
        selection.pop(first)
    elif fault == "extra-project":
        selection["active/private"] = ["tests/test_private.py"]
    elif fault == "empty-selection":
        selection[first] = []
    elif fault == "escape":
        (tmp_path / "projects" / first).parent.joinpath("private.py").touch()
        selection[first] = ["tests/../../private.py"]
    else:
        selection[first] = ["tests/nonexistent.py"]
    manifest.write_text(json.dumps(selection))
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
    result = subprocess.run(
        ["bash", "-e", "-o", "pipefail", "-c", step["run"]],
        env={
            **os.environ,
            "COVERAGE_REQUESTED": coverage_requested,
            "DOCS_ONLY": "false",
            "NEEDS_JSON": "null" if fault == "malformed" else json.dumps(values),
            "GITHUB_STEP_SUMMARY": str(tmp_path / "summary.md"),
        },
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert (result.returncode == 0) == (fault == "none" and coverage_requested in {"true", "false"}), result.stderr


def test_external_symlinked_public_project_roots_are_refused(tmp_path: Path) -> None:
    (tmp_path / ".github").mkdir()
    (tmp_path / ".github/project-smoke.json").write_bytes((REPO / ".github/project-smoke.json").read_bytes())
    templates = tmp_path / "projects/templates"
    templates.mkdir(parents=True)
    for project in PUBLIC_PROJECT_NAMES:
        (templates / Path(project).name).symlink_to(REPO / "projects" / project, target_is_directory=True)
    with pytest.raises(ValueError, match="project root is missing or noncanonical"):
        project_smoke_matrix(tmp_path)


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
def test_requested_coverage_refuses_nonpublic_scope_before_measurement(project: str, tmp_path: Path) -> None:
    reusable = yaml.load((REPO / ".github/workflows/exemplar-coverage.yml").read_text(), Loader=yaml.BaseLoader)
    job = reusable["jobs"]["own-exemplar-coverage"]
    steps = job["steps"]
    validation = next(i for i, step in enumerate(steps) if step.get("name") == "Validate the requested public project")
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
    manual = yaml.safe_load((REPO / ".github/workflows/public-exemplar-coverage.yml").read_text())
    selector = manual["jobs"]["select"]["steps"][-1]["run"]
    output = tmp_path / "github-output"
    selected = subprocess.run(
        ["bash", "-e", "-o", "pipefail", "-c", selector],
        cwd=REPO,
        env={**os.environ, "COVERAGE_PROJECT": project, "GITHUB_OUTPUT": str(output)},
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert (selected.returncode == 0) == (not project or project in PUBLIC_PROJECT_NAMES), selected.stderr
    if selected.returncode == 0:
        rows = json.loads(output.read_text().removeprefix("matrix="))["include"]
        assert [row["project"] for row in rows] == ([project] if project else list(PUBLIC_PROJECT_NAMES))
        assert len({row["name"] for row in rows}) == len(rows)
        assert all("/" not in row["name"] for row in rows)


@pytest.mark.parametrize("projects", [(), ("templates/template_code_project",) * 2, ("working/private",)])
def test_executable_smoke_subset_never_accepts_empty_duplicate_or_private_scopes(projects: tuple[str, ...]) -> None:
    with pytest.raises(ValueError):
        project_smoke_matrix(REPO, projects)
    assert project_smoke_matrix(REPO, ("templates/template_code_project",)) == {
        "include": [{"project": "templates/template_code_project"}]
    }


@pytest.mark.parametrize(
    "docs_only,project,contract,passes",
    [
        ("true", "skipped", "success", True),
        ("false", "success", "success", True),
        ("true", "success", "success", False),
        ("false", "skipped", "success", False),
        ("true", "skipped", "skipped", False),
        ("true", "skipped", "failure", False),
        ("", "success", "success", False),
        ("TRUE", "skipped", "success", False),
    ],
)
def test_fast_gate_admits_only_the_declared_documentation_skip(
    tmp_path: Path, docs_only: str, project: str, contract: str, passes: bool
) -> None:
    workflow = yaml.safe_load((REPO / ".github/workflows/ci.yml").read_text())
    gate = workflow["jobs"]["ci-gate"]
    values = {name: {"result": "success"} for name in gate["needs"]}
    values["test-project"]["result"] = project
    values["test-contract"]["result"] = contract
    values["own-exemplar-coverage"]["result"] = "skipped"
    step = gate["steps"][0]
    assert step["env"]["DOCS_ONLY"] == "${{ needs.detect-projects.outputs.docs_only }}"
    result = subprocess.run(
        ["bash", "-e", "-o", "pipefail", "-c", step["run"]],
        env={
            **os.environ,
            "COVERAGE_REQUESTED": "false",
            "DOCS_ONLY": docs_only,
            "NEEDS_JSON": json.dumps(values),
            "GITHUB_STEP_SUMMARY": str(tmp_path / "summary.md"),
        },
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert (result.returncode == 0) is passes, result.stderr
