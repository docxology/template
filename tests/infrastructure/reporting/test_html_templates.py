from __future__ import annotations

from infrastructure.reporting import html_templates


def test_get_base_html_template_has_placeholders() -> None:
    template = html_templates.get_base_html_template()
    assert "{title}" in template
    assert "{header}" in template
    assert "{content}" in template


def test_render_summary_cards_and_table() -> None:
    cards_html = html_templates.render_summary_cards(
        [{"title": "Tests", "value": "10"}, {"title": "Passed", "value": "9"}]
    )
    assert "Tests" in cards_html
    assert "9" in cards_html

    table_html = html_templates.render_table(headers=["Name", "Status"], rows=[["setup", "passed"]])
    assert "<table>" in table_html
    assert "setup" in table_html

