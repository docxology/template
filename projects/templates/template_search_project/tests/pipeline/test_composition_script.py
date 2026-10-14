"""Test the literature-review composition script (subprocess; no mocks)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "s_compose_literature_review.py"),
            *args,
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )


def _seal(root: Path) -> None:
    from template_search_project.publish.config import load_project_config
    from template_search_project.publish.deep_custody import begin_deep_producer, finish_deep_producer

    config = load_project_config(root / "manuscript" / "config.yaml").deep_search
    finish_deep_producer(root, config, begin_deep_producer(config), root / "output" / "deep_search")


def _setup_iso_with_deep_search(tmp_path: Path) -> Path:
    """Build an isolated project root with a fake deep-search output set."""
    iso = tmp_path / "iso"
    iso.mkdir()
    (iso / "manuscript").mkdir()
    (iso / "output" / "bibliography").mkdir(parents=True)
    (iso / "manuscript" / "config.yaml").write_text(
        "paper:\n  title: 'X'\n"
        "search:\n  query: 'x'\n"
        "deep_search:\n"
        "  enabled: true\n"
        "  keywords: ['convex']\n"
        "  max_results_per_keyword: 2\n"
        "  output_dir: 'output/deep_search'\n"
        "  unified_bibtex_path: 'output/bibliography/references_deep.bib'\n",
        encoding="utf-8",
    )

    deep = iso / "output" / "deep_search"
    (deep / "convex" / "per_paper").mkdir(parents=True)
    aggregate = {
        "keywords": ["convex"],
        "unique_papers": [
            {
                "id": "doi:10.1/x",
                "title": "On Convexity",
                "authors": ["Alice", "Bob"],
                "year": 2020,
                "doi": "10.1/x",
                "url": "https://doi.org/10.1/x",
            }
        ],
        "citation_keys": {"doi:10.1/x": "alice2020convexity"},
    }
    (deep / "aggregate.json").write_text(json.dumps(aggregate), encoding="utf-8")
    (deep / "convex" / "papers.json").write_text(
        json.dumps(
            {
                "keyword": "convex",
                "papers": aggregate["unique_papers"],
                "per_source_counts": {"local": 1},
                "errors": {},
            }
        ),
        encoding="utf-8",
    )
    # Per-paper note with the structured sections.
    (deep / "convex" / "per_paper" / "doi_10.1_x.md").write_text(
        "# [alice2020convexity] — On Convexity\n\n"
        "## Contribution\n\nA novel contribution paragraph.\n\n"
        "## Method\n\n- step\n\n"
        "## Significance for convex\n\nWhy this matters paragraph.\n\n"
        "## Tags\n\nconvex, optimization\n",
        encoding="utf-8",
    )
    # Minimal bib with the cited key.
    (iso / "output" / "bibliography" / "references_deep.bib").write_text(
        "@article{alice2020convexity,\n"
        "  title={On Convexity},\n"
        "  author={Alice and Bob},\n"
        "  year={2020},\n"
        "  doi={10.1/x}\n"
        "}\n",
        encoding="utf-8",
    )
    _seal(iso)
    return iso


def test_composition_skips_when_no_deep_search(tmp_path: Path):
    iso = tmp_path / "empty"
    iso.mkdir()
    (iso / "manuscript").mkdir()
    (iso / "output" / "bibliography").mkdir(parents=True)
    (iso / "manuscript" / "config.yaml").write_text("paper:\n  title: 'X'\nsearch:\n  query: 'x'\n", encoding="utf-8")
    result = _run(
        [
            "--config",
            str(iso / "manuscript" / "config.yaml"),
            "--project-root",
            str(iso),
        ]
    )
    assert result.returncode == 2
    assert "skipping" in (result.stdout + result.stderr).lower()


def test_composition_writes_section_with_all_keys(tmp_path: Path):
    iso = _setup_iso_with_deep_search(tmp_path)
    result = _run(
        [
            "--config",
            str(iso / "manuscript" / "config.yaml"),
            "--project-root",
            str(iso),
        ]
    )
    assert result.returncode == 0, result.stderr
    out_md = iso / "output" / "manuscript" / "S02_generated_literature_review.md"
    assert out_md.exists()
    text = out_md.read_text(encoding="utf-8")
    assert "[@alice2020convexity]" in text
    assert "On Convexity" in text
    assert "novel contribution paragraph" in text
    assert "Why this matters paragraph" in text
    # Pandoc supplemental marker so the section renders as an appendix.
    assert "Supplemental S2" in text
    assert "\\newpage" in text
    assert "keyword from local)" in text

    summary_path = iso / "output" / "deep_search" / "composition_summary.json"
    assert summary_path.exists()
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["unique_papers"] == 1
    assert summary["per_paper_notes_integrated"] == 1
    assert summary["missing_citation_keys"] == []
    assert summary["retrieval_sources"] == ["local"]


def test_composition_changed_artifact_fails(tmp_path: Path):
    iso = _setup_iso_with_deep_search(tmp_path)
    (iso / "output" / "bibliography" / "references_deep.bib").write_text("% changed bib\n", encoding="utf-8")
    result = _run(["--config", str(iso / "manuscript" / "config.yaml"), "--project-root", str(iso)])
    assert result.returncode == 1
    assert "artifact bytes changed" in result.stderr
    assert "artifact bytes changed" not in result.stdout
    assert not (iso / "output" / "manuscript" / "S02_generated_literature_review.md").exists()
    assert not (iso / "output" / "deep_search" / "composition_summary.json").exists()


def test_composition_custom_output_path(tmp_path: Path):
    iso = _setup_iso_with_deep_search(tmp_path)
    custom = iso / "manuscript" / "custom_lit_review.md"
    result = _run(
        [
            "--config",
            str(iso / "manuscript" / "config.yaml"),
            "--project-root",
            str(iso),
            "--output",
            str(custom),
        ]
    )
    assert result.returncode == 0, result.stderr
    assert custom.exists()
    assert "[@alice2020convexity]" in custom.read_text(encoding="utf-8")


@pytest.mark.parametrize("fault", ["authored-source", "missing-origin"])
def test_composition_refuses_changed_genuine_sdk_origin_before_outputs(tmp_path: Path, fault: str) -> None:
    """A real preloaded SDK cannot become an authored or nonexistent provider."""
    script = PROJECT_ROOT / "scripts/s_compose_literature_review.py"
    origin = script if fault == "authored-source" else tmp_path / "absent-sdk.py"
    output = tmp_path / "never-created.md"
    launch = (
        "import infrastructure,runpy,sys;infrastructure.__file__=sys.argv.pop(1);"
        "script=sys.argv.pop(1);before=sys.path[:];sys.argv[0]=script\n"
        "try:\n"
        " runpy.run_path(script,run_name='__main__')\n"
        "except (ImportError,FileNotFoundError) as error:\n"
        " assert sys.path==before\n"
        " print(type(error).__name__+': '+str(error),file=sys.stderr)\n"
        " raise SystemExit(1)\n"
        "raise AssertionError('changed SDK origin was accepted')\n"
    )
    result = subprocess.run(
        [sys.executable, "-I", "-c", launch, str(origin), str(script), "--output", str(output)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    expected = "own project source cannot provide" if fault == "authored-source" else "FileNotFoundError"
    assert expected in result.stderr
    assert not output.exists()
