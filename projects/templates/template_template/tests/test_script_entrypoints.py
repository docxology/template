"""Subprocess checks for directly executable thin orchestrators."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from helpers import PROJECT_DIR, REPO_ROOT


def test_generate_manuscript_metrics_runs_from_repo_root_without_dirtying_checkout(tmp_path: Path) -> None:
    sandbox = tmp_path / PROJECT_DIR.name
    shutil.copytree(PROJECT_DIR / "src", sandbox / "src")
    shutil.copytree(PROJECT_DIR / "manuscript", sandbox / "manuscript")
    shutil.copy2(PROJECT_DIR / "pyproject.toml", sandbox / "pyproject.toml")
    environment = dict(os.environ)
    environment.update(
        {
            "PROJECT_DIR": str(sandbox),
            "TEMPLATE_REPO_ROOT": str(REPO_ROOT),
            "SOURCE_DATE_EPOCH": "0",
        }
    )

    result = subprocess.run(
        [sys.executable, str(PROJECT_DIR / "scripts" / "generate_manuscript_metrics.py")],
        cwd=REPO_ROOT,
        env=environment,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert (sandbox / "output" / "data" / "metrics.json").is_file()
    assert (sandbox / "output" / "manuscript" / "00_abstract.md").is_file()
