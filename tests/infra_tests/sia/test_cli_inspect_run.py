"""CLI inspect-run and JSON output tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_cli_inspect_run_json(tmp_path: Path) -> None:
    summary = tmp_path / "run_summary.json"
    summary.write_text(
        json.dumps(
            {
                "run_id": 1,
                "live": False,
                "max_generations": 3,
                "task_dir": "/tmp/task",
                "generations": [{}, {}, {}],
            }
        ),
        encoding="utf-8",
    )
    repo = Path(__file__).resolve().parents[3]
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "infrastructure.sia.cli",
            "inspect-run",
            str(summary),
            "--json",
        ],
        cwd=str(repo),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["generation_count"] == 3
