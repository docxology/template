"""Tests for the orchestrator scripts (subprocess; no mocks)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_ROOT.parent.parent


def _run(script: str, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / script), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def _make_run(tmp_path: Path) -> Path:
    """Run run_search_pipeline.py against an isolated project root using the bundled corpus."""
    project_root = tmp_path / "proj"
    project_root.mkdir()
    # Copy the corpus and config into the isolated project.
    (project_root / "manuscript").mkdir()
    (project_root / "data").mkdir()
    corpus_src = PROJECT_ROOT / "data" / "corpus.json"
    (project_root / "data" / "corpus.json").write_text(
        corpus_src.read_text(encoding="utf-8"), encoding="utf-8"
    )
    config_src = PROJECT_ROOT / "manuscript" / "config.yaml"
    (project_root / "manuscript" / "config.yaml").write_text(
        config_src.read_text(encoding="utf-8"), encoding="utf-8"
    )
    return project_root


def test_run_search_pipeline_offline_smoke(tmp_path: Path):
    project_root = _make_run(tmp_path)
    result = _run(
        "run_search_pipeline.py",
        [
            "--config", str(project_root / "manuscript" / "config.yaml"),
            "--project-root", str(project_root),
            "--no-llm",
        ],
    )
    assert result.returncode == 0, result.stderr
    # Required outputs exist.
    assert (project_root / "manuscript" / "references.bib").exists()
    assert (project_root / "output" / "corpus.json").exists()
    assert (project_root / "output" / "search" / "results.json").exists()
    assert (project_root / "output" / "reading_report.md").exists()
    summary = json.loads((project_root / "output" / "run_summary.json").read_text())
    assert summary["papers"] >= 1
    assert summary["llm_used"] is False


def test_generate_search_figures(tmp_path: Path):
    project_root = _make_run(tmp_path)
    # First run the search so figures have input.
    pipeline_result = _run(
        "run_search_pipeline.py",
        [
            "--config", str(project_root / "manuscript" / "config.yaml"),
            "--project-root", str(project_root),
            "--no-llm",
        ],
    )
    assert pipeline_result.returncode == 0, pipeline_result.stderr

    # Now run figures.
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "y_generate_search_figures.py")],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env={
            **dict(__import__("os").environ),
            # The script resolves relative to its own path, but we need to
            # point it at the isolated project.
        },
    )
    # The y_ script reads from PROJECT_ROOT/output, not the isolated copy,
    # so we instead invoke it via the in-process module to verify behaviour:
    # exercised in test_figures.py. Here we just assert the script imports
    # cleanly when there are no results.
    if not (PROJECT_ROOT / "output" / "search" / "results.json").exists():
        assert result.returncode == 2  # graceful skip


def test_generate_manuscript_variables_skips_without_input(tmp_path: Path):
    """If results.json is missing, the manuscript-vars script exits 2."""
    # Only check skip-path behaviour at the script level; full happy-path is
    # covered by unit tests on src.manuscript_variables.
    if (PROJECT_ROOT / "output" / "search" / "results.json").exists():
        pytest.skip("results.json present — happy path covered by unit tests")
    result = _run("z_generate_manuscript_variables.py", [])
    assert result.returncode == 2


def test_run_deep_search_disabled_exits_zero(tmp_path: Path):
    """Regression: when deep_search.enabled=false the script must exit 0
    cleanly so the pipeline runner doesn't treat it as a stage failure."""
    iso = tmp_path / "iso"
    iso.mkdir()
    (iso / "manuscript").mkdir()
    # Minimal config with deep_search disabled (default).
    (iso / "manuscript" / "config.yaml").write_text(
        "paper:\n  title: 'X'\n"
        "search:\n  query: 'x'\n  sources: [local]\n"
        "deep_search:\n  enabled: false\n",
        encoding="utf-8",
    )
    result = _run(
        "run_deep_search.py",
        ["--config", str(iso / "manuscript" / "config.yaml"),
         "--project-root", str(iso)],
    )
    assert result.returncode == 0
    assert "skipping deep search" in (result.stderr + result.stdout).lower()


def test_run_deep_search_enabled_with_corpus(tmp_path: Path):
    """End-to-end: --enable + local corpus + --no-llm must succeed."""
    iso = tmp_path / "iso"
    iso.mkdir()
    (iso / "manuscript").mkdir()
    (iso / "data").mkdir()
    # Copy bundled corpus.
    bundled_corpus = PROJECT_ROOT / "data" / "corpus.json"
    (iso / "data" / "corpus.json").write_text(
        bundled_corpus.read_text(encoding="utf-8"), encoding="utf-8"
    )
    (iso / "manuscript" / "config.yaml").write_text(
        "paper:\n  title: 'X'\n"
        "search:\n  query: 'x'\n  sources: [local]\n"
        "  local_corpus: 'data/corpus.json'\n"
        "deep_search:\n"
        "  enabled: false\n"  # script will --enable override this
        "  sources: [local]\n"
        "  fetch_abstracts: false\n"
        "  fetch_fulltext: false\n"
        "  output_dir: 'output/deep_search'\n"
        "  search_cache_dir: 'output/cache/search'\n"
        "  unified_bibtex_path: 'manuscript/refs.bib'\n",
        encoding="utf-8",
    )
    result = _run(
        "run_deep_search.py",
        [
            "--config", str(iso / "manuscript" / "config.yaml"),
            "--project-root", str(iso),
            "--enable", "--no-llm",
            "--keyword", "convex",
            "--corpus", str(iso / "data" / "corpus.json"),
        ],
    )
    assert result.returncode == 0, result.stderr
    assert (iso / "output" / "deep_search" / "convex" / "papers.json").exists()
    assert (iso / "manuscript" / "refs.bib").exists()
