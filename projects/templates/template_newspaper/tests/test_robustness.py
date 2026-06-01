"""Robustness tests — the silent-failure modes surfaced by cross-vendor audit.

These bind the fixes for: over-tall boxes (must be detected, not shrunk),
unescaped author markup (must not corrupt or crash), and the strict-loader
contract for figures and pull blocks.
"""

from __future__ import annotations

import pytest

from newspaper.components import _esc
from newspaper.config import NewspaperConfig
from newspaper.content import Block, Box, Edition, Figure, Page, Story, _parse_block, _parse_figure
from newspaper.engine import render_edition


# --- C1: over-tall boxes are detected, not silently shrunk -------------------

def test_over_tall_box_is_detected_as_overset(tmp_path) -> None:
    tall = Box(kind="generic", title="Huge", items=[f"line {i}" for i in range(400)])
    page = Page(number=1, template="standard", columns=2, main_items=[tall])
    edition = Edition(nameplate="T", city="C", state="S", date="D", pages=[page])
    result = render_edition(edition, NewspaperConfig(), project_root=tmp_path, output_path=tmp_path / "o.pdf")
    assert not result.all_pages_fit
    assert result.oversets.get(1, 0) > 0


# --- H1: author markup is escaped, not corrupted ----------------------------

def test_esc_escapes_bare_ampersand() -> None:
    assert _esc("AT&T merger") == "AT&amp;T merger"


def test_esc_escapes_angle_brackets() -> None:
    assert _esc("5 < 10 and x > y") == "5 &lt; 10 and x &gt; y"


def test_esc_preserves_allowed_markup() -> None:
    assert _esc("keep <b>bold</b> and <i>italic</i><br/>") == "keep <b>bold</b> and <i>italic</i><br/>"


def test_esc_does_not_double_escape_entities() -> None:
    assert _esc("Local &amp; Region") == "Local &amp; Region"


def test_esc_preserves_font_tag() -> None:
    s = 'caption <font name="NP-Body">/ credit</font>'
    assert _esc(s) == s


def test_render_with_ampersand_content_does_not_crash(tmp_path) -> None:
    story = Story(headline="AT&T & R&D < gains", body=[Block("p", "Revenue rose 5% as A&B and X<Y resolved.")])
    page = Page(number=1, template="standard", columns=2, main_items=[story])
    edition = Edition(nameplate="T&T", city="C", state="S", date="D", pages=[page])
    result = render_edition(edition, NewspaperConfig(), project_root=tmp_path, output_path=tmp_path / "amp.pdf")
    assert result.page_count == 1


# --- M1/M2/M3: strict-loader contract ---------------------------------------

def test_figure_requires_path() -> None:
    with pytest.raises(ValueError):
        Figure(path="")
    with pytest.raises(ValueError) as exc:
        _parse_figure({"caption": "no path"})
    assert "path" in str(exc.value)


def test_figure_rejects_nonpositive_height() -> None:
    with pytest.raises(ValueError):
        Figure(path="x.png", height=0)
    with pytest.raises(ValueError):
        _parse_figure({"path": "x.png", "height": "tall"})


def test_pull_block_as_list_raises_named_error() -> None:
    with pytest.raises(ValueError):
        _parse_block({"pull": ["not", "a", "mapping"]})
