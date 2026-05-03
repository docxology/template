"""Test the literature-review composition script (subprocess; no mocks)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_ROOT.parent.parent


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "s_compose_literature_review.py"),
            *args,
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def _setup_iso_with_deep_search(tmp_path: Path) -> Path:
    """Build an isolated project root with a fake deep-search output set."""
    iso = tmp_path / "iso"
    iso.mkdir()
    (iso / "manuscript").mkdir()
    (iso / "manuscript" / "config.yaml").write_text(
        "paper:\n  title: 'X'\n"
        "search:\n  query: 'x'\n"
        "deep_search:\n"
        "  enabled: true\n"
        "  keywords: ['convex']\n"
        "  max_results_per_keyword: 2\n"
        "  output_dir: 'output/deep_search'\n"
        "  unified_bibtex_path: 'manuscript/references_deep.bib'\n",
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
    (deep / "aggregate.json").write_text(
        json.dumps(aggregate), encoding="utf-8"
    )
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
    (iso / "manuscript" / "references_deep.bib").write_text(
        "@article{alice2020convexity,\n"
        "  title={On Convexity},\n"
        "  author={Alice and Bob},\n"
        "  year={2020},\n"
        "  doi={10.1/x}\n"
        "}\n",
        encoding="utf-8",
    )
    return iso


def test_composition_skips_when_no_deep_search(tmp_path: Path):
    iso = tmp_path / "empty"
    iso.mkdir()
    (iso / "manuscript").mkdir()
    (iso / "manuscript" / "config.yaml").write_text(
        "paper:\n  title: 'X'\nsearch:\n  query: 'x'\n", encoding="utf-8"
    )
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
    out_md = iso / "manuscript" / "S01_literature_review.md"
    assert out_md.exists()
    text = out_md.read_text(encoding="utf-8")
    assert "[@alice2020convexity]" in text
    assert "On Convexity" in text
    assert "novel contribution paragraph" in text
    assert "Why this matters paragraph" in text
    # Pandoc supplemental marker so the section renders as an appendix.
    assert "Supplemental S1" in text
    assert "\\newpage" in text

    summary_path = iso / "output" / "deep_search" / "composition_summary.json"
    assert summary_path.exists()
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["unique_papers"] == 1
    assert summary["per_paper_notes_integrated"] == 1
    assert summary["missing_citation_keys"] == []


def test_composition_flags_missing_keys(tmp_path: Path):
    iso = _setup_iso_with_deep_search(tmp_path)
    # Empty the bib so every cited key is missing.
    (iso / "manuscript" / "references_deep.bib").write_text(
        "% empty bib\n", encoding="utf-8"
    )
    result = _run(
        [
            "--config",
            str(iso / "manuscript" / "config.yaml"),
            "--project-root",
            str(iso),
        ]
    )
    assert result.returncode == 0, result.stderr
    summary = json.loads(
        (iso / "output" / "deep_search" / "composition_summary.json").read_text(
            encoding="utf-8"
        )
    )
    assert "alice2020convexity" in summary["missing_citation_keys"]


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
