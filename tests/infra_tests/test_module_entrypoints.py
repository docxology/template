"""Guard: every documented ``python -m <pkg>`` entrypoint must actually run.

Several CLIs advertise a package-level invocation (``python -m infrastructure.x``)
in their help text / docs. That only works if the package ships a ``__main__.py``.
This test exercises the *real* subprocess invocation (not a direct ``main``
import) so a missing ``__main__.py`` is caught here instead of by a user.

No mocks: a real subprocess per entrypoint, asserting ``--help`` exits 0.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]

# Packages whose help text / docs advertise ``python -m <name>``.
_ENTRYPOINTS = [
    "infrastructure.search.exa",
    "infrastructure.search.literature",
    "infrastructure.reference.citation",
    "infrastructure.llm.cli",
]


@pytest.mark.parametrize("module", _ENTRYPOINTS)
def test_module_entrypoint_help_exits_zero(module: str) -> None:
    """``python -m <module> --help`` must exit 0 (package has a runnable __main__)."""
    result = subprocess.run(
        [sys.executable, "-m", module, "--help"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"`python -m {module} --help` exited {result.returncode}; "
        f"a documented entrypoint is not runnable.\nstderr:\n{result.stderr}"
    )
