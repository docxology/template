"""Tests for infrastructure.prose.cli (real subprocess + tmp files)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "infrastructure.prose.cli", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def _write(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    return path


def test_metrics_subcommand(tmp_path: Path):
    p = _write(tmp_path / "intro.md", "Hello world. This is fine.")
    result = _run(["metrics", str(p)])
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["word_count"] == 5
    assert "flesch_reading_ease" in payload


def test_outline_subcommand(tmp_path: Path):
    p = _write(tmp_path / "doc.md", "# Top\n\n## Mid\n\n### Leaf\n")
    result = _run(["outline", str(p)])
    assert result.returncode == 0, result.stderr
    assert "- Top" in result.stdout
    assert "    - Leaf" in result.stdout


def test_quality_subcommand(tmp_path: Path):
    p = _write(tmp_path / "doc.md", "We may suggest this is probably useful.")
    result = _run(["quality", str(p)])
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["hedge_count"] >= 1


def test_report_subcommand(tmp_path: Path):
    man = tmp_path / "manuscript"
    man.mkdir()
    _write(man / "01_a.md", "# A\n\nFirst body.")
    _write(man / "02_b.md", "# B\n\nSecond body.")
    out = tmp_path / "report.json"
    result = _run(["report", str(man), "--output", str(out)])
    assert result.returncode == 0, result.stderr
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["total_words"] >= 4
    assert len(payload["files"]) == 2
