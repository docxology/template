"""Performance observations can be read without making pytest an SDK dependency."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from infrastructure.core.testing.pytest_observations import member_digest


def test_actual_observation_reader_imports_without_site_pytest() -> None:
    root = Path(__file__).resolve().parents[3]
    result = subprocess.run(
        [
            sys.executable,
            "-S",
            "-c",
            "from infrastructure.core.testing.pytest_observations import member_digest; "
            "import sys; assert 'pytest' not in sys.modules; print(member_digest(('owned::case',)))",
        ],
        cwd=root,
        env={**os.environ, "PYTHONPATH": str(root)},
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == member_digest(("owned::case",))
