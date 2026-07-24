from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from PIL import Image

from storybook import build_storybook_pdf, load_storybook, render_story_number, render_story_page
from storybook.text_layout import contrast_ratio, validate_text_contrast


def _pdf_page_count(data: bytes) -> int:
    return data.count(b"/Type /Page") - data.count(b"/Type /Pages")


def _pdf_media_box(data: bytes) -> tuple[float, float]:
    """Extract the (width, height) of the first /MediaBox entry in a PDF."""
    match = re.search(rb"/MediaBox\s*\[\s*[\d.]+\s+[\d.]+\s+([\d.]+)\s+([\d.]+)\s*\]", data)
    assert match is not None, "no /MediaBox found in PDF bytes"
    return float(match.group(1)), float(match.group(2))


def _write_single_page_project(project_root: Path, *, page_width: int, page_height: int) -> Path:
    """Build a minimal isolated storybook project with a custom, non-3:4 page size."""
    story_path = project_root / "content" / "story.yaml"
    payload = yaml.safe_load(story_path.read_text(encoding="utf-8"))
    payload["storybook"]["page_width"] = page_width
    payload["storybook"]["page_height"] = page_height
    payload["pages"] = [
        {
            "number": 0,
            "slug": "cover",
            "title": "The Shape Between",
            "scene": "cosmic_yinyang",
            "overlay_box": False,
            "palette": ["#0b1026", "#f3e8d9", "#ffcf56", "#5ed6df"],
            "text": "A single-page fixture for a non-3:4 page size.",
        }
    ]
    story_path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    return project_root


def test_render_single_page_image_is_full_page(isolated_project, tmp_path) -> None:
    spec = load_storybook(isolated_project)
    out = tmp_path / "cover.png"
    path = render_story_page(isolated_project, "cover")
    copied = Image.open(path)
    copied.save(out)
    image = Image.open(out)
    colors = image.resize((32, 32)).getcolors(maxcolors=4096)
    assert image.size == (spec.page_width, spec.page_height)
    assert colors is not None
    assert len(colors) > 20


def test_build_storybook_pdf_writes_manifest_and_pdf(isolated_project) -> None:
    spec = load_storybook(isolated_project)
    result = build_storybook_pdf(isolated_project)
    data = result.output_path.read_bytes()
    assert data.startswith(b"%PDF-")
    assert _pdf_page_count(data) == result.page_count
    assert result.manifest_path.is_file()
    assert result.summary_path.is_file()
    assert result.contact_sheet_path is not None
    assert result.contact_sheet_path.is_file()
    assert len(result.image_paths) == result.page_count
    assert _pdf_media_box(data) == (float(spec.page_width), float(spec.page_height))


def test_build_storybook_pdf_respects_square_page_size(isolated_project) -> None:
    """A square (1:1) page size is not a 3:4 ratio like the default 1275x1650 config.

    This would have caught the original bug where the PDF canvas was hardcoded to
    `reportlab.lib.pagesizes.letter` (612x792, also 3:4) and the configured PNG was
    stretched into it with `preserveAspectRatio=False` — a distortion that was
    invisible only because 1275/1650 and 612/792 both reduce to 3:4.
    """
    _write_single_page_project(isolated_project, page_width=900, page_height=900)
    spec = load_storybook(isolated_project)
    assert spec.page_width == spec.page_height  # sanity: genuinely non-3:4 vs. the default

    result = build_storybook_pdf(isolated_project)
    data = result.output_path.read_bytes()
    assert data.startswith(b"%PDF-")
    assert _pdf_media_box(data) == (900.0, 900.0)


def test_build_storybook_pdf_respects_widescreen_page_size(isolated_project) -> None:
    """A 16:9 page size is another ratio distinct from the default 3:4 config."""
    _write_single_page_project(isolated_project, page_width=1600, page_height=900)

    result = build_storybook_pdf(isolated_project)
    data = result.output_path.read_bytes()
    assert data.startswith(b"%PDF-")
    assert _pdf_media_box(data) == (1600.0, 900.0)


def test_storybook_manifest_contains_alt_text_and_contact_sheet(isolated_project) -> None:
    result = build_storybook_pdf(isolated_project)
    manifest = yaml.safe_load(result.manifest_path.read_text(encoding="utf-8"))

    assert manifest["pages"][0]["alt_text"]
    assert manifest["render"]["contact_sheet_path"] == "output/figures/storybook_contact_sheet.png"
    assert len(manifest["render"]["text_contrast_audit"]) == 14
    assert all(row["ink_present"] for row in manifest["render"]["text_contrast_audit"])
    assert str(isolated_project) not in json.dumps(manifest)


def test_text_overlay_palette_meets_wcag_contrast() -> None:
    assert validate_text_contrast() >= 4.5
    assert contrast_ratio((255, 255, 255), (255, 255, 255)) == 1.0


def test_build_storybook_pdf_removes_stale_page_images(isolated_project) -> None:
    stale_dir = isolated_project / "output" / "figures" / "storybook_pages"
    stale_dir.mkdir(parents=True)
    stale = stale_dir / "99_retired_page.png"
    stale.write_bytes(b"old page")

    build_storybook_pdf(isolated_project)

    assert not stale.exists()


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))


def test_family_pages_use_dedicated_family_character_colors(isolated_project) -> None:
    """cube_family/tetra_family in content/story.yaml must actually be consumed.

    Their names ("The Square House" / "The Pointed House") match the titles of
    the square_house/pointed_house pages, so their fill colors should show up on
    those pages rather than the pages only ever reusing tessa's/ciro's own colors.
    """
    spec = load_storybook(isolated_project)
    cube_family = next(character for character in spec.characters if character.character_id == "cube_family")
    tetra_family = next(character for character in spec.characters if character.character_id == "tetra_family")

    square_house_path = render_story_number(isolated_project, 2)
    pointed_house_path = render_story_number(isolated_project, 3)

    square_house_image = Image.open(square_house_path).convert("RGB")
    pointed_house_image = Image.open(pointed_house_path).convert("RGB")
    square_house_colors = {
        rgb for _, rgb in square_house_image.getcolors(maxcolors=square_house_image.width * square_house_image.height)
    }
    pointed_house_colors = {
        rgb
        for _, rgb in pointed_house_image.getcolors(maxcolors=pointed_house_image.width * pointed_house_image.height)
    }

    assert _hex_to_rgb(cube_family.fill) in square_house_colors
    assert _hex_to_rgb(tetra_family.fill) in pointed_house_colors


_TITLE_INK = (24, 28, 42)


def _colors_in_top_strip(path: Path) -> set[tuple[int, int, int]]:
    strip = Image.open(path).convert("RGB").crop((0, 60, 1275, 220))
    return {rgb for _, rgb in strip.getcolors(maxcolors=strip.width * strip.height)}


def test_caption_position_config_moves_overlay_caption(isolated_project) -> None:
    """`caption_position` in story.yaml, not a hardcoded page slug, controls caption placement.

    square_house (page 2) has `overlay_box: true` and defaults to `caption_position: "bottom"`,
    so its title ink should not appear near the top of the page. Flipping the story.yaml
    value to "top" (the same mechanism content/story.yaml already uses for the mega_symbol
    page) must move the caption near the top — proving the knob is actually consumed by
    src/storybook/text_layout.py, not just present in the schema.
    """
    baseline_path = render_story_number(isolated_project, 2)
    assert _TITLE_INK not in _colors_in_top_strip(baseline_path)

    story_path = isolated_project / "content" / "story.yaml"
    payload = yaml.safe_load(story_path.read_text(encoding="utf-8"))
    assert payload["pages"][2]["slug"] == "square_house"
    payload["pages"][2]["caption_position"] = "top"
    story_path.write_text(yaml.safe_dump(payload), encoding="utf-8")

    overridden_path = render_story_number(isolated_project, 2)
    assert _TITLE_INK in _colors_in_top_strip(overridden_path)


def test_invalid_caption_position_fails(isolated_project) -> None:
    story_path = isolated_project / "content" / "story.yaml"
    payload = yaml.safe_load(story_path.read_text(encoding="utf-8"))
    payload["pages"][2]["caption_position"] = "middle"
    story_path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    with pytest.raises(ValueError):
        load_storybook(isolated_project)


def test_render_story_number_uses_configured_filename(isolated_project) -> None:
    path = render_story_number(isolated_project, 2)
    assert path.name == "02_square_house.png"
    assert path.is_file()
    final_path = render_story_number(isolated_project, 13)
    assert final_path.name == "13_shared_home.png"
    assert final_path.is_file()


def test_page_script_accepts_project_root(isolated_project, project_root) -> None:
    script = project_root / "scripts" / "20_render_page_01.py"
    completed = subprocess.run(
        [sys.executable, str(script), "--project-root", str(isolated_project)],
        check=True,
        capture_output=True,
        text=True,
    )
    rendered = isolated_project / "output" / "figures" / "storybook_pages" / "01_publication_information.png"
    assert str(rendered) in completed.stdout
    assert rendered.is_file()
