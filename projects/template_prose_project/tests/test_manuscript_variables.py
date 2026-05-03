"""Tests for src.manuscript_variables."""

from __future__ import annotations

import json
from pathlib import Path

from src.manuscript_variables import (
    compute_variables,
    load_manuscript_report,
    substitute_in_text,
    write_resolved_manuscript_tree,
    write_variables,
)


def _payload(files: list[dict] | None = None, citation_keys: list[str] | None = None):
    return {
        "total_words": sum(f["metrics"]["word_count"] for f in (files or [])),
        "total_sentences": sum(f["metrics"]["sentence_count"] for f in (files or [])),
        "total_paragraphs": 5,
        "avg_flesch_kincaid_grade": 12.4,
        "avg_flesch_reading_ease": 50.5,
        "avg_gunning_fog": 14.0,
        "citation_keys": citation_keys or [],
        "files": files or [],
    }


def _file(name: str, words: int, sentences: int = 5):
    return {
        "name": name,
        "metrics": {
            "word_count": words,
            "sentence_count": sentences,
            "flesch_reading_ease": 50.0,
            "flesch_kincaid_grade": 12.0,
            "gunning_fog": 14.0,
        },
    }


def test_compute_variables_basic():
    payload = _payload(
        files=[_file("a.md", 100), _file("b.md", 250)],
        citation_keys=["k1", "k2"],
    )
    vars_ = compute_variables(config_title="Demo", manuscript_report=payload)
    assert vars_.config_title == "Demo"
    assert vars_.total_words == 350
    assert vars_.citation_count == 2
    assert vars_.files_analysed == 2
    assert vars_.longest_section_words == 250
    assert vars_.shortest_section_words == 100


def test_compute_variables_empty():
    vars_ = compute_variables(config_title="Demo", manuscript_report={})
    assert vars_.total_words == 0
    assert vars_.files_analysed == 0
    assert vars_.longest_section_words == 0


def test_uppercase_keys_format():
    vars_ = compute_variables(
        config_title="X", manuscript_report=_payload(files=[_file("a.md", 1)])
    )
    keys = vars_.as_uppercase_keys()
    assert "{{TOTAL_WORDS}}" in keys
    assert "{{CONFIG_TITLE}}" in keys
    assert keys["{{CONFIG_TITLE}}"] == "X"


def test_substitute_in_text():
    vars_ = compute_variables(
        config_title="My Paper",
        manuscript_report=_payload(files=[_file("a.md", 42)]),
    )
    out = substitute_in_text("{{CONFIG_TITLE}} has {{TOTAL_WORDS}} words.", vars_)
    assert out == "My Paper has 42 words."


def test_substitute_leaves_unmatched_markers():
    vars_ = compute_variables(config_title="X", manuscript_report={})
    out = substitute_in_text("{{NOT_A_VAR}} stays", vars_)
    assert "{{NOT_A_VAR}}" in out


def test_write_variables_round_trip(tmp_path: Path):
    vars_ = compute_variables(
        config_title="X", manuscript_report=_payload(files=[_file("a.md", 5)])
    )
    path = write_variables(vars_, tmp_path / "vars.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["total_words"] == 5
    assert payload["config_title"] == "X"


def test_load_manuscript_report(tmp_path: Path):
    src = tmp_path / "r.json"
    src.write_text(json.dumps(_payload()), encoding="utf-8")
    payload = load_manuscript_report(src)
    assert payload["total_paragraphs"] == 5


def test_write_resolved_manuscript_tree(tmp_path: Path):
    """write_resolved_manuscript_tree hydrates {{TOKEN}} markers and copies aux files."""
    project_root = tmp_path / "proj"
    manuscript = project_root / "manuscript"
    manuscript.mkdir(parents=True)
    (manuscript / "00_abstract.md").write_text(
        "# Abstract\n\n{{CONFIG_TITLE}} has {{TOTAL_WORDS}} words.\n",
        encoding="utf-8",
    )
    (manuscript / "01_intro.md").write_text(
        "# Intro\n\nNo tokens here.\n",
        encoding="utf-8",
    )
    (manuscript / "config.yaml").write_text("paper: {title: 'X'}\n", encoding="utf-8")
    (manuscript / "references.bib").write_text(
        "@article{k1, title={A}, year={2020}, author={X}}\n",
        encoding="utf-8",
    )

    vars_ = compute_variables(
        config_title="My Paper",
        manuscript_report=_payload(files=[_file("a.md", 7)]),
    )
    out_dir = write_resolved_manuscript_tree(project_root, vars_)

    assert out_dir == project_root / "output" / "manuscript"
    abstract = (out_dir / "00_abstract.md").read_text(encoding="utf-8")
    assert "{{CONFIG_TITLE}}" not in abstract
    assert "My Paper has 7 words." in abstract
    intro = (out_dir / "01_intro.md").read_text(encoding="utf-8")
    assert "No tokens here." in intro
    # Aux files copied through.
    assert (out_dir / "config.yaml").exists()
    assert (out_dir / "references.bib").exists()


def test_write_resolved_manuscript_tree_no_aux(tmp_path: Path):
    """Aux files are optional; tree write must succeed without them."""
    project_root = tmp_path / "proj"
    manuscript = project_root / "manuscript"
    manuscript.mkdir(parents=True)
    (manuscript / "00_abstract.md").write_text("# A\n\nplain text.\n", encoding="utf-8")
    vars_ = compute_variables(config_title="X", manuscript_report=_payload())
    out_dir = write_resolved_manuscript_tree(project_root, vars_)
    assert (out_dir / "00_abstract.md").exists()
    assert not (out_dir / "config.yaml").exists()
