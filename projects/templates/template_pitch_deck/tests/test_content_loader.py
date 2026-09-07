"""No-mocks tests for src/content_loader.py."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from content_loader import build_deck_content, load_deck_yaml, raw_deck_texts
from deck_tokens import build_deck_tokens
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.rendering.slide_deck import SlideBudget
from paths import locate_repo_root, project_root

_ROSTER_TITLE = "The full roster, not one cherry-picked example"
_CONTRACT_TITLE = "One contract across all public exemplars"
_ROSTER_CLAIMS = (
    "projects/templates/ holds all {{EXEMPLAR_COUNT}} public exemplars: {{EXEMPLAR_ROSTER}}.",
    "{{SECOND_EXEMPLAR_NAME}} is called out here only as one concrete instance to point to — "
    "every name in that list is an independently-built exemplar following the identical two-layer architecture, "
    "not a hand-picked best case.",
    "Neither exemplar's coverage gate or drift check required any special-casing to add — the contract is uniform "
    "across all {{EXEMPLAR_COUNT}} projects, and the folder itself is the evidence, not a claim about it.",
)
_SHORTENED_INFRA_SCOPE_CLAIM = (
    "The next chart narrows the total to importable subpackages, excluding {{INFRA_UNATTRIBUTED_FILE_COUNT}} "
    "top-level file(s): infrastructure/__init__.py and mcp_server.py."
)


def test_load_deck_yaml_reads_real_file(tmp_path: Path):
    content_path = tmp_path / "deck.yaml"
    content_path.write_text(
        yaml.safe_dump({"title": "T", "subtitle": "S", "slides": [{"title": "One", "bullets": ["a", "b"]}]}),
        encoding="utf-8",
    )
    raw = load_deck_yaml(content_path)
    assert raw["title"] == "T"
    assert raw["slides"][0]["title"] == "One"


def test_raw_deck_texts_flattens_title_subtitle_and_slides():
    raw = {
        "title": "Deck Title",
        "subtitle": "Deck Subtitle",
        "slides": [
            {"title": "Slide One", "bullets": ["bullet a", "bullet b"]},
            {"title": "Slide Two", "bullets": [], "notes": "a note"},
        ],
    }
    texts = raw_deck_texts(raw)
    assert texts["title"] == "Deck Title"
    assert texts["subtitle"] == "Deck Subtitle"
    assert texts["slide[0].title"] == "Slide One"
    assert texts["slide[0].bullets[0]"] == "bullet a"
    assert texts["slide[0].bullets[1]"] == "bullet b"
    assert texts["slide[1].title"] == "Slide Two"
    assert texts["slide[1].notes"] == "a note"


def test_raw_deck_texts_omits_notes_field_when_absent():
    raw = {"title": "T", "slides": [{"title": "S", "bullets": []}]}
    texts = raw_deck_texts(raw)
    assert "slide[0].notes" not in texts


def test_raw_deck_texts_includes_stat_and_quote_fields():
    raw = {
        "title": "T",
        "slides": [
            {"title": "Stat", "kind": "stat", "stat_value": "89 tests", "stat_label": "coverage"},
            {"title": "", "kind": "quote", "quote_text": "A quote.", "quote_attribution": "Someone"},
        ],
    }
    texts = raw_deck_texts(raw)
    assert texts["slide[0].stat_value"] == "89 tests"
    assert texts["slide[0].stat_label"] == "coverage"
    assert texts["slide[1].quote_text"] == "A quote."
    assert texts["slide[1].quote_attribution"] == "Someone"


def test_raw_deck_texts_omits_empty_stat_and_quote_fields():
    raw = {"title": "T", "slides": [{"title": "S", "bullets": []}]}
    texts = raw_deck_texts(raw)
    for field_name in ("stat_value", "stat_label", "quote_text", "quote_attribution"):
        assert f"slide[0].{field_name}" not in texts


def test_build_deck_content_resolves_tokens_across_all_fields():
    raw = {
        "title": "{{TITLE}}",
        "subtitle": "{{SUBTITLE}}",
        "slides": [
            {"kind": "title", "title": "{{TITLE}}"},
            {"kind": "content", "title": "Point", "bullets": ["{{FACT}}"]},
        ],
    }
    tokens = {"TITLE": "My Deck", "SUBTITLE": "A subtitle", "FACT": "42 tests"}
    deck = build_deck_content(raw, tokens)

    assert deck.title == "My Deck"
    assert deck.subtitle == "A subtitle"
    assert deck.slides[0].kind == "title"
    assert deck.slides[0].title == "My Deck"
    assert deck.slides[1].bullets == ("42 tests",)


def test_build_deck_content_attaches_figure_path_when_figures_dir_given(tmp_path: Path):
    raw = {"title": "T", "slides": [{"title": "S", "bullets": [], "figure": "chart.png"}]}
    deck = build_deck_content(raw, {}, figures_dir=tmp_path)
    assert deck.slides[0].figure_path == tmp_path / "chart.png"


def test_build_deck_content_figure_path_is_none_without_figures_dir():
    raw = {"title": "T", "slides": [{"title": "S", "bullets": [], "figure": "chart.png"}]}
    deck = build_deck_content(raw, {})
    assert deck.slides[0].figure_path is None


def test_build_deck_content_defaults_kind_to_content():
    raw = {"title": "T", "slides": [{"title": "S", "bullets": []}]}
    deck = build_deck_content(raw, {})
    assert deck.slides[0].kind == "content"


def test_build_deck_content_resolves_stat_and_quote_fields():
    raw = {
        "title": "T",
        "slides": [
            {"title": "Proof", "kind": "stat", "stat_value": "{{N}} tests", "stat_label": "{{PCT}}% coverage"},
            {"title": "", "kind": "quote", "quote_text": "By {{WHO}}.", "quote_attribution": "{{WHO}}"},
        ],
    }
    tokens = {"N": "89", "PCT": "91", "WHO": "Ada"}
    deck = build_deck_content(raw, tokens)

    assert deck.slides[0].stat_value == "89 tests"
    assert deck.slides[0].stat_label == "91% coverage"
    assert deck.slides[1].quote_text == "By Ada."
    assert deck.slides[1].quote_attribution == "Ada"


def test_build_deck_content_defaults_stat_and_quote_fields_to_empty():
    raw = {"title": "T", "slides": [{"title": "S", "bullets": []}]}
    deck = build_deck_content(raw, {})
    assert deck.slides[0].stat_value == ""
    assert deck.slides[0].stat_label == ""
    assert deck.slides[0].quote_text == ""
    assert deck.slides[0].quote_attribution == ""


def test_build_deck_content_copies_source_through_verbatim_without_token_resolution():
    raw = {"title": "T", "slides": [{"title": "S", "bullets": [], "source": "path/with/{{NOT_A_TOKEN_CALL}}.py"}]}
    deck = build_deck_content(raw, {})
    assert deck.slides[0].source == "path/with/{{NOT_A_TOKEN_CALL}}.py"


def test_build_deck_content_defaults_source_to_empty_string():
    raw = {"title": "T", "slides": [{"title": "S", "bullets": []}]}
    deck = build_deck_content(raw, {})
    assert deck.slides[0].source == ""


@pytest.mark.parametrize(
    ("content_filename", "expected_slide_count", "budget"),
    (
        pytest.param("deck_content_medium.yaml", 38, SlideBudget.MEDIUM, id="medium"),
        pytest.param("deck_content_long.yaml", 57, SlideBudget.LONG, id="long"),
    ),
)
def test_flagship_roster_split_preserves_all_claims_names_sources_and_budget(
    content_filename: str,
    expected_slide_count: int,
    budget: SlideBudget,
):
    pitch_root = project_root()
    raw = load_deck_yaml(pitch_root / "manuscript" / content_filename)
    raw_slides = raw["slides"]
    by_title = {slide["title"]: slide for slide in raw_slides}
    roster_slide = by_title[_ROSTER_TITLE]
    contract_slide = by_title[_CONTRACT_TITLE]

    assert len(raw_slides) == expected_slide_count
    assert expected_slide_count <= budget.max_slides
    assert roster_slide["bullets"] == [_ROSTER_CLAIMS[0]]
    assert contract_slide["bullets"] == list(_ROSTER_CLAIMS[1:])
    assert roster_slide["source"] == contract_slide["source"] == "docs/_generated/active_projects.md"
    assert by_title["Not a black box"]["bullets"][3] == _SHORTENED_INFRA_SCOPE_CLAIM

    repo_root = locate_repo_root(pitch_root)
    deck = build_deck_content(raw, build_deck_tokens(repo_root))
    resolved_roster_slide = next(slide for slide in deck.slides if slide.title == _ROSTER_TITLE)
    expected_names = sorted(name.rsplit("/", 1)[-1] for name in PUBLIC_PROJECT_NAMES)
    roster_prefix = f"projects/templates/ holds all {len(expected_names)} public exemplars: "
    resolved_roster = resolved_roster_slide.bullets[0]
    assert resolved_roster.startswith(roster_prefix)
    roster_names = resolved_roster.removeprefix(roster_prefix).removesuffix(".").split(", ")
    assert roster_names == expected_names
