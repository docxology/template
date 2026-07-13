"""Tests for the orchestrator scripts (subprocess; no mocks)."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
# Project lives at projects/templates/<name>/; repo root is three levels up.
REPO_ROOT = PROJECT_ROOT.parents[2]


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
    # Copy authored manuscript inputs and the bundled corpus into the isolated project.
    shutil.copytree(PROJECT_ROOT / "manuscript", project_root / "manuscript")
    (project_root / "data").mkdir()
    corpus_src = PROJECT_ROOT / "data" / "corpus.json"
    (project_root / "data" / "corpus.json").write_text(corpus_src.read_text(encoding="utf-8"), encoding="utf-8")
    return project_root


def _run_offline_pipeline(project_root: Path) -> subprocess.CompletedProcess[str]:
    """Run the real offline search CLI against an isolated project root."""
    return _run(
        "run_search_pipeline.py",
        [
            "--config",
            str(project_root / "manuscript" / "config.yaml"),
            "--project-root",
            str(project_root),
            "--no-llm",
        ],
    )


def test_run_search_pipeline_offline_smoke(tmp_path: Path):
    project_root = _make_run(tmp_path)
    result = _run_offline_pipeline(project_root)
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
    pipeline_result = _run_offline_pipeline(project_root)
    assert pipeline_result.returncode == 0, pipeline_result.stderr

    result = _run(
        "y_generate_search_figures.py",
        ["--project-root", str(project_root)],
    )

    assert result.returncode == 0, result.stderr
    figures_dir = project_root / "output" / "figures"
    expected = {
        figures_dir / "papers_per_source.png",
        figures_dir / "year_histogram.png",
        figures_dir / "score_distribution.png",
    }
    assert set(figures_dir.glob("*.png")) == expected
    assert all(path.stat().st_size > 0 for path in expected)
    registry = json.loads((figures_dir / "figure_registry.json").read_text(encoding="utf-8"))
    assert len(registry["figures"]) == 3


def test_generate_search_figures_skips_without_input(tmp_path: Path):
    project_root = _make_run(tmp_path)
    result = _run("y_generate_search_figures.py", ["--project-root", str(project_root)])

    assert result.returncode == 2
    assert not (project_root / "output" / "figures").exists()


def test_generate_manuscript_variables(tmp_path: Path):
    project_root = _make_run(tmp_path)
    pipeline_result = _run_offline_pipeline(project_root)
    assert pipeline_result.returncode == 0, pipeline_result.stderr

    result = _run(
        "z_generate_manuscript_variables.py",
        ["--project-root", str(project_root)],
    )

    assert result.returncode == 0, result.stderr
    variables_path = project_root / "output" / "data" / "manuscript_variables.json"
    resolved_abstract = project_root / "output" / "manuscript" / "00_abstract.md"
    assert variables_path.is_file()
    assert json.loads(variables_path.read_text(encoding="utf-8"))["result_num_papers"] >= 1
    assert resolved_abstract.is_file()
    assert "{{RESULT_NUM_PAPERS}}" not in resolved_abstract.read_text(encoding="utf-8")
    assert str(variables_path) in result.stdout


def test_generate_manuscript_variables_skips_without_input(tmp_path: Path):
    """If the isolated project has no results JSON, the CLI exits 2 without artifacts."""
    project_root = _make_run(tmp_path)
    result = _run(
        "z_generate_manuscript_variables.py",
        ["--project-root", str(project_root)],
    )

    assert result.returncode == 2
    assert not (project_root / "output" / "data" / "manuscript_variables.json").exists()
    assert not (project_root / "output" / "manuscript").exists()


def test_run_deep_search_disabled_exits_zero(tmp_path: Path):
    """Regression: when deep_search.enabled=false the script must exit 0
    cleanly so the pipeline runner doesn't treat it as a stage failure."""
    iso = tmp_path / "iso"
    iso.mkdir()
    (iso / "manuscript").mkdir()
    # Minimal config with deep_search disabled (default).
    (iso / "manuscript" / "config.yaml").write_text(
        "paper:\n  title: 'X'\nsearch:\n  query: 'x'\n  sources: [local]\ndeep_search:\n  enabled: false\n",
        encoding="utf-8",
    )
    result = _run(
        "run_deep_search.py",
        ["--config", str(iso / "manuscript" / "config.yaml"), "--project-root", str(iso)],
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
    (iso / "data" / "corpus.json").write_text(bundled_corpus.read_text(encoding="utf-8"), encoding="utf-8")
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
            "--config",
            str(iso / "manuscript" / "config.yaml"),
            "--project-root",
            str(iso),
            "--enable",
            "--no-llm",
            "--keyword",
            "convex",
            "--corpus",
            str(iso / "data" / "corpus.json"),
        ],
    )
    assert result.returncode == 0, result.stderr
    assert (iso / "output" / "deep_search" / "convex" / "papers.json").exists()
    assert (iso / "manuscript" / "refs.bib").exists()
