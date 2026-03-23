"""Subprocess integration: stats JSON then B&W word-count chart script."""

import os
import subprocess
import sys
from pathlib import Path


def test_visualization_wordcount_bw_script_after_stats(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parent.parent.parent.parent
    project = repo / "projects" / "traditional_newspaper"
    stats_script = project / "scripts" / "report_manuscript_stats.py"
    viz_script = project / "scripts" / "visualization_wordcount_bw.py"
    env = os.environ.copy()
    env["PROJECT_DIR"] = str(project)
    r1 = subprocess.run(
        [sys.executable, str(stats_script)],
        cwd=str(repo),
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert r1.returncode == 0, r1.stderr
    r2 = subprocess.run(
        [sys.executable, str(viz_script)],
        cwd=str(repo),
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert r2.returncode == 0, r2.stderr
    out_line = r2.stdout.strip().splitlines()[-1]
    png = Path(out_line)
    assert png.is_file()
    assert png.name == "wordcount_bars_bw.png"
    assert png.stat().st_size > 500
