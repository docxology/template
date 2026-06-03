"""Integrity tests binding the materialised manuscript to the engine contract.

These run against the real files under ``manuscript/`` so a hand-edit that drops
a required section, cites an undefined key, or links a missing glossary anchor
fails CI.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from textbook import content
from textbook.config import iter_chapters, load_config, validate_config
from textbook.constants import CITATION_KEYS, GLOSSARY_ANCHORS

MANUSCRIPT = Path(__file__).resolve().parent.parent / "manuscript"
CONFIG = load_config(MANUSCRIPT)
CHAPTERS = iter_chapters(CONFIG)


def test_config_is_valid():
    assert validate_config(CONFIG) == []


def test_all_chapters_exist_and_validate():
    missing = [c.file for c in CHAPTERS if not c.path(MANUSCRIPT).exists()]
    assert missing == [], f"missing chapter files: {missing}"
    for chapter in CHAPTERS:
        text = chapter.path(MANUSCRIPT).read_text(encoding="utf-8")
        assert content.validate_chapter(text) == [], f"{chapter.file} failed validation"


def test_every_chapter_has_lab_and_questions():
    for chapter in CHAPTERS:
        lab = MANUSCRIPT / "labs" / chapter.part_id / f"lab_{chapter.stem}.md"
        question = MANUSCRIPT / "questions" / chapter.part_id / f"q_{chapter.stem}.md"
        assert lab.exists(), f"missing lab: {lab}"
        assert question.exists(), f"missing question bank: {question}"


def test_references_define_every_contract_key():
    bib = (MANUSCRIPT / "references.bib").read_text(encoding="utf-8")
    defined = set(re.findall(r"@\w+\{([^,]+),", bib))
    assert set(CITATION_KEYS) <= defined, set(CITATION_KEYS) - defined


def test_glossary_defines_every_contract_anchor():
    glossary = (MANUSCRIPT / "glossary.md").read_text(encoding="utf-8")
    anchors = set(re.findall(r"\{#gl:([\w-]+)\}", glossary))
    assert set(GLOSSARY_ANCHORS) <= anchors, set(GLOSSARY_ANCHORS) - anchors


def test_chapters_only_cite_defined_keys():
    bib = (MANUSCRIPT / "references.bib").read_text(encoding="utf-8")
    defined = set(re.findall(r"@\w+\{([^,]+),", bib))
    for chapter in CHAPTERS:
        text = chapter.path(MANUSCRIPT).read_text(encoding="utf-8")
        cited = set(re.findall(r"@([A-Za-z][\w]+\d{4}\w+)", text))
        undefined = cited - defined
        assert undefined == set(), f"{chapter.file} cites undefined keys: {undefined}"


def test_chapters_only_link_defined_glossary_anchors():
    valid = set(GLOSSARY_ANCHORS)
    for chapter in CHAPTERS:
        text = chapter.path(MANUSCRIPT).read_text(encoding="utf-8")
        linked = set(re.findall(r"\(#gl:([\w-]+)\)", text))
        undefined = linked - valid
        assert undefined == set(), f"{chapter.file} links undefined anchors: {undefined}"


# --- appendices ------------------------------------------------------------


def _reference_appendix_paths() -> list[Path]:
    """Resolve every configured reference appendix to its file on disk."""
    refs = CONFIG.get("appendices", {}).get("reference", [])
    paths: list[Path] = []
    for entry in refs:
        candidate = MANUSCRIPT / "appendices" / entry["file"]
        paths.append(candidate if candidate.exists() else MANUSCRIPT / entry["file"])
    return paths


def test_all_reference_appendices_exist():
    missing = [p for p in _reference_appendix_paths() if not p.exists()]
    assert missing == [], f"missing reference appendices: {missing}"


def test_appendices_only_cite_and_link_defined_targets():
    bib = (MANUSCRIPT / "references.bib").read_text(encoding="utf-8")
    defined_keys = set(re.findall(r"@\w+\{([^,]+),", bib))
    anchors = set(GLOSSARY_ANCHORS)
    for path in _reference_appendix_paths():
        text = path.read_text(encoding="utf-8")
        cited = set(re.findall(r"@([A-Za-z][\w]+\d{4}\w+)", text))
        assert cited - defined_keys == set(), f"{path.name} cites undefined keys"
        linked = set(re.findall(r"\(#gl:([\w-]+)\)", text))
        assert linked - anchors == set(), f"{path.name} links undefined anchors"


# Finished reference chapters: (part_id, stem). Each must be fully filled —
# real prose, no stub markers — while still satisfying the structural contract.
WORKED_EXEMPLARS = [("part_I", "first_principles"), ("part_III", "case_studies")]


@pytest.mark.parametrize("part_id,stem", WORKED_EXEMPLARS, ids=[s for _, s in WORKED_EXEMPLARS])
def test_worked_exemplar_chapter_is_filled(part_id, stem):
    """The finished reference chapters carry real prose and no stub markers."""
    text = (MANUSCRIPT / part_id / f"{stem}.md").read_text(encoding="utf-8")
    assert content.validate_chapter(text) == []  # still satisfies the contract
    assert content.count_words(text) > 700  # substantially filled
    assert content.count_stub_markers(text) == 0  # nothing left to fill
    lab = (MANUSCRIPT / "labs" / part_id / f"lab_{stem}.md").read_text(encoding="utf-8")
    questions = (MANUSCRIPT / "questions" / part_id / f"q_{stem}.md").read_text(encoding="utf-8")
    assert content.count_stub_markers(lab) == 0
    assert content.count_stub_markers(questions) == 0


def test_format_gallery_figure_refs_match_generator():
    """Every ../figures/gallery/gallery_<name>.png reference must be producible."""
    from visualization.gallery import GALLERY

    producible = {f"gallery_{name}" for name, _ in GALLERY}
    gallery = (MANUSCRIPT / "appendices" / "appendix_format_gallery.md").read_text(encoding="utf-8")
    referenced = set(re.findall(r"figures/gallery/(gallery_[\w]+)\.png", gallery))
    assert referenced, "format gallery references no gallery figures"
    missing = referenced - producible
    assert missing == set(), f"format gallery references non-producible figures: {missing}"
