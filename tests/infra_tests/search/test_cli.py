"""Tests for infrastructure.search.literature.cli (real subprocess + LocalBackend)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def _run(args: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    return subprocess.run(
        [sys.executable, "-m", "infrastructure.search.literature.cli", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=full_env,
    )


def _write_corpus(path: Path) -> None:
    papers = [
        {
            "id": "doi:10.1/x",
            "title": "Convex Optimization",
            "authors": ["Boyd, Stephen", "Vandenberghe, Lieven"],
            "year": 2004,
            "doi": "10.1/x",
            "abstract": "A textbook on convex programming.",
            "venue": "Cambridge",
            "venue_type": "book",
            "publisher": "Cambridge UP",
        },
        {
            "id": "arxiv:1412.6980",
            "title": "Adam: A method for stochastic optimization",
            "authors": ["Kingma, Diederik P", "Ba, Jimmy"],
            "year": 2014,
            "venue": "ICLR",
            "venue_type": "conference",
        },
    ]
    path.write_text(json.dumps(papers), encoding="utf-8")


def test_cli_search_local_emits_json(tmp_path: Path):
    corpus = tmp_path / "c.json"
    _write_corpus(corpus)
    result = _run(
        [
            "search",
            "convex",
            "--source",
            "local",
            "--corpus",
            str(corpus),
            "--max-results",
            "5",
        ]
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["per_source_counts"] == {"local": 1}
    assert payload["papers"][0]["title"] == "Convex Optimization"


def test_cli_search_writes_to_file(tmp_path: Path):
    corpus = tmp_path / "c.json"
    _write_corpus(corpus)
    out = tmp_path / "out.json"
    result = _run(
        [
            "search",
            "convex",
            "--source",
            "local",
            "--corpus",
            str(corpus),
            "--output",
            str(out),
        ]
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert len(payload["papers"]) == 1


def test_cli_to_bibtex_emits_bibtex(tmp_path: Path):
    corpus = tmp_path / "c.json"
    _write_corpus(corpus)
    result = _run(
        [
            "to-bibtex",
            "optimization",
            "--source",
            "local",
            "--corpus",
            str(corpus),
            "--max-results",
            "10",
        ]
    )
    assert result.returncode == 0, result.stderr
    bibtex = result.stdout
    assert "@book{boyd2004convex" in bibtex
    assert "@inproceedings{" in bibtex
    assert "kingma2014adam" in bibtex
    assert "  title={" in bibtex  # 2-space indent preserved


def test_cli_paperclip_requires_env_key():
    # No PAPERCLIP_API_KEY set → exit with error.
    env = {k: v for k, v in os.environ.items() if k != "PAPERCLIP_API_KEY"}
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "infrastructure.search.literature.cli",
            "search",
            "x",
            "--source",
            "paperclip",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode != 0
    assert "PAPERCLIP_API_KEY" in (result.stderr + result.stdout)


def test_cli_unknown_source_errors(tmp_path: Path):
    result = _run(["search", "x", "--source", "fictional_db"])
    assert result.returncode != 0
    assert "Unknown source" in (result.stderr + result.stdout)


def test_cli_uses_cache_dir(tmp_path: Path):
    corpus = tmp_path / "c.json"
    _write_corpus(corpus)
    cache_dir = tmp_path / "cache"
    _run(
        [
            "search",
            "convex",
            "--source",
            "local",
            "--corpus",
            str(corpus),
            "--cache-dir",
            str(cache_dir),
        ]
    )
    files = list(cache_dir.glob("search_*.json")) if cache_dir.exists() else []
    assert len(files) == 1
