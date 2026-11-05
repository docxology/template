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
  and refuses when ``main`` advanced — and it is the only step that pushes;
* the fingerprint report prints the measured stage and config digests beside the
  stamped ones, so a checkout shape that differs from a developer's is visible.
"""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
from pathlib import Path

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parents[3]
_WORKFLOW_PATH = _REPO_ROOT / ".github/workflows/rebind.yml"

_CHECKOUT = "Check out the commit to rebind with submodules"
_SUBMODULES = "Initialize submodules before any measurement"
_ENVIRONMENT = "Prepare the locked environment"
_DECISION = "Decide whether this run must rebind"
_REBIND = "Rebind rendered receipts and stage the footprint"
_COMMIT = "Commit the rebind"
_VERIFY = "Verify both gates on the committed tree"
_CAPTURE = "Capture the verified rebind review patch"
_REVIEW_UPLOAD = "Retain the verified rebind review patch"
_DIAGNOSTIC_UPLOAD = "Retain original rebind diagnostics"
_FINGERPRINTS = "Report the measured fingerprints of one exemplar"
_PUSH = "Push the rebind commit to main"
_SUMMARY = "Summarize the decision, the tree and the submodule"

_STRUCTURAL_TERMINATION = (
    "The commit is confined to `projects/templates/*/output/reports/*.json`,\n"
    "          # so the rebind's own push matches no trigger path — structural\n"
    "          # termination, no `[skip ci]`."
)
_NO_PATHS_FILTER = "There is no `paths:` filter, so a skip is always reported rather than silent."

_FINGERPRINT_LINE = re.compile(
    r"^(stage|config) sha256 (?P<measured>[0-9a-f]{64}) \((?P<measured_files>\d+) files\); "
    r"receipt (?P<stamped>[0-9a-f]{64}) \((?P<stamped_files>\d+) files\); current (True|False)$"
)


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
        _CAPTURE,
        _REVIEW_UPLOAD,
        _DIAGNOSTIC_UPLOAD,
        _FINGERPRINTS,
        _PUSH,
        _SUMMARY,
    }, sorted(steps)
    return steps


def _refresh_steps() -> dict[str, dict]:
    return {step["name"]: step for step in _workflow()["jobs"]["refresh-active-inference"]["steps"] if "name" in step}


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
        env={
            **_git_env(),
            "GITHUB_OUTPUT": str(output),
            "GITHUB_ENV": str(tmp_path / "job.env"),
            "RUNNER_TEMP": str(tmp_path),
            **env,
        },
        capture_output=True,
        text=True,
        timeout=120,
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
    # The labels name a commit, never the string `HEAD`.
    assert re.fullmatch(r"manual dispatch on [0-9a-f]{12}", recorded["reason"]), recorded["reason"]
    assert re.fullmatch(r"[0-9a-f]{12}", recorded["range"]), recorded["range"]
    assert recorded["affecting"] == "1"
    assert re.search(r"informational: [0-9a-f]{12} touched 1 path\(s\), 1 of them receipt-affecting", result.stdout), (
        result.stdout
    )


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


def test_active_refresh_is_explicit_read_only_artifact_preparation() -> None:
    workflow = _workflow()
    assert _trigger()["workflow_dispatch"]["inputs"]["refresh_active_inference"] == {
        "description": "Regenerate only Active Inference and retain a reviewed patch; requires dry_run",
        "type": "boolean",
        "default": False,
    }
    job = workflow["jobs"]["refresh-active-inference"]
    assert job["if"] == "inputs.refresh_active_inference == true"
    assert _job()["if"] == "inputs.refresh_active_inference != true"
    assert job["permissions"] == {"contents": "read"}
    assert "REFRESH_DIRECTORY" not in job.get("env", {})
    checkout = next(step for step in job["steps"] if step.get("uses", "").startswith("actions/checkout@"))
    assert checkout["with"]["persist-credentials"] is False
    assert checkout["with"]["submodules"] == "recursive"
    scripts = "\n".join(_executable(step.get("run", "")) for step in job["steps"])
    assert re.search(r"\bgit\s+push\b", scripts) is None
    assert "github-apply" not in scripts
    steps = _refresh_steps()
    lifecycle = steps["Regenerate and validate the actual Active producers"]["run"]
    assert lifecycle.index("stage_02_analysis.py") < lifecycle.index("refresh_rendered_provenance.py")
    assert "--rebind" not in lifecycle
    assert "test_active_coverage_workspace_preserves_canonical_semantic_readiness" in lifecycle
    names = [step.get("name") for step in job["steps"]]
    assert names.index("Capture the confined Active evidence patch") < names.index(
        "Verify the committed Active candidate tree"
    )
    verify = steps["Verify the committed Active candidate tree"]["run"]
    assert "check_publication_outputs.py" in verify
    assert "--strict --rendered" in verify
    upload = steps["Retain the Active evidence candidate and original diagnostics"]
    assert upload["if"] == "always()"
    assert upload["with"]["retention-days"] == 30
    assert upload["with"]["path"] == "${{ runner.temp }}/template-active-refresh/"
    admit = steps["Admit an artifact-only Active refresh"]
    assert admit["env"]["REFRESH_DIRECTORY"] == "${{ runner.temp }}/template-active-refresh"
    assert '>> "$GITHUB_ENV"' in admit["run"]


def _admit_refresh(repo: Path, tmp_path: Path, *, dry_run: str = "true", sha: str | None = None):
    directory = tmp_path / "refresh-artifact"
    result, _ = _run_step(
        _refresh_steps()["Admit an artifact-only Active refresh"],
        repo,
        {
            "DRY_RUN": dry_run,
            "GITHUB_SHA": sha or _git(repo, "rev-parse", "HEAD").strip(),
            "REFRESH_DIRECTORY": str(directory),
        },
        tmp_path,
    )
    return result, directory


@pytest.mark.parametrize("dry_run", ("false", "", "TRUE"))
def test_active_refresh_admission_refuses_non_dry_requests(tmp_path: Path, dry_run: str) -> None:
    repo = _repository(tmp_path)
    result, directory = _admit_refresh(repo, tmp_path, dry_run=dry_run)
    assert result.returncode != 0
    assert "requires dry_run=true" in result.stderr
    assert not (directory / "base-commit.txt").exists()


@pytest.mark.parametrize("defect", ("wrong-sha", "dirty-source", "untracked-source"))
def test_active_refresh_admission_requires_exact_clean_source(tmp_path: Path, defect: str) -> None:
    repo = _repository(tmp_path)
    sha = "0" * 40 if defect == "wrong-sha" else None
    if defect == "dirty-source":
        _write(repo, "README.md", "preserve this work\n", tracked=False)
    elif defect == "untracked-source":
        _write(repo, "new.py", "VALUE = 1\n", tracked=False)
    result, directory = _admit_refresh(repo, tmp_path, sha=sha)
    assert result.returncode != 0
    assert not (directory / "base-commit.txt").exists()


def _capture_refresh(repo: Path, directory: Path, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    result, _ = _run_step(
        _refresh_steps()["Capture the confined Active evidence patch"],
        repo,
        {"REFRESH_DIRECTORY": str(directory)},
        tmp_path,
    )
    return result


_ACTIVE_OUTPUT = "projects/templates/template_active_inference/output/data/result.json"


def test_active_refresh_patch_replays_exact_binary_candidate_tree(tmp_path: Path) -> None:
    repo = _repository(tmp_path)
    figure = "projects/templates/template_active_inference/output/figures/figure.png"
    section = "projects/templates/template_active_inference/manuscript/01_introduction.md"
    _commit_paths(repo, [_ACTIVE_OUTPUT, figure, section], "original evidence")
    result, directory = _admit_refresh(repo, tmp_path)
    assert result.returncode == 0, result.stderr
    base = _git(repo, "rev-parse", "HEAD").strip()
    _write(repo, _ACTIVE_OUTPUT, '{"measured": true}\n', tracked=False)
    (repo / figure).write_bytes(b"\x89PNG\0genuine-test-binary\xff\n")
    _write(repo, section, "# Regenerated section\n", tracked=False)

    captured = _capture_refresh(repo, directory, tmp_path)
    assert captured.returncode == 0, captured.stderr
    patch = directory / "refresh.patch"
    assert b"GIT binary patch" in patch.read_bytes()
    assert (directory / "base-commit.txt").read_text().strip() == base
    target = (directory / "candidate-tree.txt").read_text().strip()
    assert _git(repo, "rev-parse", "HEAD^{tree}").strip() == target
    assert _git(repo, "status", "--porcelain") == ""
    for line in (directory / "SHA256SUMS").read_text().splitlines():
        digest, filename = line.split("  ", 1)
        assert hashlib.sha256((directory / filename).read_bytes()).hexdigest() == digest
    replay = tmp_path / "replay"
    _git(tmp_path, "clone", "--no-hardlinks", "-q", str(repo), str(replay))
    _git(replay, "switch", "--detach", base)
    _git(replay, "apply", "--index", str(patch))
    assert _git(replay, "write-tree").strip() == target


@pytest.mark.parametrize(
    "defect", ("outside-project", "authored-source", "nested-section", "untracked", "deleted", "mode", "symlink")
)
def test_active_refresh_capture_refuses_widening_before_staging(tmp_path: Path, defect: str) -> None:
    repo = _repository(tmp_path)
    authored = "projects/templates/template_active_inference/src/method.py"
    nested = "projects/templates/template_active_inference/manuscript/01_nested/content.md"
    _commit_paths(repo, [_ACTIVE_OUTPUT, "infrastructure/unrelated.py", authored, nested], "original inputs")
    result, directory = _admit_refresh(repo, tmp_path)
    assert result.returncode == 0, result.stderr
    _write(repo, _ACTIVE_OUTPUT, '{"refreshed": true}\n', tracked=False)
    if defect == "outside-project":
        _write(repo, "infrastructure/unrelated.py", "preserve source\n", tracked=False)
    elif defect == "authored-source":
        _write(repo, authored, "preserve source\n", tracked=False)
    elif defect == "nested-section":
        _write(repo, nested, "preserve source\n", tracked=False)
    elif defect == "untracked":
        _write(repo, "new.py", "preserve untracked\n", tracked=False)
    elif defect == "deleted":
        (repo / _ACTIVE_OUTPUT).unlink()
    elif defect == "mode":
        (repo / _ACTIVE_OUTPUT).chmod(0o755)
    elif defect == "symlink":
        target = tmp_path / "preserved-external.json"
        target.write_text("external bytes\n")
        (repo / _ACTIVE_OUTPUT).unlink()
        (repo / _ACTIVE_OUTPUT).symlink_to(target)
    captured = _capture_refresh(repo, directory, tmp_path)
    assert captured.returncode != 0
    assert _git(repo, "diff", "--cached", "--name-only") == ""
    assert not (directory / "refresh.patch").exists()
    if defect == "symlink":
        assert (tmp_path / "preserved-external.json").read_text() == "external bytes\n"


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


def test_rebind_review_artifact_requires_both_verified_tree_gates() -> None:
    steps = _steps()
    assert steps[_CAPTURE]["if"] == "steps.commit.outputs.committed == 'true' && steps.verify.outcome == 'success'"
    assert steps[_REVIEW_UPLOAD]["if"] == (
        "steps.commit.outputs.committed == 'true' && steps.verify.outcome == 'success' "
        "&& steps.capture.outcome == 'success'"
    )
    assert steps[_DIAGNOSTIC_UPLOAD]["if"] == "always()"
    assert "--receipts" in steps[_VERIFY]["run"]
    assert "--format json" in steps[_VERIFY]["run"]
    assert "git push" not in steps[_CAPTURE]["run"]


@pytest.mark.parametrize("defect", (None, "failed-gate", "moved-tree", "outside-footprint", "missing-receipt"))
def test_rebind_review_capture_binds_base_tree_patch_and_gate_receipts(tmp_path: Path, defect: str | None) -> None:
    repo = _repository(tmp_path)
    path = "projects/templates/template_code_project/output/reports/rendered_provenance.json"
    _commit_paths(repo, [path], "original receipt")
    base = _git(repo, "rev-parse", "HEAD").strip()
    changed = "infrastructure/unrelated.py" if defect == "outside-footprint" else path
    _commit_paths(repo, [changed], "rebound receipt")
    commit = _git(repo, "rev-parse", "HEAD").strip()
    tree = _git(repo, "rev-parse", "HEAD^{tree}").strip()
    receipts = tmp_path / "rebind-publication-gate"
    receipts.mkdir()
    (receipts / "template_code_project.json").write_text('{"blocking": 0}\n')
    (tmp_path / "rebind-rendered-audit.json").write_text('{"blocking": 0}\n')
    (tmp_path / "rebind-publication-exit.txt").write_text("0\n")
    (tmp_path / "rebind-rendered-exit.txt").write_text("0\n")
    if defect == "missing-receipt":
        (tmp_path / "rebind-rendered-audit.json").unlink()
    result, _ = _run_step(
        _steps()[_CAPTURE],
        repo,
        {
            "VERIFICATION_OUTCOME": "failure" if defect == "failed-gate" else "success",
            "VERIFIED_COMMIT": commit,
            "VERIFIED_TREE": "0" * 40 if defect == "moved-tree" else tree,
            "GITHUB_SHA": base,
        },
        tmp_path,
    )
    directory = tmp_path / "rebind-review-patch"
    if defect is not None:
        assert result.returncode != 0
        assert not (directory / "COMPLETE.txt").exists()
        return
    assert result.returncode == 0, result.stderr
    assert (directory / "COMPLETE.txt").is_file()
    assert (directory / "base-commit.txt").read_text().strip() == base
    assert (directory / "candidate-commit.txt").read_text().strip() == commit
    assert (directory / "candidate-tree.txt").read_text().strip() == tree
    assert (directory / "publication-gate/template_code_project.json").read_bytes() == (
        receipts / "template_code_project.json"
    ).read_bytes()
    replay = tmp_path / "replay"
    _git(tmp_path, "clone", "--no-hardlinks", "-q", str(repo), str(replay))
    _git(replay, "switch", "--detach", base)
    _git(replay, "apply", "--index", str(directory / "refresh.patch"))
    assert _git(replay, "write-tree").strip() == tree


def test_the_run_reports_the_measured_fingerprints() -> None:
    """A green gate cannot show which stage digest the receipts were stamped with."""
    steps = _steps()
    report = steps[_FINGERPRINTS]
    assert report["id"] == "fingerprints"
    assert report["continue-on-error"] is True
    assert report["if"] == "steps.decide.outputs.act == 'true'"
    assert "build_current_rendered_snapshot" in report["run"]
    assert "templates/template_code_project" in report["run"]
    summary = steps[_SUMMARY]["run"]
    assert "Measured fingerprints" in summary
    assert "fingerprints.txt" in summary


@pytest.mark.timeout(300)
def test_the_fingerprint_report_executes_and_parses(tmp_path: Path) -> None:
    """Execute the real snippet against this checkout and parse its two lines."""
    result = subprocess.run(
        ["bash", "-e", "-o", "pipefail", "-c", _steps()[_FINGERPRINTS]["run"]],
        cwd=_REPO_ROOT,
        env={**_git_env(), "RUNNER_TEMP": str(tmp_path)},
        capture_output=True,
        text=True,
        timeout=280,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(("stage sha256", "config sha256"))]
    assert len(lines) == 2, result.stdout
    parsed = {}
    for line in lines:
        match = _FINGERPRINT_LINE.match(line)
        assert match, line
        parsed[match.group(1)] = match
    # The stage closure is repository-wide; its file count is the recorded one.
    assert int(parsed["stage"].group("measured_files")) > 1000, parsed["stage"].group(0)


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
