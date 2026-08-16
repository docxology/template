"""Regression tests for process-local Git configuration in the test harness."""

from __future__ import annotations

import hashlib
import os
import subprocess
from pathlib import Path


def _run_git(
    repository: Path,
    *arguments: str,
    environment: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603 - fixed executable with test-controlled arguments
        ["git", *arguments],
        cwd=repository,
        check=False,
        capture_output=True,
        env=environment,
        text=True,
        timeout=30,
    )


def test_ephemeral_git_repositories_do_not_activate_fsmonitor(tmp_path: Path) -> None:
    """Child Git processes avoid detached daemons and optional index writes."""
    isolated_home = tmp_path / "home"
    isolated_home.mkdir()
    (isolated_home / ".gitconfig").write_text("[core]\n\tfsmonitor = true\n", encoding="utf-8")
    environment = os.environ.copy()
    environment["HOME"] = str(isolated_home)
    environment["XDG_CONFIG_HOME"] = str(isolated_home / ".config")
    assert environment["GIT_OPTIONAL_LOCKS"] == "0"

    repository = tmp_path / "repository"
    repository.mkdir()

    initialized = _run_git(repository, "init", "--quiet", environment=environment)
    assert initialized.returncode == 0, initialized.stderr

    global_config = _run_git(
        repository,
        "config",
        "--global",
        "--get",
        "core.fsmonitor",
        environment=environment,
    )
    assert global_config.returncode == 0, global_config.stderr
    assert global_config.stdout.strip() == "true"

    configured = _run_git(repository, "config", "--get", "core.fsmonitor", environment=environment)
    assert configured.returncode == 0, configured.stderr
    assert configured.stdout.strip() == "false"
    assert (
        _run_git(
            repository,
            "config",
            "--local",
            "--get",
            "core.fsmonitor",
            environment=environment,
        ).returncode
        == 1
    )

    configured_email = _run_git(
        repository,
        "config",
        "user.email",
        "test@example.invalid",
        environment=environment,
    )
    assert configured_email.returncode == 0, configured_email.stderr
    configured_name = _run_git(
        repository,
        "config",
        "user.name",
        "Test Harness",
        environment=environment,
    )
    assert configured_name.returncode == 0, configured_name.stderr

    tracked = repository / "tracked.txt"
    tracked.write_text("stable content\n", encoding="utf-8")
    added = _run_git(repository, "add", "tracked.txt", environment=environment)
    assert added.returncode == 0, added.stderr
    committed = _run_git(repository, "commit", "--quiet", "-m", "baseline", environment=environment)
    assert committed.returncode == 0, committed.stderr

    index = repository / ".git" / "index"
    index_digest = hashlib.sha256(index.read_bytes()).hexdigest()
    os.utime(tracked, (946684800, 946684800))

    status = _run_git(repository, "status", "--short", environment=environment)
    assert status.returncode == 0, status.stderr
    assert status.stdout == ""
    assert hashlib.sha256(index.read_bytes()).hexdigest() == index_digest
    assert not (repository / ".git" / "index.lock").exists()
    assert _run_git(repository, "fsmonitor--daemon", "status", environment=environment).returncode != 0
