"""Tests for table-of-contents numbering and label/title derivation."""

from __future__ import annotations

import pytest

from textbook.config import ChapterRef, iter_chapters, load_config
from textbook import toc


def _sample_chapter() -> ChapterRef:
    return ChapterRef(
        part_id="part_I",
        part_label="I",
        part_title="Fundamentals",
        directory="part_I",
        file="first_principles.md",
        title="First Principles",
        enabled=True,
    )


def test_build_toc_numbers_sequentially():
    config = load_config()
    entries = toc.build_toc(config)
    assert [e.number for e in entries] == list(range(1, len(entries) + 1))
    assert entries[0].number == 1


def test_chapter_number_found_and_missing():
    config = load_config()
    first = iter_chapters(config)[0]
    assert toc.chapter_number(config, first.part_id, first.file) == 1
    with pytest.raises(KeyError):
        toc.chapter_number(config, "nope", "nope.md")


def test_labels():
    ch = _sample_chapter()
    assert toc.section_label(ch) == "sec:part_I_first_principles"
    assert toc.lab_label(ch) == "sec:lab_part_I_first_principles"
    assert toc.question_label(ch) == "sec:q_part_I_first_principles"


def test_titles():
    assert toc.lab_title("X") == "Lab — X"
    assert toc.question_bank_title("X") == "Question Bank — X"


def test_toc_entry_fields():
    """TocEntry must carry all expected fields correctly."""
    config = load_config()
    entries = toc.build_toc(config)
    assert entries, "TOC must be non-empty"
    first = entries[0]
    assert first.number == 1
    assert first.part_id
    assert first.file.endswith(".md")
    assert first.title
    assert first.part_title


def test_build_toc_only_includes_enabled(tmp_path):
    """build_toc must skip disabled chapters (include_disabled=False by default)."""
    config = {
        "parts": [
            {
                "id": "p",
                "label": "I",
                "title": "Part",
                "directory": "p",
                "chapters": [
                    {"file": "a.md", "title": "A"},
                    {"file": "b.md", "title": "B", "enabled": False},
                    {"file": "c.md", "title": "C"},
                ],
            }
        ]
    }
    entries = toc.build_toc(config)
    assert len(entries) == 2
    assert [e.file for e in entries] == ["a.md", "c.md"]
    assert [e.number for e in entries] == [1, 2]


def test_section_lab_question_labels_are_unique_across_chapters():
    """All label types must be unique across the whole book."""
    config = load_config()
    chapters = iter_chapters(config)
    sec_labels = [toc.section_label(ch) for ch in chapters]
    lab_labels = [toc.lab_label(ch) for ch in chapters]
    q_labels = [toc.question_label(ch) for ch in chapters]
    assert len(sec_labels) == len(set(sec_labels)), "duplicate section labels"
    assert len(lab_labels) == len(set(lab_labels)), "duplicate lab labels"
    assert len(q_labels) == len(set(q_labels)), "duplicate question labels"
