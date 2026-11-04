"""Execute the real rebind workflow decision and commit guard.

The workflow under test restamps rendered-provenance receipts on ``main``. Its
two load-bearing properties are executable, so this module runs the actual
``run:`` scripts from ``.github/workflows/rebind.yml`` against real Git
repositories:

* the receipt-affecting decision must act only for paths that can move a
  fingerprint, and must state why it skipped otherwise (loop termination);
* the commit guard must refuse to commit when verification did not succeed, and
  must refuse any path outside the rebind's own ``output/reports/`` footprint.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
import yaml

_WORKFLOW_PATH = Path(__file__).resolve().parents[3] / ".github/workflows/rebind.yml"

_SUBMODULES = "Initialize submodules before any measurement"
_DECISION = "Decide whether this push invalidates rendered receipts"
_REBIND = "Rebind rendered receipts and stage the footprint"
_VERIFY = "Verify both gates on the tree the commit will contain"
_COMMIT = "Commit the rebind"
_PUSH = "Push the rebind commit to main"
_SUMMARY = "Summarize the decision, the tree and the submodule"


def _workflow() -> dict:
    return yaml.safe_load(_WORKFLOW_PATH.read_text(encoding="utf-8"))


def _job() -> dict:
    return _workflow()["jobs"]["rebind"]


def _steps() -> dict[str, dict]:
    steps = {step["name"]: step for step in _job()["steps"] if "name" in step}
    assert set(steps) == {_SUBMODULES, _DECISION, _REBIND, _VERIFY, _COMMIT, _PUSH, _SUMMARY} | {
        "Check out the pushed commit with submodules",
        "Prepare the locked environment",
    }, sorted(steps)
    return steps


def _git_env() -> dict[str, str]:
    return {
        "PATH": os.environ.get("PATH", os.defpath),
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_AUTHOR_NAME": "Rebind Workflow Test",
        "GIT_AUTHOR_EMAIL": "rebind-workflow-test@example.invalid",
        "GIT_COMMITTER_NAME": "Rebind Workflow Test",
        "GIT_COMMITTER_EMAIL": "rebind-workflow-test@example.invalid",
    }


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        env=_git_env(),
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def _repository(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _commit_paths(repo, ["README.md"], "initial")
    return repo


def _commit_paths(repo: Path, paths: list[str], message: str) -> str:
    for path in paths:
        # Content is the commit message, never the bare path: a line naming
        # `.gitignore` inside `.gitignore` would ignore the file itself.
        _write(repo, path, f"{message}\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", message)
    return _git(repo, "rev-parse", "HEAD").strip()


def _write(repo: Path, path: str, text: str = "changed\n", *, tracked: bool = True) -> None:
    """Write a path and stage it, so it participates as a tracked modification."""
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    if tracked:
        _git(repo, "add", "--", path)


def _run_step(
    step: dict,
    repo: Path,
    env: dict[str, str],
    tmp_path: Path,
) -> tuple[subprocess.CompletedProcess[str], dict[str, str]]:
    assert step["shell"] == "bash", step["name"]
    output = tmp_path / f"{step['name'].replace(' ', '-')}.output"
    output.write_text("", encoding="utf-8")
    result = subprocess.run(
        ["bash", "-e", "-o", "pipefail", "-c", step["run"]],
        cwd=repo,
        env={**_git_env(), "GITHUB_OUTPUT": str(output), "RUNNER_TEMP": str(tmp_path), **env},
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    recorded = dict(line.split("=", 1) for line in output.read_text(encoding="utf-8").splitlines() if "=" in line)
    return result, recorded


def _decide(
    repo: Path, before: str, after: str, tmp_path: Path
) -> tuple[subprocess.CompletedProcess[str], dict[str, str]]:
    return _run_step(
        _steps()[_DECISION],
        repo,
        {"PUSH_BEFORE": before, "PUSH_AFTER": after},
        tmp_path,
    )


def _commit(
    repo: Path,
    verification: str | None,
    tmp_path: Path,
) -> tuple[subprocess.CompletedProcess[str], dict[str, str]]:
    env = {
        "TRIGGER_REASON": "1 receipt-affecting path(s) in deadbeef0000..cafebabe0000",
        "TRIGGER_RANGE": "deadbeef0000..cafebabe0000",
        "SUBMODULE_KMYTH": "cb23c6d94423cbe4f5ef0caf23594d1095ddde79",
        "GITHUB_SHA": "cafebabe0000" * 4,
        "SOURCE_DATE_EPOCH": "1793806881",
    }
    if verification is not None:
        env["VERIFICATION_OUTCOME"] = verification
    return _run_step(_steps()[_COMMIT], repo, env, tmp_path)


@pytest.mark.parametrize(
    "path,affecting",
    [
        # Roots and shared implementation: one change invalidates every receipt.
        ("pyproject.toml", True),
        ("uv.lock", True),
        (".gitignore", True),
        (".python-version", True),
        ("infrastructure/validation/publication/gate.py", True),
        ("infrastructure/rendering/latex_fragments/preamble.tex", True),
        ("infrastructure/steganography/kmyth", True),
        ("scripts/audit/check_publication_outputs.py", True),
        ("scripts/maintenance/refresh_rendered_provenance.py", True),
        # Exemplar trees: config, source and manuscript inputs are all bound.
        ("projects/templates/template_code_project/uv.lock", True),
        ("projects/templates/template_code_project/pyproject.toml", True),
        ("projects/templates/template_code_project/manuscript/config.yaml", True),
        ("projects/templates/template_code_project/manuscript/01_introduction.md", True),
        ("projects/templates/template_code_project/src/template_code_project/core.py", True),
        # The rebind's own footprint: acting here would loop forever.
        ("projects/templates/template_code_project/output/reports/rendered_provenance.json", False),
        ("projects/templates/template_code_project/output/reports/validation_report.json", False),
        ("projects/templates/template_code_project/output/reports/artifact_manifest.json", False),
        ("projects/templates/template_code_project/output/pdf/template_code_project_combined.pdf", False),
        # Snapshot-excluded documentation and every unrelated surface.
        ("projects/templates/template_code_project/AGENTS.md", False),
        ("projects/templates/template_code_project/README.md", False),
        ("README.md", False),
        ("docs/maintenance/release-boundary.md", False),
        ("tests/infra_tests/config/test_rebind_workflow.py", False),
        (".github/workflows/rebind.yml", False),
        ("fonds/templates/example/manifest.yaml", False),
    ],
)
def test_decision_acts_only_for_receipt_affecting_paths(path: str, affecting: bool, tmp_path: Path) -> None:
    repo = _repository(tmp_path)
    before = _git(repo, "rev-parse", "HEAD").strip()
    after = _commit_paths(repo, [path], f"touch {path}")

    result, recorded = _decide(repo, before, after, tmp_path)

    assert result.returncode == 0, result.stderr
    assert recorded["act"] == ("true" if affecting else "false"), result.stdout
    assert recorded["affecting"] == ("1" if affecting else "0"), recorded
    assert recorded["changed"] == "1"
    if affecting:
        assert path in result.stdout
        assert recorded["reason"].startswith("1 receipt-affecting path(s)")
    else:
        # Requirement: a skip states why, in the log and in the run summary.
        assert "skip: no receipt-affecting path" in result.stdout
        assert "1 changed path(s)" in recorded["reason"]
        assert path in result.stdout


def test_decision_treats_the_whole_rebind_footprint_as_a_skip(tmp_path: Path) -> None:
    """The second run after a rebind must be a no-op, or the loop never ends."""
    repo = _repository(tmp_path)
    before = _git(repo, "rev-parse", "HEAD").strip()
    footprint = [
        f"projects/templates/template_{name}/output/reports/{report}"
        for name in ("code_project", "prose_project", "formal")
        for report in ("rendered_provenance.json", "validation_report.json")
    ]
    after = _commit_paths(repo, footprint, "rebind rendered receipts")

    result, recorded = _decide(repo, before, after, tmp_path)

    assert result.returncode == 0, result.stderr
    assert recorded["act"] == "false"
    assert recorded["changed"] == str(len(footprint))
    assert recorded["affecting"] == "0"
    assert "skip: no receipt-affecting path" in result.stdout


def test_decision_survives_a_missing_before_commit(tmp_path: Path) -> None:
    """A force-push or an unreachable ``before`` must still classify the tip."""
    repo = _repository(tmp_path)
    after = _commit_paths(repo, ["projects/templates/template_code_project/uv.lock"], "lock bump")

    result, recorded = _decide(repo, "", after, tmp_path)

    assert result.returncode == 0, result.stderr
    assert recorded["act"] == "true"
    assert "no usable before-commit" in recorded["range"]


def test_workflow_trigger_and_privileges() -> None:
    workflow = _workflow()
    push = workflow[True]["push"] if True in workflow else workflow["on"]["push"]
    assert push == {"branches": ["main"]}, push
    # A paths: filter would silently skip the run; the job decides and reports.
    assert "paths" not in push and "paths-ignore" not in push
    assert workflow["permissions"] == {"contents": "write"}
    assert workflow["concurrency"] == {
        "group": "rebind-rendered-provenance",
        "cancel-in-progress": False,
    }
    # No suppression marker anywhere in the executable scripts: termination is
    # structural (the decision above), and the rebind commit still needs CI.
    for step in _job()["steps"]:
        assert "[skip ci]" not in step.get("run", ""), step["name"]


def test_checkout_initializes_the_submodule_before_any_measurement() -> None:
    steps = _steps()
    checkout = next(step for step in _job()["steps"] if step.get("uses", "").startswith("actions/checkout@"))
    assert checkout["with"]["submodules"] == "recursive"
    assert checkout["with"]["fetch-depth"] == 0
    submodules = steps[_SUBMODULES]
    assert submodules["id"] == "submodules"
    assert "git submodule update --init --recursive" in submodules["run"]
    assert submodules["run"].index("git submodule update") < submodules["run"].index("rev-parse HEAD")
    step_names = [step["name"] for step in _job()["steps"] if "name" in step]
    assert step_names.index(_SUBMODULES) < step_names.index(_DECISION)


def test_rebind_is_the_last_change_and_the_gates_run_before_the_commit() -> None:
    steps = _steps()
    step_names = [step["name"] for step in _job()["steps"] if "name" in step]
    assert step_names.index(_REBIND) < step_names.index(_VERIFY) < step_names.index(_COMMIT) < step_names.index(_PUSH)
    assert step_names[step_names.index(_REBIND) + 1 : step_names.index(_COMMIT)] == [_VERIFY]

    rebind = steps[_REBIND]["run"]
    assert "--rebind --jobs 4" in rebind
    assert "--all-public" in rebind
    assert "SOURCE_DATE_EPOCH" in rebind
    assert "git config " not in rebind  # the rebind step changes no identity
    assert steps[_REBIND]["if"] == steps[_VERIFY]["if"] == steps[_COMMIT]["if"] == "steps.decide.outputs.act == 'true'"

    verify = steps[_VERIFY]["run"]
    assert "scripts/audit/check_publication_outputs.py" in verify
    assert "--all-public --strict --jobs 4" in verify
    assert "publication-audit" in verify
    assert "--strict --rendered" in verify
    assert "blocking=0, review_required=0" in verify


def test_pinned_epoch_comes_from_the_triggering_commit() -> None:
    rebind = _steps()[_REBIND]["run"]
    assert 'epoch=$(git show -s --format=%ct "$target")' in rebind
    assert 'export SOURCE_DATE_EPOCH="$epoch"' in rebind
    assert "date +%s" not in rebind


def test_commit_refuses_a_failed_verification(tmp_path: Path) -> None:
    repo = _repository(tmp_path)
    head_before = _git(repo, "rev-parse", "HEAD").strip()
    _write(repo, "projects/templates/template_code_project/output/reports/rendered_provenance.json")

    for verification in ("failure", "skipped", "cancelled", None):
        result, recorded = _commit(repo, verification, tmp_path)
        assert result.returncode != 0, result.stdout
        assert "refusing to commit" in result.stdout + result.stderr
        assert "committed" not in recorded
        assert _git(repo, "rev-parse", "HEAD").strip() == head_before


def test_commit_refuses_paths_outside_the_rebind_footprint(tmp_path: Path) -> None:
    repo = _repository(tmp_path)
    head_before = _git(repo, "rev-parse", "HEAD").strip()
    _write(repo, "projects/templates/template_code_project/output/reports/rendered_provenance.json")
    _write(repo, "docs/maintenance/release-boundary.md")

    result, recorded = _commit(repo, "success", tmp_path)

    assert result.returncode != 0, result.stdout
    assert "outside its output/reports footprint" in result.stdout + result.stderr
    assert "docs/maintenance/release-boundary.md" in result.stdout + result.stderr
    assert "committed" not in recorded
    assert _git(repo, "rev-parse", "HEAD").strip() == head_before


def test_commit_records_the_verified_tree_when_only_receipts_changed(tmp_path: Path) -> None:
    repo = _repository(tmp_path)
    _write(repo, "projects/templates/template_code_project/output/reports/rendered_provenance.json")
    _write(repo, "projects/templates/template_code_project/output/reports/validation_report.json")

    result, recorded = _commit(repo, "success", tmp_path)

    assert result.returncode == 0, result.stderr
    assert recorded["committed"] == "true"
    assert recorded["commit"] == _git(repo, "rev-parse", "HEAD").strip()
    assert recorded["tree"] == _git(repo, "rev-parse", "HEAD^{tree}").strip()
    message = _git(repo, "log", "-1", "--format=%B")
    assert "rebind rendered receipts" in message
    assert "blocking=0, review_required=0" in message
    assert "publication-audit --all-public --strict --rendered" in message
    assert "1793806881" in message
    assert "cb23c6d94423cbe4f5ef0caf23594d1095ddde79" in message
    changed = _git(repo, "diff", "--name-only", "HEAD^", "HEAD").split()
    assert sorted(changed) == [
        "projects/templates/template_code_project/output/reports/rendered_provenance.json",
        "projects/templates/template_code_project/output/reports/validation_report.json",
    ]


def test_commit_reports_no_change_instead_of_an_empty_commit(tmp_path: Path) -> None:
    repo = _repository(tmp_path)
    head_before = _git(repo, "rev-parse", "HEAD").strip()

    result, recorded = _commit(repo, "success", tmp_path)

    assert result.returncode == 0, result.stderr
    assert recorded["committed"] == "false"
    assert _git(repo, "rev-parse", "HEAD").strip() == head_before


def test_push_is_gated_and_never_forces_or_retries() -> None:
    push = _steps()[_PUSH]
    assert push["if"] == "steps.commit.outputs.committed == 'true'"
    assert "git push origin HEAD:main" in push["run"]
    assert "--force" not in push["run"]
    assert "--retry" not in push["run"]
    # A moved main is refused, not raced or retried.
    assert "git fetch --no-tags origin main" in push["run"]
    assert "not pushing" in push["run"]


def test_summary_reports_the_tree_and_the_submodule() -> None:
    summary = _steps()[_SUMMARY]
    assert summary["if"] == "always()"
    body = summary["run"]
    assert "Pushed tree" in body and "Submodule kmyth" in body
    assert "Rebind commit" in body
    assert '>> "$GITHUB_STEP_SUMMARY"' in body
