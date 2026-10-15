"""Actual configured Git fsmonitor must not mutate a held publication index."""

from __future__ import annotations

import hashlib
import shlex
import subprocess
from pathlib import Path

import pytest

from infrastructure.publishing._standalone_git import (
    _git,
    _git_environment,
    _git_clean_source_inventory,
    _git_head_status,
    _git_source_inventory,
)
from infrastructure.publishing.standalone_mirror import _validate_git_destination_current


def _index_identity(path: Path) -> tuple[int, int, int, int, int, int, str]:
    observed = path.stat()
    return (
        observed.st_dev,
        observed.st_ino,
        observed.st_mode,
        observed.st_size,
        observed.st_mtime_ns,
        observed.st_ctime_ns,
        hashlib.sha256(path.read_bytes()).hexdigest(),
    )


def test_metadata_reads_disable_actual_fsmonitor_and_optional_index_writes(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    def fixture_git(args: list[str]) -> None:
        subprocess.run(
            ["git", "--no-replace-objects", "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false", *args],
            cwd=repo,
            env=_git_environment(),
            capture_output=True,
            text=True,
            check=True,
            timeout=60,
        )

    fixture_git(["init", "-q"])
    (repo / "infrastructure").mkdir()
    (repo / "infrastructure" / "witness.py").write_text("VALUE = 1\n", encoding="utf-8")
    fixture_git(["add", "-A"])
    fixture_git(["-c", "user.name=Test", "-c", "user.email=t@example.com", "commit", "-qm", "fixture"])
    marker = repo / ".git" / "fsmonitor-invoked"
    hook = repo / ".git" / "fixture-fsmonitor"
    hook.write_text(
        f"#!/bin/sh\nprintf 'actual-fsmonitor\\n' > {shlex.quote(str(marker))}\nprintf 'fixture-token\\000/\\000'\n",
        encoding="utf-8",
    )
    hook.chmod(0o700)
    fixture_git(["config", "core.fsmonitor", str(hook)])
    # Real positive control proves this exact repository hook can run.
    original = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=repo,
        env={**_git_environment(), "GIT_OPTIONAL_LOCKS": "1"},
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    assert original.stdout == "" and marker.read_text(encoding="utf-8") == "actual-fsmonitor\n"
    marker.unlink()
    index = repo / ".git" / "index"
    before = _index_identity(index)
    assert _git_environment()["GIT_OPTIONAL_LOCKS"] == "0"
    head, label, status = _git_head_status(repo)
    assert label is None and status == ""
    assert _git(["status", "--porcelain", "--untracked-files=all"], repo).stdout == ""
    tracked, tree = _git_source_inventory(repo, head)
    assert tracked == ["infrastructure/witness.py"]
    assert "infrastructure/witness.py" in tree
    assert not marker.exists()
    assert _index_identity(index) == before
    assert _git(["config", "--local", "--get", "core.fsmonitor"], repo).stdout.strip() == str(hook)


def _actual_repository(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _fixture_git(repo, ["init", "-q"])
    (repo / "infrastructure").mkdir()
    (repo / "infrastructure/witness.py").write_text("VALUE = 1\n", encoding="utf-8")
    _fixture_git(repo, ["add", "-A"])
    _fixture_git(repo, ["-c", "user.name=Test", "-c", "user.email=t@example.com", "commit", "-qm", "fixture"])
    head = _fixture_git(repo, ["rev-parse", "--verify", "HEAD^{commit}"]).stdout.strip()
    return repo, head


def _fixture_git(repo: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "--no-replace-objects", "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false", *args],
        cwd=repo,
        env=_git_environment(),
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )


def test_actual_clean_inventory_cohort_preserves_index_and_fsmonitor(tmp_path: Path) -> None:
    repo, head = _actual_repository(tmp_path)
    marker = repo / ".git/fsmonitor-invoked"
    hook = repo / ".git/fixture-fsmonitor"
    hook.write_text(
        f"#!/bin/sh\nprintf 'actual-fsmonitor\\n' > {shlex.quote(str(marker))}\nprintf 'fixture-token\\000/\\000'\n",
        encoding="utf-8",
    )
    hook.chmod(0o700)
    _fixture_git(repo, ["config", "core.fsmonitor", str(hook)])
    subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=repo,
        env={**_git_environment(), "GIT_OPTIONAL_LOCKS": "1"},
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    assert marker.read_text(encoding="utf-8") == "actual-fsmonitor\n"
    marker.unlink()
    before = _index_identity(repo / ".git/index")
    actual_head, tracked, tree = _git_clean_source_inventory(repo, head[:12])
    assert actual_head == head and tracked == ["infrastructure/witness.py"]
    assert "infrastructure/witness.py" in tree
    assert not marker.exists()
    assert _index_identity(repo / ".git/index") == before
    assert _fixture_git(repo, ["config", "--local", "--get", "core.fsmonitor"]).stdout.strip() == str(hook)


@pytest.mark.parametrize("fault", ["tracked", "untracked", "revision"])
def test_actual_clean_inventory_cohort_refuses_unadmitted_source(tmp_path: Path, fault: str) -> None:
    repo, head = _actual_repository(tmp_path)
    if fault == "untracked":
        (repo / "untracked.txt").write_text("unadmitted\n", encoding="utf-8")
    else:
        (repo / "infrastructure/witness.py").write_text("VALUE = 2\n", encoding="utf-8")
        if fault == "revision":
            _fixture_git(repo, ["add", "-A"])
            _fixture_git(repo, ["-c", "user.name=Test", "-c", "user.email=t@example.com", "commit", "-qm", "next"])
    before = _index_identity(repo / ".git/index")
    refusal = "differs from current HEAD" if fault == "revision" else "requires a clean source working tree"
    with pytest.raises(ValueError, match=refusal):
        _git_clean_source_inventory(repo, head)
    assert _index_identity(repo / ".git/index") == before


def test_actual_destination_cohort_preserves_unrelated_routing_and_configuration(tmp_path: Path) -> None:
    repo, _ = _actual_repository(tmp_path)
    admitted = "https://github.com/example/admitted.git"
    _fixture_git(repo, ["remote", "add", "origin", admitted])
    _fixture_git(repo, ["remote", "add", "unrelated", "https://github.com/example/unrelated.git"])
    before = (repo / ".git/config").read_bytes()
    index_before = _index_identity(repo / ".git/index")
    _validate_git_destination_current(admitted, repo)
    assert (repo / ".git/config").read_bytes() == before
    assert _index_identity(repo / ".git/index") == index_before


@pytest.mark.parametrize("fault", ["insteadOf", "pushInsteadOf", "origin", "additional"])
def test_actual_destination_cohort_refuses_rewrite_and_origin_redirection(tmp_path: Path, fault: str) -> None:
    repo, _ = _actual_repository(tmp_path)
    admitted = "https://github.com/example/admitted.git"
    other = "https://github.com/example/unreviewed.git"
    _fixture_git(repo, ["remote", "add", "origin", admitted])
    if fault in {"insteadOf", "pushInsteadOf"}:
        _fixture_git(repo, ["config", f"url.{other}.{fault}", admitted])
    else:
        if fault == "additional":
            _fixture_git(repo, ["config", "--add", "remote.origin.pushurl", admitted])
        _fixture_git(repo, ["config", "--add", "remote.origin.pushurl", other])
    before = (repo / ".git/config").read_bytes()
    refusal = "Git rewrites" if fault in {"insteadOf", "pushInsteadOf"} else "origin push destination differs"
    with pytest.raises(ValueError, match=refusal):
        _validate_git_destination_current(admitted, repo)
    assert (repo / ".git/config").read_bytes() == before


def test_actual_clean_inventory_cohort_retains_native_git_failure(tmp_path: Path) -> None:
    repo = tmp_path / "empty"
    repo.mkdir()
    _fixture_git(repo, ["init", "-q"])
    with pytest.raises(RuntimeError, match="original native Git return code: 128"):
        _git_clean_source_inventory(repo, "0" * 40)
