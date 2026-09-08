"""Dry-run and explicit-boundary tests for the release rehearsal."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import pytest

from infrastructure.publishing.rehearsal import (
    _clean_generated_render_output,
    _rehearsal_exit_code,
    build_clean_checkout_plan,
    run_clean_checkout_rehearsal,
)


def test_rehearsal_plan_is_offline_and_skipped_by_default() -> None:
    root = Path(__file__).resolve().parents[3]
    plan = build_clean_checkout_plan(root)
    assert plan.network_allowed is False
    assert plan.runs == 2
    assert plan.status == "skipped"
    assert "--execute" in plan.skip_reason


def test_rehearsal_plan_rejects_empty_commands(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="at least one"):
        build_clean_checkout_plan(tmp_path, commands=())


def _git(cwd: Path, *args: str) -> str:
    """Run a real git command for disposable-rehearsal fixtures."""
    result = subprocess.run(("git", *args), cwd=cwd, check=True, capture_output=True, text=True)
    return result.stdout


def test_rehearsal_restores_only_generated_render_output(tmp_path: Path) -> None:
    """Platform-specific canonical render bytes cannot leak into a fresh clone."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "rehearsal-test")
    output = repo / "projects/templates/template_code_project/output"
    output.mkdir(parents=True)
    (output / "tracked.txt").write_text("original\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "fixture")
    (output / "tracked.txt").write_text("rerendered\n", encoding="utf-8")
    (output / "new.txt").write_text("generated\n", encoding="utf-8")
    status = _git(repo, "status", "--porcelain", "--untracked-files=all")

    clean, reason = _clean_generated_render_output(repo, status)

    assert clean is True
    assert "restored 2" in reason
    assert (output / "tracked.txt").read_text(encoding="utf-8") == "original\n"
    assert not (output / "new.txt").exists()
    assert _git(repo, "status", "--porcelain", "--untracked-files=all") == ""


def test_rehearsal_rejects_render_changes_outside_generated_output(tmp_path: Path) -> None:
    """A render that touches source or private state remains a hard blocker."""
    repo = tmp_path / "repo"
    repo.mkdir()
    outside = repo / "README.md"
    outside.write_text("changed\n", encoding="utf-8")

    clean, reason = _clean_generated_render_output(repo, " M README.md\n")

    assert clean is False
    assert "non-generated paths" in reason


def _git_supports_clone_revision() -> bool:
    """``git clone --revision`` needs Git 2.51+; older tooling must skip."""
    with tempfile.TemporaryDirectory() as td:
        origin = Path(td) / "origin"
        origin.mkdir()
        _git(origin, "init", "-q")
        _git(origin, "config", "user.email", "probe@example.invalid")
        _git(origin, "config", "user.name", "probe")
        (origin / "file.txt").write_text("probe\n", encoding="utf-8")
        _git(origin, "add", ".")
        _git(origin, "commit", "-qm", "probe")
        clone = subprocess.run(
            ("git", "clone", "-q", "--no-local", "--revision", "HEAD", str(origin), str(Path(td) / "clone")),
            capture_output=True,
            text=True,
        )
        return clone.returncode == 0


def _fixture_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "rehearsal-test")
    (repo / "README.md").write_text("fixture\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "fixture")
    return repo


@pytest.mark.skipif(not _git_supports_clone_revision(), reason="git clone --revision requires Git 2.51+")
def test_rehearsal_passes_when_two_runs_produce_identical_digests(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    plan = build_clean_checkout_plan(repo, commands=(("git", "rev-parse", "HEAD"),))

    receipt = run_clean_checkout_rehearsal(repo, plan, platform_name="darwin", timeout_seconds=120)

    assert receipt.status == "pass"
    assert receipt.validate() == []
    assert _rehearsal_exit_code(receipt) == 0


@pytest.mark.skipif(not _git_supports_clone_revision(), reason="git clone --revision requires Git 2.51+")
def test_rehearsal_blocks_when_runs_produce_unequal_digests(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    plan = build_clean_checkout_plan(repo, commands=(("sh", "-c", "echo $$"),))

    receipt = run_clean_checkout_rehearsal(repo, plan, platform_name="darwin", timeout_seconds=120)
    assert receipt.status == "blocked"
    assert "different deterministic output digests" in receipt.skip_reason
    passing_digests = {run.output_sha256 for run in receipt.runs if run.status == "pass"}
    assert len(passing_digests) == plan.runs
    assert receipt.validate() == []
    assert _rehearsal_exit_code(receipt) == 1


@pytest.mark.skipif(not _git_supports_clone_revision(), reason="git clone --revision requires Git 2.51+")
def test_rehearsal_ignores_volatile_outputs_when_judging_determinism(tmp_path: Path) -> None:
    """Wall-clock-embedded command output must not block an otherwise-equal pair.

    Hosted run 34243791209 passed all 20 commands but the run digests
    differed only because health/stage/sync stdout embeds durations; the
    determinism digest now covers the byte-stable subset only.
    """
    repo = _fixture_repo(tmp_path)
    script = repo / "scripts/pipeline/stage_01_test.py"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text("import random\nprint(random.random())\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "volatile script")
    plan = build_clean_checkout_plan(repo, commands=(("python", "scripts/pipeline/stage_01_test.py"),))

    receipt = run_clean_checkout_rehearsal(repo, plan, platform_name="darwin", timeout_seconds=120)

    assert receipt.status == "pass"
    assert receipt.validate() == []


def test_output_is_volatile_classification() -> None:
    """Only the known wall-clock-embedded commands count as volatile."""
    from infrastructure.publishing.rehearsal import _output_is_volatile

    assert _output_is_volatile(("uv", "sync", "--locked", "--offline"))
    assert _output_is_volatile(("uv", "run", "python", "-m", "infrastructure.core.health", "--json"))
    assert _output_is_volatile(("uv", "run", "python", "scripts/pipeline/stage_01_test.py", "--receipt", "x.json"))
    assert _output_is_volatile(("uv", "run", "python", "scripts/pipeline/stage_03_render.py", "--project", "p"))
    assert not _output_is_volatile(("uv", "run", "python", "scripts/docgen/counts.py", "--check"))
    assert not _output_is_volatile(("git", "status", "--porcelain", "--untracked-files=all"))


def test_failed_command_receipt_carries_output_tail(tmp_path: Path) -> None:
    """A failing rehearsal command records a bounded diagnostic tail for triage."""
    from infrastructure.publishing.rehearsal import _run_command

    receipt = _run_command(
        [
            "python",
            "-c",
            "import sys; print('stdout-marker'); sys.stderr.write('boom-detail-line'); sys.exit(3)",
        ],
        tmp_path,
    )
    assert receipt.status == "blocked"
    assert receipt.exit_code == 3
    assert "boom-detail-line" in receipt.output_tail
    assert "stdout-marker" in receipt.output_tail
    assert len(receipt.output_tail) <= 4000


def test_passing_command_receipt_has_empty_output_tail(tmp_path: Path) -> None:
    from infrastructure.publishing.rehearsal import _run_command

    receipt = _run_command(["python", "-c", "print('fine')"], tmp_path)
    assert receipt.status == "pass"
    assert receipt.output_tail == ""


def test_run_command_outputs_sink_captures_full_output(tmp_path: Path) -> None:
    """The optional sink receives the complete stdout/stderr pair for persistence."""
    from infrastructure.publishing.rehearsal import _run_command

    captured: list[tuple[str, str]] = []
    receipt = _run_command(
        ["python", "-c", "print('full-stdout'); import sys; sys.stderr.write('full-stderr')"],
        tmp_path,
        outputs_sink=captured.append,
    )
    assert receipt.status == "pass"
    assert captured == [("full-stdout\n", "full-stderr")]


def test_persist_run_artifacts_writes_matrix_receipt_and_failure_logs(tmp_path: Path) -> None:
    """Blocked commands persist redacted logs and the matrix receipt beside the top-level receipt."""
    import json

    from infrastructure.publishing.rehearsal import CommandReceipt, _persist_run_artifacts

    receipt_path = tmp_path / "matrix.json"
    receipt_path.write_text('{"overall_exit": 1}', encoding="utf-8")
    blocked = CommandReceipt(
        command=("uv", "run", "python", "-m", "infrastructure.core.health"),
        status="blocked",
        exit_code=1,
        duration_seconds=1.0,
        skip_reason="command failed",
    )
    passing = CommandReceipt(
        command=("git", "rev-parse", "HEAD"),
        status="pass",
        exit_code=0,
        duration_seconds=0.1,
    )
    artifact_dir = tmp_path / "artifacts"
    _persist_run_artifacts(artifact_dir, 0, receipt_path, [blocked, passing], [("boom-out", "boom-err"), ("", "")])

    run_dir = artifact_dir / "run-1"
    assert json.loads((run_dir / "public-matrix-receipt.json").read_text(encoding="utf-8")) == {"overall_exit": 1}
    logs = sorted(path.name for path in run_dir.glob("*.log"))
    assert len(logs) == 1
    assert "boom-out" in (run_dir / logs[0]).read_text(encoding="utf-8")


def test_persist_run_artifacts_noop_without_artifact_dir(tmp_path: Path) -> None:
    from infrastructure.publishing.rehearsal import CommandReceipt, _persist_run_artifacts

    receipt = CommandReceipt(command=("false",), status="blocked", exit_code=1, duration_seconds=0.1)
    _persist_run_artifacts(None, 0, tmp_path / "missing.json", [receipt], [("out", "err")])
    assert not (tmp_path / "run-1").exists()


def test_failure_tail_redacts_credential_like_output(tmp_path: Path) -> None:
    from infrastructure.publishing.rehearsal import _run_command

    receipt = _run_command(
        ["python", "-c", "import sys; sys.stderr.write('token=supersecret123'); sys.exit(2)"],
        tmp_path,
    )
    assert receipt.status == "blocked"
    assert "supersecret123" not in receipt.output_tail
    assert "redacted" in receipt.output_tail
