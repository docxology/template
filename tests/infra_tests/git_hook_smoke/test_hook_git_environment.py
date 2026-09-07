"""Real Git regressions for repository-local variables inherited by push hooks."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
import yaml


@pytest.mark.parametrize("hook_id", ["pre-push-quick", "docs-contract-guard"])
@pytest.mark.parametrize("isolated", [True, False], ids=["configured-hook", "negative-control"])
def test_hook_subprocess_preserves_caller_index(tmp_path: Path, hook_id: str, isolated: bool) -> None:
    """Nested Git writes its own index; the old prefix demonstrates the hazard."""
    root = Path(__file__).resolve().parents[3]
    config = yaml.safe_load((root / ".pre-commit-config.yaml").read_text(encoding="utf-8"))
    hook = next(hook for repo in config["repos"] for hook in repo["hooks"] if hook["id"] == hook_id)
    prefix, separator, _ = hook["args"][-1].partition("uv run ")
    assert separator
    isolation = "unset $(git rev-parse --local-env-vars) && "
    assert isolation in prefix
    if not isolated:
        prefix = prefix.replace(isolation, "", 1)

    # Never let the test's own setup inherit the invoking repository's index.
    clean_env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    caller, nested = tmp_path / "caller", tmp_path / "nested"
    for repo in (caller, nested):
        repo.mkdir()
        subprocess.run(["git", "init", "--quiet", str(repo)], env=clean_env, check=True, timeout=30)
        (repo / "file.txt").write_text(repo.name, encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "add", "file.txt"], env=clean_env, check=True, timeout=30)
    caller_index, nested_index = caller / ".git/index", nested / ".git/index"
    caller_before, nested_before = caller_index.read_bytes(), nested_index.read_bytes()
    inherited = dict(
        clean_env, GIT_DIR=str(caller / ".git"), GIT_WORK_TREE=str(caller), GIT_INDEX_FILE=str(caller_index)
    )
    subprocess.run(
        ["bash", "-eo", "pipefail", "-c", prefix + 'git -C "$1" read-tree --empty', "hook-probe", str(nested)],
        cwd=caller,
        env=inherited,
        check=True,
        timeout=30,
    )
    assert (caller_index.read_bytes() == caller_before) is isolated
    assert (nested_index.read_bytes() != nested_before) is isolated
