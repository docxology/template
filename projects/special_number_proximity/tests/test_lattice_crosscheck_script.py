"""End-to-end run of ``02_lattice_crosscheck.py`` (real subprocess, no mocks)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def test_02_lattice_crosscheck_writes_json() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    project_root = Path(__file__).resolve().parents[1]
    script = project_root / "scripts" / "02_lattice_crosscheck.py"
    env = os.environ.copy()
    env["PROJECT_DIR"] = str(project_root)
    env["PYTHONPATH"] = os.pathsep.join(
        [
            str(repo_root),
            str(repo_root / "infrastructure"),
            str(project_root / "src"),
        ]
    )
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(repo_root),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (result.stdout, result.stderr)
    out_line = result.stdout.strip().splitlines()[-1]
    path = Path(out_line)
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert len(data) >= 4
    for row in data:
        assert row["abs_diff"] <= 1e-12
        assert row["residual_obeyed"] is True
