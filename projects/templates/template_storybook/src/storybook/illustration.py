from __future__ import annotations

import hashlib
import math
import random
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .characters import child_pair
from .models import Character, PageSpec, StorybookSpec

RGB = tuple[int, int, int]


def _hex(color: str) -> RGB:
    color = color.lstrip("#")
    return (int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16))


def _mix(a: RGB, b: RGB, amount: float) -> RGB:
    return (
        int(a[0] + (b[0] - a[0]) * amount),
        int(a[1] + (b[1] - a[1]) * amount),
        int(a[2] + (b[2] - a[2]) * amount),
    )


def _font(size: int, *, bold: bool = False) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Avenir Next.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/Library/Fonts/Arial.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _gradient(width: int, height: int, top: RGB, bottom: RGB) -> Image.Image:
    image = Image.new("RGB", (width, height), top)
    draw = ImageDraw.Draw(image)
    for y in range(height):
        color = _mix(top, bottom, y / max(1, height - 1))
        draw.line((0, y, width, y), fill=color)
    return image


def _seed(slug: str) -> random.Random:
    digest = hashlib.sha256(slug.encode("utf-8")).hexdigest()
    return random.Random(int(digest[:12], 16))


def _draw_stars(draw: ImageDraw.ImageDraw, slug: str, width: int, height: int, color: RGB) -> None:
    rng = _seed(slug)
    for _ in range(95):
        x = rng.randint(20, width - 20)
        y = rng.randint(20, height - 20)
        radius = rng.choice([2, 3, 4, 5])
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)


def _draw_yinyang(draw: ImageDraw.ImageDraw, cx: int, cy: int, radius: int, light: RGB, dark: RGB) -> None:
    box = (cx - radius, cy - radius, cx + radius, cy + radius)
    draw.ellipse(box, fill=light)
    draw.pieslice(box, 90, 270, fill=dark)
    small = radius // 2
    draw.ellipse((cx - small, cy - radius, cx + small, cy), fill=light)
    draw.ellipse((cx - small, cy, cx + small, cy + radius), fill=dark)
    dot = radius // 8
    draw.ellipse((cx - dot, cy - radius // 2 - dot, cx + dot, cy - radius // 2 + dot), fill=dark)
    draw.ellipse((cx - dot, cy + radius // 2 - dot, cx + dot, cy + radius // 2 + dot), fill=light)
    draw.ellipse(box, outline=_mix(light, dark, 0.45), width=max(4, radius // 70))


def _tetra_points(
    cx: int, cy: int, size: int
) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int], tuple[int, int]]:
    top = (cx, cy - size)
    left = (cx - int(size * 0.86), cy + int(size * 0.55))
    right = (cx + int(size * 0.86), cy + int(size * 0.55))
    inner = (cx, cy + int(size * 0.15))
    return top, left, right, inner


def draw_tetrahedron(
    draw: ImageDraw.ImageDraw,
    center: tuple[int, int],
    size: int,
    fill: str,
    accent: str,
) -> None:
    cx, cy = center
    fill_rgb = _hex(fill)
    accent_rgb = _hex(accent)
    top, left, right, inner = _tetra_points(cx, cy, size)
    shadow = (cx - int(size * 0.62), cy + int(size * 0.55), cx + int(size * 0.62), cy + int(size * 0.75))
    draw.ellipse(shadow, fill=(0, 0, 0, 45))
    draw.polygon((top, left, inner), fill=_mix(fill_rgb, (255, 255, 255), 0.25), outline=accent_rgb)
    draw.polygon((top, inner, right), fill=fill_rgb, outline=accent_rgb)
    draw.polygon((left, right, inner), fill=_mix(fill_rgb, accent_rgb, 0.25), outline=accent_rgb)
    draw.line((top, inner), fill=accent_rgb, width=max(3, size // 18))
    eye_y = cy - size // 18
    draw.ellipse((cx - size // 4 - 8, eye_y - 8, cx - size // 4 + 8, eye_y + 8), fill=accent_rgb)
    draw.ellipse((cx + size // 4 - 8, eye_y - 8, cx + size // 4 + 8, eye_y + 8), fill=accent_rgb)
    draw.arc((cx - size // 5, eye_y + 20, cx + size // 5, eye_y + 60), 0, 180, fill=accent_rgb, width=4)


def draw_cube(
    draw: ImageDraw.ImageDraw,
    center: tuple[int, int],
    size: int,
    fill: str,
    accent: str,
) -> None:
    cx, cy = center
    fill_rgb = _hex(fill)
    accent_rgb = _hex(accent)
    half = size // 2
    shift = int(size * 0.28)
    front = [
        (cx - half, cy - half + shift),
        (cx + half, cy - half + shift),
        (cx + half, cy + half + shift),
        (cx - half, cy + half + shift),
    ]
    top = [
        (cx - half, cy - half + shift),
        (cx - half + shift, cy - half),
        (cx + half + shift, cy - half),
        (cx + half, cy - half + shift),
    ]
    side = [
        (cx + half, cy - half + shift),
        (cx + half + shift, cy - half),
        (cx + half + shift, cy + half),
        (cx + half, cy + half + shift),
    ]
    draw.ellipse((cx - half, cy + half + shift - 8, cx + half + shift, cy + half + shift + 28), fill=(0, 0, 0, 45))
    draw.polygon(top, fill=_mix(fill_rgb, (255, 255, 255), 0.32), outline=accent_rgb)
    draw.polygon(side, fill=_mix(fill_rgb, accent_rgb, 0.22), outline=accent_rgb)
    draw.polygon(front, fill=fill_rgb, outline=accent_rgb)
    draw.line(
        (cx - half, cy - half + shift, cx + half, cy + half + shift), fill=_mix(fill_rgb, accent_rgb, 0.35), width=3
    )
    eye_y = cy + shift
    draw.ellipse((cx - size // 5 - 8, eye_y - 8, cx - size // 5 + 8, eye_y + 8), fill=accent_rgb)
    draw.ellipse((cx + size // 5 - 8, eye_y - 8, cx + size // 5 + 8, eye_y + 8), fill=accent_rgb)
    draw.arc((cx - size // 5, eye_y + 24, cx + size // 5, eye_y + 64), 0, 180, fill=accent_rgb, width=4)


def _draw_character(draw: ImageDraw.ImageDraw, character: Character, center: tuple[int, int], size: int) -> None:
    if character.shape == "cube":
        draw_cube(draw, center, size, character.fill, character.accent)
    else:
        draw_tetrahedron(draw, center, size, character.fill, character.accent)


def _draw_family(draw: ImageDraw.ImageDraw, character: Character, centers: list[tuple[int, int]], size: int) -> None:
    for index, center in enumerate(centers):
        scale = size - (index % 2) * max(8, size // 8)
        if character.family_shape == "cube":
            draw_cube(draw, center, scale, character.fill, character.accent)
        else:
            draw_tetrahedron(draw, center, scale, character.fill, character.accent)


def _overlay_text(image: Image.Image, page: PageSpec) -> None:
    draw = ImageDraw.Draw(image, "RGBA")
    width, height = image.size
    title_font = _font(58, bold=True)
    text_font = _font(37)
    margin = 86
    max_chars = 40
    title_lines = textwrap.wrap(page.title, width=24)
    body_lines = textwrap.wrap(page.text, width=max_chars)
    line_gap = 12
    title_height = 68 * len(title_lines)
    body_height = 48 * len(body_lines)
    box_height = title_height + body_height + 72
    top = height - box_height - 88
    if page.slug in {"cover", "mega_symbol"}:
        top = 92
    if page.overlay_box:
        draw.rounded_rectangle(
            (margin - 28, top - 30, width - margin + 28, top + box_height),
            radius=24,
            fill=(255, 250, 240, 224),
            outline=(35, 38, 55, 190),
            width=4,
        )
        text_color = (24, 28, 42, 255)
    else:
        text_color = (255, 250, 240, 255)
        shadow_color = (12, 14, 24, 210)
        y_shadow = top + 4
        for line in title_lines:
            draw.text((margin + 4, y_shadow), line, font=title_font, fill=shadow_color)
            y_shadow += 68
        y_shadow += line_gap
        for line in body_lines:
            draw.text((margin + 4, y_shadow), line, font=text_font, fill=shadow_color)
            y_shadow += 48
    y = top
    for line in title_lines:
        draw.text((margin, y), line, font=title_font, fill=text_color)
        y += 68
    y += line_gap
    for line in body_lines:
        draw.text((margin, y), line, font=text_font, fill=text_color)
        y += 48


def render_page_image(spec: StorybookSpec, page: PageSpec, output_path: Path | str) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    width, height = spec.page_width, spec.page_height
    a, b, c, d = (_hex(color) for color in page.palette)
    image = _gradient(width, height, a, b)
    draw = ImageDraw.Draw(image, "RGBA")
    tessa, ciro = child_pair(spec.characters)
    _draw_stars(draw, page.slug, width, height, _mix(c, (255, 255, 255), 0.35))

    if page.scene == "cosmic_yinyang":
        _draw_yinyang(draw, width // 2, height // 2 + 30, 460, _hex("#f7efe5"), _hex("#141421"))
        _draw_character(draw, tessa, (width // 2 - 175, height // 2 - 40), 210)
        _draw_character(draw, ciro, (width // 2 + 210, height // 2 + 60), 220)
    elif page.scene == "cube_home":
        _draw_family(draw, tessa, [(250, 1110), (470, 1030), (720, 1125), (965, 1038)], 170)
        _draw_character(draw, tessa, (width // 2, 680), 250)
        draw.rectangle((90, 1240, width - 90, 1335), fill=_mix(a, d, 0.35))
    elif page.scene == "tetra_home":
        _draw_family(draw, ciro, [(235, 1020), (455, 940), (810, 1010), (1045, 910)], 180)
        _draw_character(draw, ciro, (width // 2, 685), 250)
        for x in range(120, width, 170):
            draw.polygon(((x, 1320), (x + 80, 1210), (x + 160, 1320)), outline=d, fill=_mix(a, c, 0.25))
    elif page.scene == "symbol_valley":
        _draw_yinyang(draw, width // 2, 790, 520, _hex("#f4f1ea"), _hex("#141421"))
        _draw_family(draw, tessa, [(315, 625), (260, 875)], 110)
        _draw_family(draw, ciro, [(940, 625), (1010, 880)], 120)
    elif page.scene == "meeting":
        _draw_yinyang(draw, width // 2, 760, 380, _mix(a, (255, 255, 255), 0.35), _mix(d, (0, 0, 0), 0.15))
        _draw_character(draw, tessa, (470, 820), 230)
        _draw_character(draw, ciro, (820, 830), 230)
        draw.line((572, 835, 705, 835), fill=_hex("#ffffff"), width=12)
    elif page.scene == "mirror":
        draw.line((width // 2, 260, width // 2, 1260), fill=_hex("#ffffff"), width=10)
        _draw_family(draw, tessa, [(250, 950), (420, 1040), (275, 1145)], 140)
        _draw_family(draw, ciro, [(1010, 950), (850, 1040), (990, 1145)], 140)
        _draw_character(draw, tessa, (500, 690), 210)
        _draw_character(draw, ciro, (780, 690), 210)
    elif page.scene == "bridge":
        for i in range(8):
            x = 120 + i * 145
            y = 990 - int(math.sin(i / 7 * math.pi) * 260)
            if i % 2:
                draw_cube(draw, (x, y), 86, "#62c7d8", "#294353")
            else:
                draw_tetrahedron(draw, (x, y), 86, "#f5c84c", "#27364a")
        _draw_character(draw, tessa, (260, 880), 190)
        _draw_character(draw, ciro, (1010, 850), 190)
    elif page.scene == "mega_symbol":
        _draw_yinyang(draw, width // 2, 830, 560, _hex("#f8f2e9"), _hex("#141421"))
        draw_tetrahedron(draw, (width // 2 - 150, 765), 190, "#f5c84c", "#27364a")
        draw_cube(draw, (width // 2 + 170, 875), 190, "#62c7d8", "#4d2d73")
        draw.rectangle((width // 2 - 275, 575, width // 2 + 275, 1085), outline=_hex("#f8f2e9"), width=8)
    elif page.scene == "shared_home":
        _draw_yinyang(draw, width // 2, 720, 390, _hex("#f7efe5"), _hex("#2b3350"))
        _draw_family(draw, tessa, [(245, 1110), (380, 1200), (520, 1115)], 120)
        _draw_family(draw, ciro, [(755, 1110), (900, 1200), (1040, 1115)], 120)
        _draw_character(draw, tessa, (515, 775), 190)
        _draw_character(draw, ciro, (770, 785), 190)
    else:
        raise ValueError(f"Unsupported scene: {page.scene}")

    _overlay_text(image, page)
    image.save(output)
    return output
