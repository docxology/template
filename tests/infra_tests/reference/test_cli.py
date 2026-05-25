"""Tests for infrastructure.reference.citation.cli (real subprocess + tmp files)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "infrastructure.reference.citation.cli", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def test_cli_validate_passes_on_exemplar():
    bibfile = REPO_ROOT / "projects" / "template_code_project" / "manuscript" / "references.bib"
    result = _run(["validate", str(bibfile)])
    assert result.returncode == 0, result.stderr


def test_cli_validate_strict_flags_missing_fields(tmp_path: Path):
    bib = tmp_path / "bad.bib"
    bib.write_text("@article{k, title={Only title}}\n", encoding="utf-8")
    result = _run(["validate", str(bib), "--strict"])
    # Missing author + year → strict exit code 1.
    assert result.returncode == 1


def test_cli_format_round_trips(tmp_path: Path):
    src = tmp_path / "in.bib"
    src.write_text(
        '@article{k,\ntitle = "Hello",\nauthor= {Alice and Bob},\nyear=2024,\n}\n',
        encoding="utf-8",
    )
    out = tmp_path / "out.bib"
    result = _run(["format", str(src), "--output", str(out)])
    assert result.returncode == 0, result.stderr
    formatted = out.read_text(encoding="utf-8")
    assert "@article{k,\n" in formatted
    assert "  title={Hello}," in formatted
    assert "  author={Alice and Bob}," in formatted
    assert "  year={2024}\n" in formatted  # last field, no trailing comma


def test_cli_convert_emits_bibtex(tmp_path: Path):
    papers = [
        {
            "id": "doi:10.1/x",
            "title": "Adam: A method for stochastic optimization",
            "authors": ["Kingma, Diederik P", "Ba, Jimmy"],
            "year": 2014,
            "doi": "10.1/x",
            "venue": "ICLR",
            "venue_type": "conference",
        }
    ]
    in_path = tmp_path / "papers.json"
    in_path.write_text(json.dumps({"papers": papers}), encoding="utf-8")
    out_path = tmp_path / "out.bib"
    result = _run(["convert", str(in_path), str(out_path)])
    assert result.returncode == 0, result.stderr
    text = out_path.read_text(encoding="utf-8")
    assert "@inproceedings{" in text
    assert "kingma2014adam" in text
    assert "booktitle={ICLR}" in text


def test_cli_convert_to_stdout(tmp_path: Path):
    papers = [{"id": "x", "title": "T", "authors": ["Smith, A"], "year": 2024}]
    in_path = tmp_path / "p.json"
    in_path.write_text(json.dumps(papers), encoding="utf-8")
    result = _run(["convert", str(in_path), "-"])
    assert result.returncode == 0, result.stderr
    assert "@article{smith2024" in result.stdout
