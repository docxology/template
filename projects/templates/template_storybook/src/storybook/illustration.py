from __future__ import annotations

import hashlib
import itertools
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


def _text_width(draw: ImageDraw.ImageDraw, line: str, font: ImageFont.ImageFont | ImageFont.FreeTypeFont) -> int:
    bbox = draw.textbbox((0, 0), line, font=font)
    return int(bbox[2] - bbox[0])


def _text_height(draw: ImageDraw.ImageDraw, line: str, font: ImageFont.ImageFont | ImageFont.FreeTypeFont) -> int:
    bbox = draw.textbbox((0, 0), line, font=font)
    return int(bbox[3] - bbox[1])


def _wrapped_lines(text: str, width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.splitlines():
        if not paragraph.strip():
            lines.append("")
            continue
        lines.extend(textwrap.wrap(paragraph, width=width))
    return lines


def _pixel_wrapped_lines(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont | ImageFont.FreeTypeFont,
    max_width: int,
) -> list[str]:
    lines: list[str] = []
    for paragraph in text.splitlines():
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current = words[0]
        for word in words[1:]:
            candidate = f"{current} {word}"
            if _text_width(draw, candidate, font) <= max_width:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines


def _regular_points(
    cx: int,
    cy: int,
    radius: int,
    count: int,
    *,
    rotation: float = -math.pi / 2,
    y_scale: float = 1.0,
) -> list[tuple[int, int]]:
    return [
        (
            cx + int(math.cos(rotation + index * math.tau / count) * radius),
            cy + int(math.sin(rotation + index * math.tau / count) * radius * y_scale),
        )
        for index in range(count)
    ]


def _draw_orbital_geometry(
    draw: ImageDraw.ImageDraw,
    cx: int,
    cy: int,
    radius: int,
    *,
    node_count: int,
    color: RGB,
    accent: RGB,
    rotation: float = -math.pi / 2,
) -> None:
    for offset, alpha in ((0, 120), (42, 70), (-46, 55)):
        draw.ellipse(
            (cx - radius + offset, cy - radius // 2, cx + radius + offset, cy + radius // 2),
            outline=(*color, alpha),
            width=4,
        )
    nodes = _regular_points(cx, cy, radius, node_count, rotation=rotation, y_scale=0.52)
    for start, end in zip(nodes, nodes[1:] + nodes[:1], strict=True):
        draw.line((*start, *end), fill=(*color, 96), width=3)
    for index, point in enumerate(nodes):
        x, y = point
        r = 6 if index % 2 else 9
        draw.ellipse((x - r, y - r, x + r, y + r), fill=(*accent, 210))


def _draw_triangle_tessellation(
    draw: ImageDraw.ImageDraw,
    width: int,
    y: int,
    *,
    color: RGB,
    accent: RGB,
    scale: int = 120,
) -> None:
    for row in range(4):
        row_y = y + row * int(scale * 0.58)
        for col, x in enumerate(range(-scale, width + scale, scale)):
            up = (row + col) % 2 == 0
            points = (
                ((x, row_y + scale), (x + scale // 2, row_y), (x + scale, row_y + scale))
                if up
                else ((x, row_y), (x + scale // 2, row_y + scale), (x + scale, row_y))
            )
            fill = (*_mix(color, accent, 0.18 if up else 0.34), 58)
            draw.polygon(points, fill=fill, outline=(*accent, 70))


def _draw_isometric_cube_lattice(draw: ImageDraw.ImageDraw, width: int, y: int, *, color: RGB) -> None:
    step = 116
    for x in range(-step, width + step, step):
        for offset in (0, step // 2):
            draw.line((x + offset, y, x + offset + step, y + 60), fill=(*color, 70), width=3)
            draw.line((x + offset, y + 120, x + offset + step, y + 60), fill=(*color, 70), width=3)
            draw.line((x + offset + step, y + 60, x + offset + step, y + 178), fill=(*color, 48), width=3)


def _draw_force_arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], color: RGB) -> None:
    draw.line((*start, *end), fill=(*color, 172), width=6)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    head = 20
    left = (
        end[0] - int(math.cos(angle - math.pi / 6) * head),
        end[1] - int(math.sin(angle - math.pi / 6) * head),
    )
    right = (
        end[0] - int(math.cos(angle + math.pi / 6) * head),
        end[1] - int(math.sin(angle + math.pi / 6) * head),
    )
    draw.polygon((end, left, right), fill=(*color, 172))


def _draw_recipient_seal(
    draw: ImageDraw.ImageDraw,
    center: tuple[int, int],
    size: int,
    *,
    color: RGB,
    accent: RGB,
    alpha: int = 86,
    rotation: float = -math.pi / 2,
) -> None:
    cx, cy = center
    square = _regular_points(cx, cy, size, 4, rotation=rotation + math.pi / 4, y_scale=0.72)
    triangle = _regular_points(cx, cy, int(size * 1.08), 3, rotation=rotation, y_scale=0.72)
    for start, end in zip(square, square[1:] + square[:1], strict=True):
        draw.line((*start, *end), fill=(*color, alpha), width=4)
    for start, end in zip(triangle, triangle[1:] + triangle[:1], strict=True):
        draw.line((*start, *end), fill=(*accent, alpha), width=4)
    for index, point in enumerate(square + triangle):
        r = 5 if index < 4 else 7
        x, y = point
        draw.ellipse((x - r, y - r, x + r, y + r), fill=(*_mix(color, accent, 0.45), min(210, alpha + 70)))


def _draw_whisper_threads(
    draw: ImageDraw.ImageDraw,
    points: list[tuple[int, int]],
    *,
    color: RGB,
    alpha: int = 56,
    width: int = 2,
) -> None:
    for start, end in itertools.combinations(points, 2):
        draw.line((*start, *end), fill=(*color, alpha), width=width)


def _draw_corner_witnesses(
    draw: ImageDraw.ImageDraw, points: list[tuple[int, int]], *, color: RGB, alpha: int = 150
) -> None:
    for index, (x, y) in enumerate(points):
        radius = 6 + (index % 3) * 2
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(*color, alpha))


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


def _draw_cover_text(image: Image.Image, page: PageSpec) -> None:
    draw = ImageDraw.Draw(image, "RGBA")
    width, height = image.size
    title_font = _font(108, bold=True)
    subtitle_font = _font(32, bold=True)
    detail_font = _font(27)
    small_font = _font(24, bold=True)
    title_lines = _wrapped_lines(page.title, 18)
    info_lines = [line for line in page.text.splitlines() if line.strip()]
    y = 86
    for line in title_lines:
        x = (width - _text_width(draw, line, title_font)) // 2
        draw.text((x + 6, y + 6), line, font=title_font, fill=(10, 12, 24, 235))
        draw.text((x, y), line, font=title_font, fill=(255, 249, 236, 255))
        y += 122
    _draw_orbital_geometry(
        draw,
        width // 2,
        height // 2 + 22,
        482,
        node_count=16,
        color=(255, 244, 210),
        accent=(245, 200, 76),
        rotation=-math.pi / 2.2,
    )
    bar_top = height - 344
    bar = (78, bar_top, width - 78, height - 72)
    draw.rounded_rectangle(bar, radius=26, fill=(12, 16, 35, 222), outline=(255, 244, 210, 190), width=4)
    draw.rectangle((110, bar_top + 30, 122, height - 104), fill=(245, 200, 76, 238))
    draw.polygon(
        ((160, bar_top + 68), (202, bar_top + 144), (118, bar_top + 144)),
        fill=(245, 200, 76, 228),
        outline=(255, 244, 210, 200),
    )
    draw.rectangle(
        (166, bar_top + 168, 228, bar_top + 230),
        fill=(98, 199, 216, 224),
        outline=(255, 244, 210, 180),
    )
    text_x = 270
    max_text_width = width - text_x - 116
    if info_lines:
        subtitle_lines = _pixel_wrapped_lines(draw, info_lines[0], subtitle_font, max_text_width)
        y_line = bar_top + 38
        for subtitle_line in subtitle_lines:
            draw.text((text_x, y_line), subtitle_line, font=subtitle_font, fill=(255, 249, 236, 255))
            y_line += _text_height(draw, subtitle_line, subtitle_font) + 10
    else:
        y_line = bar_top + 38
    y_line += 16
    for index, line in enumerate(info_lines[1:]):
        font = small_font if line == "template_storybook" else detail_font
        fill = (245, 200, 76, 255) if line == "template_storybook" else (232, 244, 247, 245)
        label = line if index == 0 else f"|  {line}"
        draw.text((text_x, y_line), label, font=font, fill=fill)
        y_line += 41


def _draw_publication_text(image: Image.Image, page: PageSpec) -> None:
    draw = ImageDraw.Draw(image, "RGBA")
    width, height = image.size
    title_font = _font(58, bold=True)
    body_font = _font(32)
    small_font = _font(26)
    margin = 112
    panel = (margin - 38, 150, width - margin + 38, height - 170)
    draw.rounded_rectangle(panel, radius=28, fill=(255, 250, 240, 232), outline=(35, 38, 55, 170), width=4)
    draw.text((margin, 198), page.title, font=title_font, fill=(24, 28, 42, 255))
    y = 296
    for line in _wrapped_lines(page.text, 57):
        if not line:
            y += 28
            continue
        font = body_font if y < 690 else small_font
        draw.text((margin, y), line, font=font, fill=(24, 28, 42, 255))
        y += 43 if font is body_font else 36


def _wire_cube_points(cx: int, cy: int, size: int) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    half = size // 2
    shift = int(size * 0.30)
    front = [
        (cx - half, cy - half + shift),
        (cx + half, cy - half + shift),
        (cx + half, cy + half + shift),
        (cx - half, cy + half + shift),
    ]
    back = [(x + shift, y - shift) for x, y in front]
    return front, back


def _draw_tetra_stability(draw: ImageDraw.ImageDraw, cx: int, cy: int, size: int) -> None:
    front, back = _wire_cube_points(cx, cy, size)
    cube_edges = [
        (front[0], front[1]),
        (front[1], front[2]),
        (front[2], front[3]),
        (front[3], front[0]),
        (back[0], back[1]),
        (back[1], back[2]),
        (back[2], back[3]),
        (back[3], back[0]),
        (front[0], back[0]),
        (front[1], back[1]),
        (front[2], back[2]),
        (front[3], back[3]),
    ]
    draw.ellipse(
        (cx - size // 2 - 80, cy + size // 2 + 32, cx + size // 2 + 270, cy + size // 2 + 98), fill=(0, 0, 0, 44)
    )
    for start, end in cube_edges:
        draw.line((*start, *end), fill=(240, 250, 255, 150), width=16)
        draw.line((*start, *end), fill=(98, 199, 216, 210), width=5)
    tetra = [back[0], front[1], front[3], back[2]]
    centroid = (sum(point[0] for point in tetra) // 4, sum(point[1] for point in tetra) // 4)
    for corner in front + back:
        _draw_force_arrow(draw, centroid, corner, (255, 250, 240))
    for start, end in itertools.combinations(tetra, 2):
        draw.line((*start, *end), fill=(56, 76, 112, 170), width=20)
        draw.line((*start, *end), fill=(245, 200, 76, 238), width=10)
    _draw_whisper_threads(draw, front + back, color=(255, 250, 240), alpha=34, width=2)
    _draw_recipient_seal(
        draw,
        centroid,
        118,
        color=(98, 199, 216),
        accent=(245, 200, 76),
        alpha=70,
        rotation=math.pi / 10,
    )
    for point in tetra:
        x, y = point
        draw.ellipse((x - 25, y - 25, x + 25, y + 25), fill=(245, 200, 76, 255), outline=(39, 54, 74, 255), width=5)
        draw.ellipse((x - 9, y - 9, x + 9, y + 9), fill=(255, 250, 240, 255))
    for face in ((tetra[0], tetra[1], tetra[2]), (tetra[0], tetra[2], tetra[3]), (tetra[1], tetra[2], tetra[3])):
        draw.polygon(face, fill=(245, 200, 76, 34))


def _draw_shadow_school(draw: ImageDraw.ImageDraw, width: int, height: int, tessa: Character, ciro: Character) -> None:
    draw.ellipse((865, 130, 1045, 310), fill=(255, 218, 112, 210))
    draw.polygon(((80, 1190), (width - 80, 1180), (width - 25, height), (25, height)), fill=(44, 52, 82, 88))
    draw.rectangle((120, 1080, width - 120, 1125), fill=(255, 250, 240, 150))
    for offset, alpha in ((0, 66), (70, 42), (130, 24)):
        draw.polygon(((260 + offset, 1030), (470 + offset, 960), (610 + offset, 1098)), fill=(39, 54, 74, alpha))
        draw.polygon(
            ((720 + offset, 1010), (900 + offset, 940), (1080 + offset, 1010), (905 + offset, 1088)),
            fill=(39, 54, 74, alpha),
        )
    _draw_character(draw, tessa, (360, 860), 185)
    _draw_character(draw, ciro, (875, 870), 190)
    draw.polygon(((175, 1185), (445, 1100), (575, 1215)), fill=(39, 54, 74, 95))
    draw.polygon(((575, 1180), (770, 1090), (1015, 1180), (820, 1270)), fill=(39, 54, 74, 82))
    for center, radius in [((300, 475), 52), ((525, 420), 38), ((790, 480), 48), ((990, 555), 32)]:
        cx, cy = center
        draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), outline=(255, 250, 240, 120), width=5)
        if radius > 40:
            draw.line((cx - radius, cy, cx + radius, cy), fill=(255, 250, 240, 70), width=3)
            draw.line((cx, cy - radius, cx, cy + radius), fill=(255, 250, 240, 70), width=3)
    draw.line((945, 245, 400, 785), fill=(255, 248, 210, 75), width=18)
    draw.line((945, 245, 875, 795), fill=(255, 248, 210, 75), width=18)
    _draw_recipient_seal(
        draw,
        (640, 455),
        112,
        color=(255, 250, 240),
        accent=(245, 200, 76),
        alpha=64,
        rotation=math.pi / 7,
    )


def _draw_tensegrity_lantern(
    draw: ImageDraw.ImageDraw, width: int, height: int, tessa: Character, ciro: Character
) -> None:
    cx, cy = width // 2, 690
    _draw_orbital_geometry(
        draw,
        cx,
        cy + 36,
        360,
        node_count=12,
        color=(98, 199, 216),
        accent=(255, 244, 190),
        rotation=math.pi / 12,
    )
    top = [
        (
            cx + int(math.cos(index * math.tau / 3 - math.pi / 2) * 220),
            cy - 150 + int(math.sin(index * math.tau / 3 - math.pi / 2) * 88),
        )
        for index in range(3)
    ]
    bottom = [
        (
            cx + int(math.cos(index * math.tau / 3 + math.pi / 6) * 240),
            cy + 185 + int(math.sin(index * math.tau / 3 + math.pi / 6) * 96),
        )
        for index in range(3)
    ]
    draw.ellipse(
        (cx - 360, cy - 390, cx + 360, cy + 420), fill=(255, 220, 130, 32), outline=(255, 240, 180, 120), width=6
    )
    for ring in (top, bottom):
        for start, end in zip(ring, ring[1:] + ring[:1], strict=True):
            draw.line((*start, *end), fill=(98, 199, 216, 180), width=5)
    for index, start in enumerate(top):
        for end in (bottom[index], bottom[(index + 1) % 3]):
            draw.line((*start, *end), fill=(98, 199, 216, 150), width=4)
    rod_pairs = [
        (top[0], bottom[1]),
        (top[1], bottom[2]),
        (top[2], bottom[0]),
        ((top[0][0] + 48, top[0][1] + 34), (bottom[2][0] - 46, bottom[2][1] - 28)),
        ((top[1][0] - 44, top[1][1] + 28), (bottom[0][0] + 46, bottom[0][1] - 32)),
        ((top[2][0], top[2][1] + 44), (bottom[1][0], bottom[1][1] - 44)),
    ]
    for start, end in rod_pairs:
        draw.line((*start, *end), fill=(245, 200, 76, 238), width=16)
        draw.line((*start, *end), fill=(255, 244, 190, 155), width=5)
    for point in top + bottom:
        x, y = point
        draw.ellipse((x - 18, y - 18, x + 18, y + 18), fill=(255, 244, 190, 255), outline=(18, 24, 46, 255), width=3)
    for index, start in enumerate(bottom):
        end = top[(index + 2) % 3]
        draw.line((*start, *end), fill=(255, 250, 240, 82), width=2)
    _draw_whisper_threads(draw, top + bottom, color=(255, 250, 240), alpha=28, width=2)
    _draw_recipient_seal(
        draw,
        (cx, cy + 34),
        145,
        color=(98, 199, 216),
        accent=(255, 244, 190),
        alpha=58,
        rotation=math.pi / 5,
    )
    draw.line((cx, 110, cx, cy - 398), fill=(255, 244, 190, 145), width=5)
    draw.ellipse((cx - 82, cy - 80, cx + 82, cy + 84), fill=(255, 250, 210, 86))
    draw.ellipse((cx - 28, cy - 26, cx + 28, cy + 30), fill=(255, 250, 210, 155))
    _draw_character(draw, tessa, (180, 945), 122)
    _draw_character(draw, ciro, (1020, 1145), 150)


def _draw_vector_garden(draw: ImageDraw.ImageDraw, width: int, height: int, tessa: Character, ciro: Character) -> None:
    origin = (width // 2, 780)
    directions = [
        (origin[0], 330),
        (930, 505),
        (1035, 890),
        (width // 2, 1145),
        (240, 890),
        (345, 505),
    ]
    draw.ellipse(
        (origin[0] - 390, origin[1] - 390, origin[0] + 390, origin[1] + 390), outline=(39, 54, 74, 66), width=5
    )
    for index, point in enumerate(directions):
        _draw_force_arrow(draw, origin, point, (39, 54, 74))
        px, py = point
        if index % 2:
            draw_cube(draw, (px, py), 84, "#62c7d8", "#4d2d73")
        else:
            draw_tetrahedron(draw, (px, py), 84, "#f5c84c", "#27364a")
    for start, end in itertools.combinations(directions, 2):
        if abs(directions.index(start) - directions.index(end)) in {1, 5}:
            draw.line((*start, *end), fill=(255, 250, 240, 120), width=4)
    _draw_recipient_seal(
        draw,
        origin,
        150,
        color=(39, 54, 74),
        accent=(98, 199, 216),
        alpha=58,
        rotation=math.pi / 6,
    )
    draw.ellipse((origin[0] - 72, origin[1] - 72, origin[0] + 72, origin[1] + 72), fill=(255, 250, 240, 190))
    draw.ellipse((origin[0] - 28, origin[1] - 28, origin[0] + 28, origin[1] + 28), fill=(39, 54, 74, 230))
    _draw_character(draw, tessa, (310, 1265), 145)
    _draw_character(draw, ciro, (965, 1265), 145)


def _overlay_text(image: Image.Image, page: PageSpec) -> None:
    if page.slug == "cover":
        _draw_cover_text(image, page)
        return
    if page.slug == "publication_information":
        _draw_publication_text(image, page)
        return
    draw = ImageDraw.Draw(image, "RGBA")
    width, height = image.size
    title_font = _font(58, bold=True)
    text_font = _font(37)
    margin = 86
    max_chars = 40
    title_lines = _wrapped_lines(page.title, 24)
    body_lines = _wrapped_lines(page.text, max_chars)
    line_gap = 12
    title_height = 68 * len(title_lines)
    body_height = 48 * len(body_lines)
    box_height = title_height + body_height + 72
    top = height - box_height - 88
    if page.slug in {"mega_symbol"}:
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
        _draw_recipient_seal(
            draw,
            (width // 2, height // 2 + 28),
            320,
            color=(255, 244, 210),
            accent=(98, 199, 216),
            alpha=48,
            rotation=math.pi / 8,
        )
        _draw_character(draw, tessa, (width // 2 - 175, height // 2 - 40), 210)
        _draw_character(draw, ciro, (width // 2 + 210, height // 2 + 60), 220)
    elif page.scene == "publication_info":
        draw.rounded_rectangle((145, 250, width - 145, height - 260), radius=36, fill=(255, 250, 240, 90))
        _draw_orbital_geometry(
            draw,
            width // 2,
            850,
            330,
            node_count=10,
            color=_mix(c, (255, 255, 255), 0.25),
            accent=c,
            rotation=math.pi / 10,
        )
        draw_cube(draw, (width // 2 - 120, 990), 138, "#62c7d8", "#4d2d73")
        draw_tetrahedron(draw, (width // 2 + 155, 980), 140, "#f5c84c", "#27364a")
        draw.line((width // 2 - 15, 1000, width // 2 + 35, 1000), fill=_hex("#27364a"), width=7)
    elif page.scene == "cube_home":
        _draw_isometric_cube_lattice(draw, width, 1040, color=_mix(c, d, 0.16))
        draw.rounded_rectangle(
            (115, 290, width - 115, 1030), radius=20, fill=(255, 250, 240, 42), outline=(*d, 90), width=5
        )
        for x in range(180, width - 160, 190):
            draw.line((x, 310, x, 1000), fill=(*d, 42), width=3)
        for y_grid in range(390, 1000, 150):
            draw.line((150, y_grid, width - 150, y_grid), fill=(*d, 42), width=3)
        _draw_family(draw, tessa, [(250, 1110), (470, 1030), (720, 1125), (965, 1038)], 170)
        _draw_character(draw, tessa, (width // 2, 680), 250)
        _draw_corner_witnesses(draw, [(235, 405), (995, 405), (995, 905), (235, 905)], color=c, alpha=130)
        draw.rectangle((90, 1240, width - 90, 1335), fill=_mix(a, d, 0.35))
    elif page.scene == "tetra_home":
        _draw_triangle_tessellation(draw, width, 1010, color=a, accent=d, scale=150)
        for point in _regular_points(width // 2, 610, 360, 6, rotation=math.pi / 6, y_scale=0.65):
            draw.line((width // 2, 610, *point), fill=(*d, 58), width=5)
        _draw_recipient_seal(
            draw,
            (width // 2, 600),
            215,
            color=_mix(c, (255, 255, 255), 0.22),
            accent=d,
            alpha=46,
            rotation=math.pi / 3,
        )
        _draw_family(draw, ciro, [(235, 1020), (455, 940), (810, 1010), (1045, 910)], 180)
        _draw_character(draw, ciro, (width // 2, 685), 250)
        for x in range(120, width, 170):
            draw.polygon(((x, 1320), (x + 80, 1210), (x + 160, 1320)), outline=d, fill=_mix(a, c, 0.25))
    elif page.scene == "symbol_valley":
        _draw_yinyang(draw, width // 2, 790, 520, _hex("#f4f1ea"), _hex("#141421"))
        _draw_orbital_geometry(
            draw,
            width // 2,
            790,
            590,
            node_count=18,
            color=_hex("#f4f1ea"),
            accent=c,
            rotation=math.pi / 18,
        )
        _draw_recipient_seal(
            draw,
            (width // 2, 790),
            365,
            color=_hex("#f4f1ea"),
            accent=c,
            alpha=38,
            rotation=math.pi / 12,
        )
        _draw_family(draw, tessa, [(315, 625), (260, 875)], 110)
        _draw_family(draw, ciro, [(940, 625), (1010, 880)], 120)
    elif page.scene == "meeting":
        _draw_yinyang(draw, width // 2, 760, 380, _mix(a, (255, 255, 255), 0.35), _mix(d, (0, 0, 0), 0.15))
        for radius in (440, 510, 580):
            draw.arc(
                (width // 2 - radius, 760 - radius // 2, width // 2 + radius, 760 + radius // 2),
                205,
                335,
                fill=(255, 250, 240, 72),
                width=5,
            )
        _draw_character(draw, tessa, (470, 820), 230)
        _draw_character(draw, ciro, (820, 830), 230)
        draw.line((572, 835, 705, 835), fill=_hex("#ffffff"), width=16)
        draw.ellipse((620, 814, 657, 851), fill=(245, 200, 76, 210))
        draw.ellipse((655, 814, 692, 851), fill=(98, 199, 216, 210))
        _draw_whisper_threads(
            draw, [(470, 820), (820, 830), (width // 2, 615), (width // 2, 995)], color=(255, 255, 255), alpha=38
        )
    elif page.scene == "tetra_stability":
        _draw_tetra_stability(draw, width // 2 - 90, 720, 560)
        _draw_character(draw, tessa, (width // 2 - 345, 870), 160)
        _draw_character(draw, ciro, (width // 2 + 375, 890), 165)
        draw.arc((220, 360, 1040, 1195), 198, 342, fill=(255, 255, 255, 160), width=7)
    elif page.scene == "mirror":
        draw.rectangle((width // 2 - 12, 250, width // 2 + 12, 1270), fill=(255, 255, 255, 140))
        for y_mark in range(320, 1210, 110):
            draw.line((width // 2 - 70, y_mark, width // 2 + 70, y_mark + 36), fill=(255, 255, 255, 80), width=3)
        _draw_family(draw, tessa, [(250, 950), (420, 1040), (275, 1145)], 140)
        _draw_family(draw, ciro, [(1010, 950), (850, 1040), (990, 1145)], 140)
        _draw_character(draw, tessa, (500, 690), 210)
        _draw_character(draw, ciro, (780, 690), 210)
    elif page.scene == "bridge":
        for band, alpha in ((0, 72), (42, 48), (84, 30)):
            draw.arc((80, 640 + band, width - 80, 1260 + band), 198, 342, fill=(*d, alpha), width=10)
        last_point: tuple[int, int] | None = None
        bridge_points: list[tuple[int, int]] = []
        for i in range(8):
            x = 120 + i * 145
            y = 990 - int(math.sin(i / 7 * math.pi) * 260)
            if last_point is not None:
                draw.line((*last_point, x, y), fill=(255, 250, 240, 150), width=8)
            last_point = (x, y)
            bridge_points.append((x, y))
            if i % 2:
                draw_cube(draw, (x, y), 86, "#62c7d8", "#294353")
            else:
                draw_tetrahedron(draw, (x, y), 86, "#f5c84c", "#27364a")
        _draw_whisper_threads(draw, bridge_points[1::2], color=(98, 199, 216), alpha=48, width=3)
        _draw_whisper_threads(draw, bridge_points[::2], color=(245, 200, 76), alpha=42, width=3)
        _draw_character(draw, tessa, (260, 880), 190)
        _draw_character(draw, ciro, (1010, 850), 190)
    elif page.scene == "shadow_school":
        _draw_shadow_school(draw, width, height, tessa, ciro)
    elif page.scene == "tensegrity_lantern":
        _draw_tensegrity_lantern(draw, width, height, tessa, ciro)
    elif page.scene == "vector_garden":
        _draw_vector_garden(draw, width, height, tessa, ciro)
    elif page.scene == "mega_symbol":
        _draw_yinyang(draw, width // 2, 830, 560, _hex("#f8f2e9"), _hex("#141421"))
        _draw_orbital_geometry(
            draw,
            width // 2,
            830,
            640,
            node_count=24,
            color=(255, 250, 240),
            accent=(98, 199, 216),
            rotation=math.pi / 24,
        )
        draw_tetrahedron(draw, (width // 2 - 150, 765), 190, "#f5c84c", "#27364a")
        draw_cube(draw, (width // 2 + 170, 875), 190, "#62c7d8", "#4d2d73")
        draw.rectangle((width // 2 - 275, 575, width // 2 + 275, 1085), outline=_hex("#f8f2e9"), width=8)
        draw.polygon(
            ((width // 2, 500), (width // 2 - 360, 1115), (width // 2 + 360, 1115)),
            outline=(245, 200, 76, 180),
            width=8,
        )
        _draw_corner_witnesses(
            draw,
            [(width // 2 - 275, 575), (width // 2 + 275, 575), (width // 2 + 275, 1085), (width // 2 - 275, 1085)],
            color=(255, 250, 240),
            alpha=178,
        )
    elif page.scene == "shared_home":
        _draw_yinyang(draw, width // 2, 720, 390, _hex("#f7efe5"), _hex("#2b3350"))
        _draw_triangle_tessellation(draw, width, 1110, color=_hex("#f7efe5"), accent=_hex("#f5c84c"), scale=138)
        _draw_isometric_cube_lattice(draw, width, 1160, color=_hex("#62c7d8"))
        draw.arc((240, 390, 1030, 1120), 202, 338, fill=(255, 250, 240, 118), width=8)
        _draw_recipient_seal(
            draw,
            (width // 2, 742),
            260,
            color=(255, 250, 240),
            accent=(245, 200, 76),
            alpha=42,
            rotation=math.pi / 9,
        )
        _draw_family(draw, tessa, [(185, 900), (330, 990), (485, 925)], 106)
        _draw_family(draw, ciro, [(755, 1110), (900, 1200), (1040, 1115)], 120)
        _draw_character(draw, tessa, (515, 775), 190)
        _draw_character(draw, ciro, (770, 785), 190)
    else:
        raise ValueError(f"Unsupported scene: {page.scene}")

    _overlay_text(image, page)
    image.save(output)
    return output
