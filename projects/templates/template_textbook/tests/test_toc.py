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
