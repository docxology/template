"""Mypy strict-gate negative controls."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_mypy_gate_fails_on_any_typing_error(tmp_path: Path) -> None:
    invalid_module = tmp_path / "invalid_module.py"
    invalid_module.write_text("value: str = 1\n", encoding="utf-8")
    proc = subprocess.run(
        [
            sys.executable,
            "scripts/gates/mypy_ratchet.py",
            str(invalid_module),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 1
    assert "Incompatible types in assignment" in proc.stdout
    assert "typing debt must remain at zero" in proc.stderr
