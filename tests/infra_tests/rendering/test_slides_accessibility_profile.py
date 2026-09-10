"""Slides accessibility profile and configuration boundary tests (split from test_slides_accessibility.py)."""

from __future__ import annotations

from typing import Any
import pytest
from infrastructure.rendering._slides_accessibility import AccessibleSlidePolicy
from infrastructure.rendering.config import RenderingConfig


def test_archive_profile_remains_the_default_and_accessible_defaults_are_exact() -> None:
    config = RenderingConfig()

    assert config.slides_profile == "archive"
    assert config.accessible_slide_policy() == AccessibleSlidePolicy(
        max_prose_words=80,
        max_table_rows=8,
        min_figure_area_percent=70,
        title_font_pt=28,
        body_font_pt=20,
        figure_label_font_pt=16,
        reader_href="../web/index.html",
    )


def test_accessible_profile_loads_strict_yaml_and_environment_overrides() -> None:
    project = {
        "render": {
            "slides": {
                "profile": "accessible",
                "max_prose_words": 80,
                "max_table_rows": 8,
                "min_figure_area_percent": 70,
                "title_font_pt": 28,
                "body_font_pt": 20,
                "figure_label_font_pt": 16,
                "reader_href": "reader/index.html",
            }
        }
    }

    config = RenderingConfig.from_project_config(
        project,
        env={"SLIDES_MAX_PROSE_WORDS": "72", "SLIDES_READER_HREF": "https://example.org/manuscript"},
    )

    assert config.slides_profile == "accessible"
    assert config.slides_max_prose_words == 72
    assert config.slides_reader_href == "https://example.org/manuscript"


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"render": {"slides": {"body_font_pt": 19}}}, "slides_body_font_pt"),
        ({"render": {"slides": {"max_prose_words": 81}}}, "slides_max_prose_words"),
        ({"render": {"slides": {"max_table_rows": 9}}}, "slides_max_table_rows"),
        ({"render": {"slides": {"max_table_rows": True}}}, "must be an integer"),
        ({"render": {"slides": {"unexpected": 1}}}, "unknown fields"),
        ({"render": {"slides": []}}, "must be a mapping"),
    ],
)
def test_accessible_profile_rejects_weakened_or_unknown_configuration(
    payload: dict[str, Any],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        RenderingConfig.from_project_config(payload, env={})


@pytest.mark.parametrize(
    "reader_href",
    ["javascript:alert(1)", "/machine/local/index.html", r"..\web\index.html", ""],
)
def test_accessible_profile_rejects_unsafe_reader_links(reader_href: str) -> None:
    with pytest.raises(ValueError, match="slides_reader_href"):
        RenderingConfig(slides_reader_href=reader_href)
