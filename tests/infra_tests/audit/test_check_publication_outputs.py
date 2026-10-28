"""Selection, sharding and severity policy of the modular publication gate."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.validation.publication import gate

REPO_ROOT = Path(__file__).resolve().parents[3]


def _result(project: str, *, blocking: tuple[str, ...] = (), review: tuple[str, ...] = ()) -> gate.ProjectGateResult:
    return gate.ProjectGateResult(
        project=project,
        status="fail" if blocking else "pass",
        blocking=blocking,
        review_required=review,
    )


def test_explicit_project_selection_rejects_unknown_names() -> None:
    with pytest.raises(ValueError, match="unknown public project"):
        gate.select_projects(projects=("templates/not_a_project",), all_public=False)


def test_selection_requires_an_explicit_choice() -> None:
    with pytest.raises(ValueError, match="select projects explicitly"):
        gate.select_projects(all_public=False)


def test_whole_roster_is_the_canonical_public_roster() -> None:
    assert gate.select_projects(all_public=True) == tuple(sorted(PUBLIC_PROJECT_NAMES))


def test_changed_selection_keeps_only_projects_with_changes() -> None:
    changed = ("projects/templates/template_madlib/pyproject.toml", "docs/RUN_GUIDE.md")
    assert gate.select_projects(all_public=True, changed=changed) == ("templates/template_madlib",)


def test_shards_partition_the_roster_disjointly_and_completely() -> None:
    roster = tuple(sorted(PUBLIC_PROJECT_NAMES))
    shards = [gate.shard_projects(roster, f"{index}/4") for index in range(4)]
    flattened = [name for shard in shards for name in shard]
    assert sorted(flattened) == list(roster)
    assert len(flattened) == len(set(flattened))
    assert all(shards)


@pytest.mark.parametrize("shard", ["4/4", "0/0", "x/2", "1", "-1/2"])
def test_invalid_shard_specs_are_refused(shard: str) -> None:
    with pytest.raises(ValueError):
        gate.shard_projects(tuple(sorted(PUBLIC_PROJECT_NAMES)), shard)


def test_blocking_mode_ignores_review_required_and_strict_mode_fails() -> None:
    blocking_report = gate.PublicationGateReport(
        mode="blocking",
        results=(_result("templates/a", review=("METHODS.STAGE_PROVENANCE_UNAVAILABLE",)),),
    )
    assert not blocking_report.failed
    assert blocking_report.review_required_count == 1

    strict_report = gate.PublicationGateReport(mode="strict", results=blocking_report.results)
    assert strict_report.failed


def test_errors_fail_every_mode() -> None:
    results = (_result("templates/a", blocking=("PUBLICATION.RENDERED_PROVENANCE_VALIDATION_INPUTS_DRIFT",)),)
    assert gate.PublicationGateReport(mode="blocking", results=results).failed
    assert gate.PublicationGateReport(mode="strict", results=results).failed


def test_report_groups_failures_by_diagnostic_code() -> None:
    report = gate.PublicationGateReport(
        mode="strict",
        results=(
            _result("templates/a", blocking=("PUBLICATION.X",)),
            _result("templates/b", blocking=("PUBLICATION.X",)),
            _result("templates/c"),
        ),
    )
    text = gate.format_gate_report(report)
    assert "PUBLICATION.X: 2 project(s)" in text
    assert "status: fail (2 project(s))" in text
    assert "stage_04_validate.py" in text


def test_receipts_bind_each_project_outcome(tmp_path: Path) -> None:
    report = gate.PublicationGateReport(
        mode="blocking",
        results=(
            _result("templates/a", blocking=("PUBLICATION.X",)),
            _result("templates/b", review=("METHODS.STAGE_PROVENANCE_UNAVAILABLE",)),
        ),
    )
    written = gate.write_receipts(report, tmp_path)
    assert {path.name for path in written} == {"a.json", "b.json"}
    payload = json.loads((tmp_path / "a.json").read_text(encoding="utf-8"))
    assert payload["status"] == "fail"
    assert payload["blocking_codes"] == ["PUBLICATION.X"]
    assert payload["schema_version"] == "template-publication-gate/v1"
    assert json.loads((tmp_path / "b.json").read_text(encoding="utf-8"))["status"] == "pass"


def test_changed_project_paths_observes_real_git_state(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "projects" / "templates" / "template_probe").mkdir(parents=True)
    tracked = repo / "projects" / "templates" / "template_probe" / "pyproject.toml"
    tracked.write_text("[project]\nname='probe'\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(
        ["git", "-c", "user.email=fixture@example.com", "-c", "user.name=Fixture", "commit", "-qm", "fixture"],
        cwd=repo,
        check=True,
    )
    assert gate.changed_project_paths(repo) == ()
    tracked.write_text("[project]\nname='probe'\nversion='2'\n", encoding="utf-8")
    (repo / "projects" / "templates" / "template_probe" / "new.txt").write_text("x\n", encoding="utf-8")
    changed = gate.changed_project_paths(repo)
    assert "projects/templates/template_probe/pyproject.toml" in changed
    assert "projects/templates/template_probe/new.txt" in changed
