"""A bounded child may inherit a broader environment than its cleanup guardian."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

from infrastructure.core.execution_boundary import build_bounded_env, run_bounded_subprocess

_SENTINEL = "TEMPLATE_GUARDIAN_SEPARATION_SENTINEL"

# The child reports its own view of the sentinel and the environments of its
# sibling processes (the guardian is launched by the same parent).
_PROBE = (
    "import json, os, psutil\n"
    "me = os.getpid()\n"
    "siblings = [p for p in psutil.Process(os.getppid()).children() if p.pid != me]\n"
    "seen = []\n"
    "for process in siblings:\n"
    "    try:\n"
    "        seen.append({'pid': process.pid, 'cmd': ' '.join(process.cmdline())[:200],\n"
    "                     'has_sentinel': '" + _SENTINEL + "' in process.environ()})\n"
    "    except psutil.Error as exc:\n"
    "        seen.append({'pid': process.pid, 'error': type(exc).__name__})\n"
    "print(json.dumps({'child': os.environ.get('" + _SENTINEL + "'), 'siblings': seen}))\n"
)


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="reads sibling environments through /proc")
@pytest.mark.timeout(120)
def test_guardian_env_excludes_child_only_credentials(tmp_path: Path) -> None:
    child_env = dict(os.environ, **{_SENTINEL: "child-only-value"})
    result = run_bounded_subprocess(
        [sys.executable, "-c", _PROBE],
        cwd=tmp_path,
        env=child_env,
        guardian_env=build_bounded_env(),
        timeout=60,
    )
    assert result.returncode == 0, (result.stderr, result.command_error)
    observed = json.loads(result.stdout.strip().splitlines()[-1])
    assert observed["child"] == "child-only-value"
    # The parent's only other live child during the run is the cleanup guardian.
    guardians = observed["siblings"]
    assert len(guardians) == 1, observed
    assert all(entry.get("has_sentinel") is False for entry in guardians), observed


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="reads sibling environments through /proc")
@pytest.mark.timeout(120)
def test_guardian_inherits_child_env_without_separate_guardian_env(tmp_path: Path) -> None:
    """Negative control: without ``guardian_env`` the guardian sees the child's variables."""
    child_env = dict(os.environ, **{_SENTINEL: "shared-value"})
    result = run_bounded_subprocess([sys.executable, "-c", _PROBE], cwd=tmp_path, env=child_env, timeout=60)
    assert result.returncode == 0, (result.stderr, result.command_error)
    observed = json.loads(result.stdout.strip().splitlines()[-1])
    # The parent's only other live child during the run is the cleanup guardian.
    guardians = observed["siblings"]
    assert len(guardians) == 1, observed
    assert any(entry.get("has_sentinel") is True for entry in guardians), observed
