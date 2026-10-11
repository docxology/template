"""Actual configured Git fsmonitor must not mutate a held publication index."""

from __future__ import annotations

import hashlib
import shlex
import subprocess
from pathlib import Path

from infrastructure.publishing.standalone_mirror import (
    _git,
    _git_environment,
    _git_head_status,
    _git_source_inventory,
)


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
