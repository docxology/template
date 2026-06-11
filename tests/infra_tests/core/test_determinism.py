#!/usr/bin/env python3
"""Tests for infrastructure.core.determinism.

No mocks: a real ``git`` repo is created under ``tmp_path`` with a committed
file, and the resolver is exercised against real environment-variable state via
monkeypatch.setenv (a pytest fixture, not a mock framework).
"""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path

from infrastructure.core.determinism import (
    TEMPLATE_DETERMINISTIC_ENV,
    deterministic_subprocess_env,
    is_deterministic_requested,
    resolve_build_timestamp,
    resolve_source_date_epoch,
)


def _git_repo_with_commit(root: Path, *, when_epoch: int) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=root, check=True)
    (root / "f.txt").write_text("x\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    iso = datetime.fromtimestamp(when_epoch, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S +0000")
    env = {"GIT_AUTHOR_DATE": iso, "GIT_COMMITTER_DATE": iso}
    subprocess.run(
        ["git", "commit", "-m", "c"], cwd=root, check=True, capture_output=True, env={**_os_environ(), **env}
    )


def _os_environ() -> dict[str, str]:
    import os

    return dict(os.environ)


def test_wallclock_when_not_deterministic(monkeypatch) -> None:
    monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
    monkeypatch.delenv(TEMPLATE_DETERMINISTIC_ENV, raising=False)
    assert is_deterministic_requested() is False
    assert resolve_source_date_epoch() is None
    # wall-clock timestamp parses as a valid recent ISO-Z string
    ts = resolve_build_timestamp()
    assert ts.endswith("Z") and "T" in ts


def test_preset_source_date_epoch_wins(monkeypatch) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
    assert is_deterministic_requested() is True
    assert resolve_source_date_epoch() == 1700000000
    assert resolve_build_timestamp() == "2023-11-14T22:13:20Z"


def test_preset_non_integer_is_ignored(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "not-a-number")
    monkeypatch.delenv(TEMPLATE_DETERMINISTIC_ENV, raising=False)
    # Invalid preset is not honored. The env var's mere presence flips
    # is_deterministic_requested() on, so resolution then tries git in repo_root;
    # against a non-git dir that fails and yields None — proving the bad preset
    # was never used as the epoch.
    assert resolve_source_date_epoch(repo_root=tmp_path) is None


def test_template_deterministic_uses_git_head(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
    monkeypatch.setenv(TEMPLATE_DETERMINISTIC_ENV, "1")
    _git_repo_with_commit(tmp_path, when_epoch=1700000000)
    assert resolve_source_date_epoch(repo_root=tmp_path) == 1700000000
    assert resolve_build_timestamp(repo_root=tmp_path) == "2023-11-14T22:13:20Z"


def test_deterministic_is_stable_across_calls(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
    monkeypatch.setenv(TEMPLATE_DETERMINISTIC_ENV, "1")
    _git_repo_with_commit(tmp_path, when_epoch=1650000000)
    first = resolve_build_timestamp(repo_root=tmp_path)
    second = resolve_build_timestamp(repo_root=tmp_path)
    assert first == second  # byte-stable — the whole point


def test_deterministic_without_git_falls_back(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
    monkeypatch.setenv(TEMPLATE_DETERMINISTIC_ENV, "1")
    # tmp_path is not a git repo → git lookup fails → wall-clock fallback (None epoch)
    assert resolve_source_date_epoch(repo_root=tmp_path) is None


def test_subprocess_env_injects_source_date_epoch(monkeypatch) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
    env = deterministic_subprocess_env(base_env={"PATH": "/usr/bin"})
    assert env["SOURCE_DATE_EPOCH"] == "1700000000"
    assert env["PATH"] == "/usr/bin"  # base preserved


def test_subprocess_env_is_noop_in_wallclock_mode(monkeypatch) -> None:
    monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
    monkeypatch.delenv(TEMPLATE_DETERMINISTIC_ENV, raising=False)
    env = deterministic_subprocess_env(base_env={"PATH": "/usr/bin"})
    assert env == {"PATH": "/usr/bin"}  # nothing added


def test_date_only_format(monkeypatch) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
    assert resolve_build_timestamp(fmt="%Y-%m-%d") == "2023-11-14"
