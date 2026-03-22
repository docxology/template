"""Integration test for ``scripts/report_manuscript_stats.py``."""

import json
import os
import subprocess
import sys
from pathlib import Path


def test_report_manuscript_stats_writes_json(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parent.parent.parent.parent
    project = repo / "projects" / "traditional_newspaper"
    script = project / "scripts" / "report_manuscript_stats.py"
    env = os.environ.copy()
    env["PROJECT_DIR"] = str(project)
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(repo),
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    out_line = result.stdout.strip().splitlines()[-1]
    json_path = Path(out_line)
    assert json_path.is_file()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data.get("project") == "traditional_newspaper"
    files = data.get("files", [])
    assert len(files) >= 18
    stems = {Path(str(f["path"])).name for f in files}
    assert "01_front_page.md" in stems
    assert "S01_layout_and_pipeline.md" in stems
    assert "98_newspaper_and_pipeline_terms.md" in stems
    for f in files:
        assert "words" in f
        assert "lines" in f
        assert int(f["words"]) >= 1
