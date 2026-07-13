"""Typography and text-overlay composition for storybook pages."""

from __future__ import annotations

import textwrap

from PIL import Image, ImageDraw, ImageFont

from .models import PageSpec


def load_font(size: int, *, bold: bool = False) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
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


def text_width(draw: ImageDraw.ImageDraw, line: str, font: ImageFont.ImageFont | ImageFont.FreeTypeFont) -> int:
    bbox = draw.textbbox((0, 0), line, font=font)
    return int(bbox[2] - bbox[0])


def text_height(draw: ImageDraw.ImageDraw, line: str, font: ImageFont.ImageFont | ImageFont.FreeTypeFont) -> int:
    bbox = draw.textbbox((0, 0), line, font=font)
    return int(bbox[3] - bbox[1])


def wrapped_lines(text: str, width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.splitlines():
        if not paragraph.strip():
            lines.append("")
            continue
        lines.extend(textwrap.wrap(paragraph, width=width))
    return lines


def pixel_wrapped_lines(
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
            if text_width(draw, candidate, font) <= max_width:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines


def draw_publication_text(image: Image.Image, page: PageSpec) -> None:
    draw = ImageDraw.Draw(image, "RGBA")
    width, height = image.size
    title_font = load_font(58, bold=True)
    body_font = load_font(32)
    small_font = load_font(26)
    margin = 112
    panel = (margin - 38, 150, width - margin + 38, height - 170)
    draw.rounded_rectangle(panel, radius=28, fill=(255, 250, 240, 232), outline=(35, 38, 55, 170), width=4)
    draw.text((margin, 198), page.title, font=title_font, fill=(24, 28, 42, 255))
    y = 296
    for line in wrapped_lines(page.text, 57):
        if not line:
            y += 28
            continue
        font = body_font if y < 690 else small_font
        draw.text((margin, y), line, font=font, fill=(24, 28, 42, 255))
        y += 43 if font is body_font else 36


def draw_page_text(image: Image.Image, page: PageSpec) -> None:
    if page.slug == "publication_information":
        draw_publication_text(image, page)
        return
    draw = ImageDraw.Draw(image, "RGBA")
    width, height = image.size
    title_font = load_font(58, bold=True)
    text_font = load_font(37)
    margin = 86
    max_chars = 40
    title_lines = wrapped_lines(page.title, 24)
    body_lines = wrapped_lines(page.text, max_chars)
    line_gap = 12
    title_height = 68 * len(title_lines)
    body_height = 48 * len(body_lines)
    box_height = title_height + body_height + 72
    top = height - box_height - 88
    if page.caption_position == "top":
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
