"""Tests for infrastructure.reporting.html_templates."""

from __future__ import annotations

from infrastructure.reporting.html_templates import (
    get_base_html_template,
    render_summary_cards,
    render_table,
)


def test_base_template_has_placeholders():
    template = get_base_html_template()
    assert "{title}" in template
    assert "{content}" in template
    assert "{header}" in template


def test_render_summary_cards_and_table():
    cards_html = render_summary_cards(
        [{"title": "A", "value": "1"}, {"title": "B", "value": "2"}]
    )
    assert "summary-card" in cards_html
    assert "A" in cards_html and "B" in cards_html

    table_html = render_table(["H1", "H2"], [["a", "b"], ["c", "d"]])
    assert "<th>H1</th>" in table_html
    assert "<td>a</td>" in table_html


