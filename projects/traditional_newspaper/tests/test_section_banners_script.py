"""Subprocess test for ``scripts/generate_section_banners.py``."""

import os
import subprocess
import sys
from pathlib import Path

from newspaper.sections import section_banner_targets


def test_generate_section_banners_script_prints_paths(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parent.parent.parent.parent
    project = repo / "projects" / "traditional_newspaper"
    script = project / "scripts" / "generate_section_banners.py"
    env = os.environ.copy()
    env["PROJECT_DIR"] = str(project)
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(repo),
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    lines: list[str] = []
    for ln in result.stdout.splitlines():
        for part in ln.split():
            if part.endswith(".png") and "section_banner_" in part:
                lines.append(part)
                break
    assert len(lines) == len(section_banner_targets())
    first = Path(lines[0])
    assert first.is_file()
    assert first.name.startswith("section_banner_")
