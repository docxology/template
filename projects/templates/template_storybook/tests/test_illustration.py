from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from storybook import load_storybook
from storybook.illustration import draw_cube, draw_tetrahedron, render_page_image


def _canvas(size: tuple[int, int] = (320, 240)) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGBA", size, (255, 255, 255, 255))
    return image, ImageDraw.Draw(image)


def test_draw_tetrahedron_and_cube_mark_the_canvas() -> None:
    for draw_shape in (draw_tetrahedron, draw_cube):
        image, draw = _canvas()
        before = image.tobytes()
        draw_shape(draw, (160, 120), 90, "#e8f1f8", "#1d3557")
        assert image.tobytes() != before


def test_draw_functions_are_deterministic() -> None:
    first, first_draw = _canvas()
    second, second_draw = _canvas()
    draw_cube(first_draw, (160, 120), 90, "#ffffff", "#111111")
    draw_cube(second_draw, (160, 120), 90, "#ffffff", "#111111")
    assert first.tobytes() == second.tobytes()


def test_render_page_image_writes_sized_png(project_root: Path, tmp_path: Path) -> None:
    spec = load_storybook(project_root)
    for slug in ("cover", "tetra_inside_cube"):
        page = spec.page_by_slug(slug)
        out = render_page_image(spec, page, tmp_path / page.filename)
        assert out.exists()
        with Image.open(out) as rendered:
            assert rendered.size == (spec.page_width, spec.page_height)
