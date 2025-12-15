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


def test_render_summary_cards_empty() -> None:
    """Test render_summary_cards with empty list."""
    html = html_templates.render_summary_cards([])
    assert '<div class="summary-grid">' in html
    assert '</div>' in html


def test_render_summary_cards_single_card() -> None:
    """Test render_summary_cards with single card."""
    html = html_templates.render_summary_cards([{"title": "Total", "value": "100"}])
    assert "Total" in html
    assert "100" in html
    assert html.count("summary-card") == 1


def test_render_table_empty_rows() -> None:
    """Test render_table with empty rows."""
    html = html_templates.render_table(headers=["Name", "Status"], rows=[])
    assert "<table>" in html
    assert "<thead>" in html
    assert "<tbody>" in html
    assert "Name" in html
    assert "Status" in html


def test_render_table_multiple_rows() -> None:
    """Test render_table with multiple rows."""
    html = html_templates.render_table(
        headers=["Stage", "Status"],
        rows=[["setup", "passed"], ["tests", "failed"], ["analysis", "passed"]]
    )
    assert "setup" in html
    assert "tests" in html
    assert "analysis" in html
    assert html.count("<tr>") == 4  # 1 header + 3 data rows


def test_get_base_html_template_structure() -> None:
    """Test base HTML template has required structure."""
    template = html_templates.get_base_html_template()
    assert "<!DOCTYPE html>" in template
    assert "<html>" in template
    assert "<head>" in template
    assert "<body>" in template
    assert "<style>" in template
    assert "{title}" in template
    assert "{header}" in template
    assert "{content}" in template
    assert "{footer}" in template











