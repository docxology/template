"""Tests for config loading + validation against the real manuscript config."""

from __future__ import annotations


import pytest

from textbook.config import (
    DEFAULT_MANUSCRIPT,
    ChapterRef,
    UnitIntroRef,
    declared_chapter_paths,
    declared_unit_intro_paths,
    iter_chapters,
    iter_unit_intros,
    load_config,
    validate_config,
)


def test_iter_unit_intros_default():
    config = load_config()
    intros = iter_unit_intros(config)
    assert len(intros) == len(config["units"])
    first = intros[0]
    assert isinstance(first, UnitIntroRef)
    assert first.file == "unit_intro.md"
    assert first.path(DEFAULT_MANUSCRIPT).name == "unit_intro.md"


def test_declared_paths_cover_real_manuscript():
    config = load_config()
    chapter_paths = declared_chapter_paths(DEFAULT_MANUSCRIPT, config)
    intro_paths = declared_unit_intro_paths(DEFAULT_MANUSCRIPT, config)
    assert all(path.exists() for path in chapter_paths)
    assert all(path.exists() for path in intro_paths)


def test_validate_config_rejects_bad_intro_file():
    cfg = {
        "book": {"title": "t"},
        "units": [{"id": "p", "title": "P", "intro_file": "intro.txt", "chapters": [{"file": "a.md", "title": "A"}]}],
    }
    assert any("intro_file must end with .md" in issue for issue in validate_config(cfg))


def test_load_default_config_has_units():
    config = load_config()
    assert config["book"]["title"]
    assert isinstance(config["units"], list) and config["units"]


def test_load_config_from_directory(tmp_path):
    (tmp_path / "config.yaml").write_text("book:\n  title: T\nparts: []\n", encoding="utf-8")
    config = load_config(tmp_path)
    assert config["book"]["title"] == "T"


def test_load_config_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "nope.yaml")


def test_load_config_non_mapping(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("- a\n- b\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_config(path)


def test_iter_chapters_default_and_disabled():
    config = load_config()
    chapters = iter_chapters(config)
    # Derive the expected count from the config (single source of truth) rather
    # than a literal, so editing units/chapters in config.yaml — the edit the
    # template invites — does not break this test.
    enabled_in_config = sum(
        1 for unit in config.get("units", []) for chap in unit.get("chapters", []) if chap.get("enabled", True)
    )
    assert len(chapters) == enabled_in_config
    # Disabled chapters are excluded from the default view.
    assert len(iter_chapters(config, include_disabled=True)) >= len(chapters)
    first = chapters[0]
    assert isinstance(first, ChapterRef)
    assert first.stem == first.file[:-3]
    assert first.path(DEFAULT_MANUSCRIPT).name == first.file


def test_iter_chapters_respects_enabled_flag():
    config = {
        "parts": [
            {
                "id": "p",
                "label": "1",
                "title": "P",
                "directory": "p",
                "chapters": [
                    {"file": "a.md", "title": "A"},
                    {"file": "b.md", "title": "B", "enabled": False},
                ],
            }
        ]
    }
    assert len(iter_chapters(config)) == 1
    assert len(iter_chapters(config, include_disabled=True)) == 2


def test_validate_real_config_is_clean():
    assert validate_config(load_config()) == []


def test_validate_config_detects_problems():
    bad = {
        "book": {},
        "parts": [
            {"id": "x", "title": "", "chapters": [{"file": "a.md", "title": ""}]},
            {"id": "x", "title": "Dup", "chapters": [{"file": "a.md", "title": "A"}]},
            {"title": "noid", "chapters": []},
        ],
    }
    issues = validate_config(bad)
    joined = " ".join(issues)
    assert "book.title is required" in joined
    assert "duplicate part id: x" in joined
    assert "missing id" in joined
    assert "missing title" in joined


def test_validate_config_requires_nonempty_units():
    assert "units must be a non-empty list" in validate_config({"book": {"title": "t"}})


def test_iter_chapters_accepts_units_key():
    config = {
        "units": [
            {
                "id": "u",
                "label": "1",
                "title": "U",
                "directory": "u",
                "chapters": [{"file": "a.md", "title": "A"}],
            }
        ]
    }
    chapters = iter_chapters(config)
    assert len(chapters) == 1 and chapters[0].part_id == "u"


def test_validate_config_chapter_without_file():
    cfg = {
        "book": {"title": "t"},
        "parts": [{"id": "p", "title": "P", "chapters": [{"title": "no file"}]}],
    }
    assert any("chapter with no file" in i for i in validate_config(cfg))


def test_validate_config_part_with_empty_chapter_list():
    """A part with an empty chapters list is reported and no chapter loop runs."""
    cfg = {
        "book": {"title": "t"},
        "parts": [{"id": "p", "title": "P", "chapters": []}],
    }
    issues = validate_config(cfg)
    assert any("has no chapters" in i for i in issues)


def test_validate_config_part_with_null_chapters():
    """A part whose 'chapters' key is missing or None is also reported."""
    cfg = {
        "book": {"title": "t"},
        "parts": [{"id": "p", "title": "P"}],  # no 'chapters' key
    }
    issues = validate_config(cfg)
    assert any("has no chapters" in i for i in issues)


def test_validate_config_duplicate_chapter_file():
    """Two chapters with the same file within the same part are flagged."""
    cfg = {
        "book": {"title": "t"},
        "parts": [
            {
                "id": "p",
                "title": "P",
                "chapters": [
                    {"file": "a.md", "title": "A"},
                    {"file": "a.md", "title": "A-dup"},
                ],
            }
        ],
    }
    issues = validate_config(cfg)
    assert any("duplicate chapter file" in i for i in issues)
