from __future__ import annotations

from pathlib import Path

import pytest

from storybook.models import Character, PageSpec, RenderResult, StorybookSpec


def _page(number: int, slug: str) -> PageSpec:
    return PageSpec(
        number=number,
        slug=slug,
        title=f"Page {number}",
        scene="scene",
        text="story text",
        overlay_box=False,
        palette=("#111111", "#eeeeee", "#222222", "#dddddd"),
    )


def _spec(pages: tuple[PageSpec, ...]) -> StorybookSpec:
    character = Character(
        character_id="tessa",
        name="Tessa",
        shape="tetrahedron",
        family_shape="cube",
        fill="#e8f1f8",
        accent="#1d3557",
        role="protagonist",
    )
    return StorybookSpec(
        title="The Shape Between",
        subtitle="subtitle",
        output_pdf=Path("output/storybook.pdf"),
        page_width=800,
        page_height=1200,
        characters=(character,),
        pages=pages,
    )


def test_page_spec_filename_zero_pads_number() -> None:
    assert _page(3, "cover").filename == "03_cover.png"
    assert _page(12, "shared_home").filename == "12_shared_home.png"


def test_page_spec_caption_position_defaults_to_bottom() -> None:
    assert _page(1, "cover").caption_position == "bottom"


def test_storybook_spec_page_count_and_lookups() -> None:
    spec = _spec((_page(1, "cover"), _page(2, "shared_home")))
    assert spec.page_count == 2
    assert spec.page_by_slug("cover").number == 1
    assert spec.page_by_number(2).slug == "shared_home"
    with pytest.raises(KeyError, match="No storybook page with slug"):
        spec.page_by_slug("missing")
    with pytest.raises(KeyError, match="No storybook page numbered"):
        spec.page_by_number(9)


def test_render_result_to_dict_prefers_project_relative_paths(tmp_path: Path) -> None:
    output_dir = tmp_path / "output" / "pages"
    output_dir.mkdir(parents=True)
    image = output_dir / "03_cover.png"
    image.write_bytes(b"png")
    result = RenderResult(
        output_path=tmp_path / "output" / "storybook.pdf",
        page_count=1,
        image_paths=(image,),
        manifest_path=tmp_path / "output" / "manifest.json",
        summary_path=tmp_path / "output" / "summary.json",
        contact_sheet_path=None,
    )
    relative = result.to_dict(root=tmp_path)
    assert relative["output_path"] == "output/storybook.pdf"
    assert relative["image_paths"] == ["output/pages/03_cover.png"]
    assert relative["contact_sheet_path"] is None

    absolute = result.to_dict()
    assert str(absolute["output_path"]).startswith(str(tmp_path))
