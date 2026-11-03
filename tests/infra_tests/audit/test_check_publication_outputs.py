"""Selection, sharding and severity policy of the modular publication gate."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.validation.publication import gate
from infrastructure.validation.publication.models import PublicationAuditReport, PublicationFinding

REPO_ROOT = Path(__file__).resolve().parents[3]


def _result(project: str, *, blocking: tuple[str, ...] = (), review: tuple[str, ...] = ()) -> gate.ProjectGateResult:
    return gate.ProjectGateResult(
        project=project,
        status="fail" if blocking else "pass",
        blocking=blocking,
        review_required=review,
    )


def _audit_process(directory: Path, content: str, original_exit: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            "import sys;sys.stdout.write(sys.stdin.read());raise SystemExit(int(sys.argv[1]))",
            str(original_exit),
        ],
        input=content,
        cwd=directory,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
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


def test_blocking_mode_ignores_review_required_and_strict_mode_fails(tmp_path: Path) -> None:
    blocking_report = gate.PublicationGateReport(
        mode="blocking",
        results=(_result("templates/a", review=("METHODS.STAGE_PROVENANCE_UNAVAILABLE",)),),
    )
    assert not blocking_report.failed
    assert blocking_report.review_required_count == 1

    strict_report = gate.PublicationGateReport(mode="strict", results=blocking_report.results)
    assert strict_report.failed

    payload = PublicationAuditReport(
        "template-publication-audit-v1",
        ("templates/a",),
        (
            PublicationFinding(
                "templates/a",
                "manuscript/example.md",
                "PUBLICATION.REVIEW",
                "warning",
                "review_required",
                "Editorial review",
            ),
        ),
    ).to_dict()
    result = gate._audit_result("templates/a", _audit_process(tmp_path, json.dumps(payload), 0))
    assert result.status == "review" and result.original_exit == 0 and not result.failed
    assert not gate.PublicationGateReport(mode="blocking", results=(result,)).failed
    assert gate.PublicationGateReport(mode="strict", results=(result,)).failed


def test_errors_fail_every_mode(tmp_path: Path) -> None:
    results = (_result("templates/a", blocking=("PUBLICATION.RENDERED_PROVENANCE_VALIDATION_INPUTS_DRIFT",)),)
    assert gate.PublicationGateReport(mode="blocking", results=results).failed
    assert gate.PublicationGateReport(mode="strict", results=results).failed

    # Declared report DATA passes through real children and the production
    # parser; no audit implementation or subprocess dependency is replaced.
    payload = PublicationAuditReport("template-publication-audit-v1", ("templates/a",)).to_dict()
    for original_exit in (0, 42, 130):
        process = _audit_process(tmp_path, json.dumps(payload), original_exit)
        assert process.returncode == original_exit and json.loads(process.stdout)["status"] == "pass"
        observed = gate._audit_result("templates/a", process)
        assert observed.original_exit == original_exit
        assert observed.failed is (original_exit != 0), "passing JSON cannot erase the original child failure"
        for mode in ("blocking", "strict"):
            report = gate.PublicationGateReport(mode=mode, results=(observed,))
            assert report.failed is (original_exit != 0)
            assert ("status: fail" in gate.format_gate_report(report)) is (original_exit != 0)
        gate.write_receipts(report, tmp_path / str(original_exit))
        receipt = json.loads((tmp_path / str(original_exit) / "a.json").read_text())
        assert receipt["original_exit"] == original_exit
        assert receipt["status"] == ("fail" if original_exit else "pass")
        if original_exit:
            assert "PUBLICATION.AUDIT_SUBPROCESS_FAILED" in observed.blocking
            assert str(original_exit) in receipt["diagnostic"]

    invalid = [
        "not JSON",
        "[]",
        "null",
        json.dumps({**payload, "schema_version": "unsupported"}),
        json.dumps({**payload, "projects": ["templates/other"]}),
        json.dumps({**payload, "status": "unknown"}),
        json.dumps({**payload, "status": "fail"}),
        json.dumps({**payload, "status": "review"}),
        json.dumps({**payload, "findings": None}),
        json.dumps({**payload, "findings": [{}]}),
        json.dumps({**payload, "summary": {}}),
        json.dumps({**payload, "summary": {**payload["summary"], "finding_count": False}}),
        json.dumps(payload)[:-1] + ', "status": "pass"}',
    ]
    for content in invalid:
        refused = gate._audit_result("templates/a", _audit_process(tmp_path, content, 0))
        assert refused.failed and refused.original_exit == 0
        assert "PUBLICATION.AUDIT_INVALID_REPORT" in refused.blocking

    # The actual CLI also reaches the same parser and retains its real failure.
    actual = gate._audit_project(tmp_path, "templates/template_code_project", mode="blocking")
    assert actual.failed and actual.original_exit != 0
    assert "PUBLICATION.AUDIT_SUBPROCESS_FAILED" in actual.blocking


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
    assert payload["schema_version"] == "template-publication-gate/v2"
    assert payload["original_exit"] is None
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
