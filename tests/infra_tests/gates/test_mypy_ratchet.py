"""Mypy debt-ratchet negative controls."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_mypy_ratchet_fails_when_ceiling_is_reduced_below_live_debt(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline.json"
    baseline.write_text(
        json.dumps(
            {
                "packages": {
                    "reporting": {
                        "max_errors": 0,
                        "allowed_files": ["infrastructure/reporting/pytest_output_parser.py"],
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    proc = subprocess.run(
        [
            sys.executable,
            "scripts/gates/mypy_ratchet.py",
            "--baseline",
            str(baseline),
            "infrastructure/reporting/pytest_output_parser.py",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 1
    assert "exceeds ceiling 0" in proc.stdout
