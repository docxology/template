"""Direct-call tests for src.composition (no mocks; real files)."""

from __future__ import annotations

import json
from pathlib import Path

from src.composition import compose_literature_review
from src.config import DeepSearchConfig, ProjectConfig, SearchConfig


def _make_config(*, output_dir: str = "output/deep_search") -> ProjectConfig:
    return ProjectConfig(
        title="X",
        search=SearchConfig(query="x"),
        deep_search=DeepSearchConfig(
            enabled=True,
            keywords=["convex"],
            max_results_per_keyword=2,
            output_dir=output_dir,
            unified_bibtex_path="manuscript/references_deep.bib",
        ),
    )


def _setup_iso_with_deep_search(tmp_path: Path) -> Path:
    """Build an isolated project root with a fake deep-search output set."""
    iso = tmp_path / "iso"
    iso.mkdir()
    (iso / "manuscript").mkdir()

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
    (deep / "convex" / "per_paper" / "doi_10.1_x.md").write_text(
        "# [alice2020convexity] — On Convexity\n\n"
        "## Contribution\n\nA novel contribution paragraph.\n\n"
        "## Method\n\n- step\n\n"
        "## Significance for convex\n\nWhy this matters paragraph.\n\n"
        "## Tags\n\nconvex, optimization\n",
        encoding="utf-8",
    )
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


def test_skips_when_no_deep_search(tmp_path: Path, capsys):
    iso = tmp_path / "empty"
    iso.mkdir()
    config = _make_config()
    exit_code = compose_literature_review(iso, config)
    assert exit_code == 2


def test_writes_section_with_all_keys(tmp_path: Path):
    iso = _setup_iso_with_deep_search(tmp_path)
    config = _make_config()
    exit_code = compose_literature_review(iso, config)
    assert exit_code == 0

    out_md = iso / "manuscript" / "S01_literature_review.md"
    assert out_md.exists()
    text = out_md.read_text(encoding="utf-8")
    assert "[@alice2020convexity]" in text
    assert "On Convexity" in text
    assert "novel contribution paragraph" in text
    assert "Why this matters paragraph" in text
    assert "Supplemental S1" in text
    assert "\\newpage" in text

    summary_path = iso / "output" / "deep_search" / "composition_summary.json"
    assert summary_path.exists()
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["unique_papers"] == 1
    assert summary["per_paper_notes_integrated"] == 1
    assert summary["missing_citation_keys"] == []


def test_flags_missing_keys(tmp_path: Path):
    iso = _setup_iso_with_deep_search(tmp_path)
    (iso / "manuscript" / "references_deep.bib").write_text("% empty bib\n", encoding="utf-8")
    config = _make_config()
    exit_code = compose_literature_review(iso, config)
    assert exit_code == 0
    summary = json.loads((iso / "output" / "deep_search" / "composition_summary.json").read_text(encoding="utf-8"))
    assert "alice2020convexity" in summary["missing_citation_keys"]


def test_custom_output_path(tmp_path: Path):
    iso = _setup_iso_with_deep_search(tmp_path)
    custom = iso / "manuscript" / "custom_lit_review.md"
    config = _make_config()
    exit_code = compose_literature_review(iso, config, str(custom))
    assert exit_code == 0
    assert custom.exists()
    assert "[@alice2020convexity]" in custom.read_text(encoding="utf-8")


def test_writes_output_manuscript_parity_copy(tmp_path: Path):
    """When output/manuscript/ already exists, the composed section is
    mirrored there too (defensive parity write)."""
    iso = _setup_iso_with_deep_search(tmp_path)
    (iso / "output" / "manuscript").mkdir(parents=True)
    config = _make_config()
    exit_code = compose_literature_review(iso, config)
    assert exit_code == 0
    mirrored = iso / "output" / "manuscript" / "S01_literature_review.md"
    assert mirrored.exists()
    assert "[@alice2020convexity]" in mirrored.read_text(encoding="utf-8")


def test_no_per_paper_notes_adds_omission_note(tmp_path: Path):
    """When per-paper notes exist but carry no Contribution section, the
    section is skipped with an explanatory note instead of placeholders."""
    iso = tmp_path / "iso"
    iso.mkdir()
    (iso / "manuscript").mkdir()
    deep = iso / "output" / "deep_search"
    (deep / "convex" / "per_paper").mkdir(parents=True)
    aggregate = {
        "keywords": ["convex"],
        "unique_papers": [{"id": "doi:10.1/x", "title": "On Convexity", "year": 2020, "doi": "10.1/x"}],
        "citation_keys": {"doi:10.1/x": "alice2020convexity"},
    }
    (deep / "aggregate.json").write_text(json.dumps(aggregate), encoding="utf-8")
    (deep / "convex" / "papers.json").write_text(
        json.dumps(
            {
                "keyword": "convex",
                "papers": aggregate["unique_papers"],
                "per_source_counts": {},
                "errors": {},
            }
        ),
        encoding="utf-8",
    )
    # Note without a Contribution section.
    (deep / "convex" / "per_paper" / "doi_10.1_x.md").write_text("# Notes\n\n## Tags\n\nconvex\n", encoding="utf-8")
    (iso / "manuscript" / "references_deep.bib").write_text("% empty\n", encoding="utf-8")
    config = _make_config()
    exit_code = compose_literature_review(iso, config)
    assert exit_code == 0
    text = (iso / "manuscript" / "S01_literature_review.md").read_text(encoding="utf-8")
    assert "Per-paper synthesis omitted" in text
