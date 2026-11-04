"""Execute the real rebind workflow decision, commit guard and push guard.

The workflow under test restamps rendered-provenance receipts. Its load-bearing
properties are executable, so this module runs the actual ``run:`` scripts from
``.github/workflows/rebind.yml`` against real Git repositories (and, for the push
guard, a real bare remote):

* the receipt-affecting decision acts only for paths that can move a fingerprint
  and states why it skipped otherwise (loop termination);
* a manual dispatch always acts, and says it was a dispatch;
* the commit guard refuses any path outside the rebind's own ``output/reports/``
  footprint;
* the push guard refuses a dry run, refuses a verification that did not succeed,
  and refuses when ``main`` advanced — and it is the only step that pushes.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
import yaml

_WORKFLOW_PATH = Path(__file__).resolve().parents[3] / ".github/workflows/rebind.yml"

_CHECKOUT = "Check out the commit to rebind with submodules"
_SUBMODULES = "Initialize submodules before any measurement"
_ENVIRONMENT = "Prepare the locked environment"
_DECISION = "Decide whether this run must rebind"
_REBIND = "Rebind rendered receipts and stage the footprint"
_COMMIT = "Commit the rebind"
_VERIFY = "Verify both gates on the committed tree"
_PUSH = "Push the rebind commit to main"
_SUMMARY = "Summarize the decision, the tree and the submodule"

_STRUCTURAL_TERMINATION = (
    "The commit is confined to `projects/templates/*/output/reports/*.json`,\n"
    "          # so the rebind's own push matches no trigger path — structural\n"
    "          # termination, no `[skip ci]`."
)
_NO_PATHS_FILTER = "There is no `paths:` filter, so a skip is always reported rather than silent."


def _workflow() -> dict:
    return yaml.safe_load(_WORKFLOW_PATH.read_text(encoding="utf-8"))


def _job() -> dict:
    return _workflow()["jobs"]["rebind"]


def _steps() -> dict[str, dict]:
    steps = {step["name"]: step for step in _job()["steps"] if "name" in step}
    assert set(steps) == {
        _CHECKOUT,
        _SUBMODULES,
        _ENVIRONMENT,
        _DECISION,
        _REBIND,
        _COMMIT,
        _VERIFY,
        _PUSH,
        _SUMMARY,
    }, sorted(steps)
    return steps


def _trigger() -> dict:
    workflow = _workflow()
    return workflow[True] if True in workflow else workflow["on"]


def _comment_text() -> str:
    """Every line's comment body, joined, so a phrase wrapped across lines matches."""
    parts = []
    for line in _WORKFLOW_PATH.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        parts.append(stripped.lstrip("#").strip() if stripped.startswith("#") else stripped)
    return " ".join(parts)


def _executable(step_run: str) -> str:
    """A step's script with its own comment lines removed."""
    return "\n".join(line for line in step_run.splitlines() if not line.strip().startswith("#"))


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
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


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


def _repository(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _commit_paths(repo, ["README.md"], "initial")
    return repo


def _repository_with_remote(tmp_path: Path) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    remote = tmp_path / "origin.git"
    subprocess.run(
        ["git", "init", "--bare", "-q", str(remote)],
        cwd=tmp_path,
        env=_git_env(),
        check=True,
        timeout=60,
    )
    # A bare `git init` points HEAD at refs/heads/master, which would make every
    # clone of it arrive with no branch checked out.
    _git(tmp_path, "--git-dir", str(remote), "symbolic-ref", "HEAD", "refs/heads/main")
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "remote", "add", "origin", str(remote))
    _commit_paths(repo, ["README.md"], "initial")
    _git(repo, "push", "-q", "origin", "main")
    return repo, remote


def _advance_remote(tmp_path: Path, remote: Path) -> str:
    """Push a further commit to the bare remote's main, as a merged PR would."""
    other = tmp_path / "other"
    _git(tmp_path, "clone", "-q", str(remote), str(other))
    _commit_paths(other, ["other.md"], "another merge")
    _git(other, "push", "-q", "origin", "main")
    return _git(other, "rev-parse", "HEAD").strip()


def _remote_main(remote: Path) -> str:
    return _git(remote, "rev-parse", "refs/heads/main").strip()


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


def _push(
    repo: Path,
    tmp_path: Path,
    *,
    dry_run: str | None = None,
    verification: str | None = "success",
) -> tuple[subprocess.CompletedProcess[str], dict[str, str]]:
    env: dict[str, str] = {}
    if dry_run is not None:
        env["DRY_RUN"] = dry_run
    if verification is not None:
        env["VERIFICATION_OUTCOME"] = verification
    return _run_step(_steps()[_PUSH], repo, env, tmp_path)


def _decide(
    repo: Path, before: str, after: str, tmp_path: Path
) -> tuple[subprocess.CompletedProcess[str], dict[str, str]]:
    return _run_step(
        _steps()[_DECISION],
        repo,
        {"EVENT_NAME": "push", "PUSH_BEFORE": before, "PUSH_AFTER": after},
        tmp_path,
    )


def _dispatch(repo: Path, tmp_path: Path) -> tuple[subprocess.CompletedProcess[str], dict[str, str]]:
    return _run_step(_steps()[_DECISION], repo, {"EVENT_NAME": "workflow_dispatch"}, tmp_path)


def _commit(repo: Path, tmp_path: Path) -> tuple[subprocess.CompletedProcess[str], dict[str, str]]:
    return _run_step(
        _steps()[_COMMIT],
        repo,
        {
            "TRIGGER_REASON": "1 receipt-affecting path(s) in deadbeef0000..cafebabe0000",
            "TRIGGER_RANGE": "deadbeef0000..cafebabe0000",
            "SUBMODULE_KMYTH": "cb23c6d94423cbe4f5ef0caf23594d1095ddde79",
            "SOURCE_DATE_EPOCH": "1793806881",
        },
        tmp_path,
    )


def _rebind_commit(repo: Path, tmp_path: Path) -> str:
    """Run the commit step over a staged receipt change, as the job does."""
    _write(repo, "projects/templates/template_code_project/output/reports/rendered_provenance.json")
    result, recorded = _commit(repo, tmp_path)
    assert result.returncode == 0, result.stderr
    assert recorded["committed"] == "true"
    return recorded["commit"]


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
        # A skip states why, in the log and in the run summary.
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


def test_manual_dispatch_always_acts_and_reports_the_tip(tmp_path: Path) -> None:
    """A dispatch assumes an operator asked for the rebind; it still reports facts."""
    repo = _repository(tmp_path)
    _commit_paths(repo, ["projects/templates/template_code_project/uv.lock"], "lock bump")

    result, recorded = _dispatch(repo, tmp_path)

    assert result.returncode == 0, result.stderr
    assert recorded["act"] == "true"
    assert recorded["reason"].startswith("manual dispatch on ")
    assert recorded["affecting"] == "1"
    assert "informational: " in result.stdout
    assert "1 of them receipt-affecting" in result.stdout


def test_workflow_is_dispatch_only_until_a_push_credential_exists() -> None:
    trigger = _trigger()
    assert set(trigger) == {"workflow_dispatch"}, trigger
    assert trigger["workflow_dispatch"]["inputs"]["dry_run"] == {
        "description": "Run the rebind, the commit and both gates, but do not push",
        "type": "boolean",
        "default": True,
    }
    assert _workflow()["permissions"] == {"contents": "write"}
    assert _workflow()["concurrency"] == {
        "group": "rebind-rendered-provenance",
        "cancel-in-progress": False,
    }
    text = _WORKFLOW_PATH.read_text(encoding="utf-8")
    # The activation, the reason it is not active, and the external contract it
    # waits on are all recorded in the file itself.
    assert "# WHY THIS IS DISPATCH-ONLY TODAY" in text
    assert "#   push:" in text
    assert "#     branches: [main]" in text
    assert "no matter how thoroughly the job has verified it" in _comment_text()
    for step in _job()["steps"]:
        assert "[skip ci]" not in _executable(step.get("run", "")), step["name"]


def test_checkout_initializes_the_submodule_before_any_measurement() -> None:
    steps = _steps()
    checkout = next(step for step in _job()["steps"] if step.get("uses", "").startswith("actions/checkout@"))
    assert checkout["with"]["submodules"] == "recursive"
    assert checkout["with"]["fetch-depth"] == 0
    submodules = steps[_SUBMODULES]
    assert submodules["id"] == "submodules"
    assert "git submodule update --init --recursive" in submodules["run"]
    assert submodules["run"].index("git submodule update") < submodules["run"].index("rev-parse HEAD")
    names = [step["name"] for step in _job()["steps"] if "name" in step]
    assert names.index(_SUBMODULES) < names.index(_DECISION)


def test_the_commit_is_verified_after_it_exists_and_pushed_last() -> None:
    """rebind → commit → verify the committed tree → push; nothing writes in between."""
    steps = _steps()
    names = [step["name"] for step in _job()["steps"] if "name" in step]
    assert (
        names.index(_REBIND) < names.index(_COMMIT) < names.index(_VERIFY) < names.index(_PUSH) < names.index(_SUMMARY)
    )
    assert names[names.index(_REBIND) + 1 : names.index(_VERIFY)] == [_COMMIT]
    assert steps[_REBIND]["if"] == steps[_COMMIT]["if"] == "steps.decide.outputs.act == 'true'"
    assert steps[_VERIFY]["if"] == "steps.commit.outputs.committed == 'true'"
    assert steps[_PUSH]["if"] == "steps.commit.outputs.committed == 'true' && inputs.dry_run != true"

    rebind = steps[_REBIND]["run"]
    assert "--rebind --jobs 4" in rebind
    assert "--all-public" in rebind
    assert "SOURCE_DATE_EPOCH" in rebind
    assert 'epoch=$(git show -s --format=%ct "$target")' in rebind
    assert "date +%s" not in rebind
    assert 'if [ "$tip" != "$main_tip" ]' in rebind  # a dispatch on a branch refuses

    verify = steps[_VERIFY]["run"]
    assert "scripts/audit/check_publication_outputs.py" in verify
    assert "--all-public --strict --jobs 4" in verify
    assert "publication-audit" in verify
    assert "--strict --rendered" in verify
    assert "blocking=0, review_required=0" in verify
    # Only the push step may push, and it is not the verification step.
    assert "git push" not in verify
    assert "git push origin HEAD:main" in steps[_PUSH]["run"]
    assert "--force" not in steps[_PUSH]["run"]


def test_commit_refuses_paths_outside_the_rebind_footprint(tmp_path: Path) -> None:
    repo = _repository(tmp_path)
    head_before = _git(repo, "rev-parse", "HEAD").strip()
    _write(repo, "projects/templates/template_code_project/output/reports/rendered_provenance.json")
    _write(repo, "docs/maintenance/release-boundary.md")

    result, recorded = _commit(repo, tmp_path)

    assert result.returncode != 0, result.stdout
    assert "outside its output/reports footprint" in result.stdout + result.stderr
    assert "docs/maintenance/release-boundary.md" in result.stdout + result.stderr
    assert "committed" not in recorded
    assert _git(repo, "rev-parse", "HEAD").strip() == head_before


def test_commit_records_the_tree_when_only_receipts_changed(tmp_path: Path) -> None:
    repo = _repository(tmp_path)
    _write(repo, "projects/templates/template_code_project/output/reports/rendered_provenance.json")
    _write(repo, "projects/templates/template_code_project/output/reports/validation_report.json")

    result, recorded = _commit(repo, tmp_path)

    assert result.returncode == 0, result.stderr
    assert recorded["committed"] == "true"
    assert recorded["commit"] == _git(repo, "rev-parse", "HEAD").strip()
    assert recorded["tree"] == _git(repo, "rev-parse", "HEAD^{tree}").strip()
    message = _git(repo, "log", "-1", "--format=%B")
    assert "rebind rendered receipts" in message
    assert "publication-audit --all-public --strict --rendered" in message
    assert "1793806881" in message
    assert "cb23c6d94423cbe4f5ef0caf23594d1095ddde79" in message
    assert "pushes only if both pass" in message
    changed = _git(repo, "diff", "--name-only", "HEAD^", "HEAD").split()
    assert sorted(changed) == [
        "projects/templates/template_code_project/output/reports/rendered_provenance.json",
        "projects/templates/template_code_project/output/reports/validation_report.json",
    ]


def test_commit_reports_no_change_instead_of_an_empty_commit(tmp_path: Path) -> None:
    repo = _repository(tmp_path)
    head_before = _git(repo, "rev-parse", "HEAD").strip()

    result, recorded = _commit(repo, tmp_path)

    assert result.returncode == 0, result.stderr
    assert recorded["committed"] == "false"
    assert _git(repo, "rev-parse", "HEAD").strip() == head_before


def test_dry_run_never_pushes_and_never_touches_the_remote(tmp_path: Path) -> None:
    """No remote is configured here: reaching for one would fail, not pass."""
    repo, _ = _repository_with_remote(tmp_path)
    _git(repo, "remote", "remove", "origin")
    _rebind_commit(repo, tmp_path)

    result, recorded = _push(repo, tmp_path, dry_run="true")

    assert result.returncode == 0, result.stderr
    assert "dry run" in result.stdout
    assert recorded["pushed"] == "false"


def test_push_refuses_a_verification_that_did_not_succeed(tmp_path: Path) -> None:
    repo, remote = _repository_with_remote(tmp_path)
    head = _rebind_commit(repo, tmp_path)
    remote_before = _remote_main(remote)

    for verification in ("failure", "skipped", "cancelled", None):
        result, recorded = _push(repo, tmp_path, dry_run="false", verification=verification)
        assert result.returncode != 0, result.stdout
        assert "refusing to push" in result.stdout + result.stderr
        assert "pushed" not in recorded
        assert _remote_main(remote) == remote_before
        assert head == _git(repo, "rev-parse", "HEAD").strip()


def test_push_succeeds_when_the_tree_is_verified_and_main_has_not_moved(tmp_path: Path) -> None:
    repo, remote = _repository_with_remote(tmp_path)
    head = _rebind_commit(repo, tmp_path)

    result, recorded = _push(repo, tmp_path, dry_run="false", verification="success")

    assert result.returncode == 0, result.stderr
    assert recorded["pushed"] == "true"
    assert _remote_main(remote) == head


def test_push_defaults_to_pushing_for_a_push_event(tmp_path: Path) -> None:
    """A push event has no ``inputs.dry_run``; the empty value must not read as dry."""
    repo, remote = _repository_with_remote(tmp_path)
    head = _rebind_commit(repo, tmp_path)

    result, recorded = _push(repo, tmp_path, dry_run=None, verification="success")

    assert result.returncode == 0, result.stderr
    assert recorded["pushed"] == "true"
    assert _remote_main(remote) == head


def test_push_refuses_when_main_advanced_during_the_rebind(tmp_path: Path) -> None:
    repo, remote = _repository_with_remote(tmp_path)
    _rebind_commit(repo, tmp_path)
    moved = _advance_remote(tmp_path, remote)

    result, recorded = _push(repo, tmp_path, dry_run="false", verification="success")

    assert result.returncode != 0, result.stdout
    assert "main advanced" in result.stdout + result.stderr
    assert "pushed" not in recorded
    assert _remote_main(remote) == moved
    assert _git(repo, "rev-parse", "origin/main").strip() != _git(repo, "rev-parse", "HEAD").strip()


def test_summary_reports_the_tree_and_the_submodule() -> None:
    summary = _steps()[_SUMMARY]
    assert summary["if"] == "always()"
    body = summary["run"]
    assert "Rebind target tree" in body and "Submodule kmyth" in body
    assert "Rebind commit" in body
    assert "Dry run: the rebind commit was built and verified" in body
    assert '>> "$GITHUB_STEP_SUMMARY"' in body


def test_the_two_crux_sentences_are_in_the_file() -> None:
    """Both are recorded verbatim: they are the design's stated standards."""
    text = _WORKFLOW_PATH.read_text(encoding="utf-8")
    assert _NO_PATHS_FILTER in text
    assert _STRUCTURAL_TERMINATION in text
