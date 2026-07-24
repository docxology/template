from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen.canvas import Canvas

from .illustration import render_page_image
from .models import PageSpec, RenderResult, StorybookSpec
from .story import load_storybook, storybook_variables
from .text_layout import audit_rendered_text_contrast


def image_output_path(project_root: Path | str, page: PageSpec) -> Path:
    """Return the output path for a page image."""
    return Path(project_root) / "output" / "figures" / "storybook_pages" / page.filename


def _clean_stale_page_images(project_root: Path, spec: StorybookSpec) -> None:
    pages_dir = project_root / "output" / "figures" / "storybook_pages"
    if not pages_dir.is_dir():
        return
    expected = {page.filename for page in spec.pages}
    for path in pages_dir.glob("*.png"):
        if path.name not in expected:
            path.unlink()


def render_story_page(project_root: Path | str, slug: str) -> Path:
    """Render a single storybook page image."""
    root = Path(project_root)
    spec = load_storybook(root)
    page = spec.page_by_slug(slug)
    return render_page_image(spec, page, image_output_path(root, page))


def render_story_number(project_root: Path | str, number: int) -> Path:
    """Render a storybook page by number."""
    root = Path(project_root)
    spec = load_storybook(root)
    page = spec.page_by_number(number)
    return render_page_image(spec, page, image_output_path(root, page))


def render_all_images(project_root: Path | str) -> tuple[Path, ...]:
    """Render all storybook page images."""
    root = Path(project_root)
    spec = load_storybook(root)
    _clean_stale_page_images(root, spec)
    return tuple(render_page_image(spec, page, image_output_path(root, page)) for page in spec.pages)


def build_contact_sheet(
    image_paths: tuple[Path, ...],
    output_path: Path,
    *,
    columns: int = 4,
    thumbnail_width: int = 320,
) -> Path:
    """Build a deterministic contact sheet for visual inspection.

    The sheet is a navigation aid, not a replacement for the full-page
    illustrations. It preserves page order, labels each thumbnail by source
    filename, and uses fixed geometry so repeated renders are byte-stable.
    """
    if not image_paths:
        raise ValueError("at least one page image is required")
    if columns < 1 or thumbnail_width < 1:
        raise ValueError("columns and thumbnail_width must be positive")

    opened: list[Image.Image] = []
    try:
        for path in image_paths:
            with Image.open(path) as source:
                image = source.convert("RGB")
            image.thumbnail((thumbnail_width, 460), Image.Resampling.LANCZOS)
            opened.append(image)
        cell_width = thumbnail_width + 32
        cell_height = max(image.height for image in opened) + 58
        rows = (len(opened) + columns - 1) // columns
        sheet = Image.new("RGB", (columns * cell_width, rows * cell_height), "white")
        draw = ImageDraw.Draw(sheet)
        label_font = ImageFont.load_default()
        for index, (path, image) in enumerate(zip(image_paths, opened, strict=True)):
            x = (index % columns) * cell_width + (cell_width - image.width) // 2
            y = (index // columns) * cell_height + 8
            sheet.paste(image, (x, y))
            label = f"{index + 1:02d} · {path.stem}"
            draw.text((x, y + image.height + 8), label, fill=(24, 28, 42), font=label_font)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(output_path, format="PNG", optimize=False)
    finally:
        for image in opened:
            image.close()
    return output_path


def build_storybook_pdf(project_root: Path | str) -> RenderResult:
    """Build a PDF from rendered storybook pages."""
    root = Path(project_root)
    spec = load_storybook(root)
    _clean_stale_page_images(root, spec)
    image_paths = tuple(render_page_image(spec, page, image_output_path(root, page)) for page in spec.pages)
    output_path = root / spec.output_pdf
    output_path.parent.mkdir(parents=True, exist_ok=True)

    page_width, page_height = spec.page_width, spec.page_height
    canvas = Canvas(str(output_path), pagesize=(page_width, page_height), invariant=True)
    canvas.setTitle(spec.title)
    canvas.setAuthor("Daniel Ari Friedman")
    canvas.setSubject(spec.subtitle)
    for path in image_paths:
        canvas.drawImage(str(path), 0, 0, width=page_width, height=page_height, preserveAspectRatio=False)
        canvas.showPage()
    canvas.save()

    data_dir = root / "output" / "data"
    reports_dir = root / "output" / "reports"
    data_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = data_dir / "storybook_manifest.json"
    summary_path = reports_dir / "storybook_summary.md"
    contact_sheet_path = root / "output" / "figures" / "storybook_contact_sheet.png"
    result = RenderResult(
        output_path=output_path,
        page_count=spec.page_count,
        image_paths=image_paths,
        manifest_path=manifest_path,
        summary_path=summary_path,
        contact_sheet_path=contact_sheet_path,
    )
    build_contact_sheet(image_paths, contact_sheet_path)
    manifest = storybook_variables(spec)
    manifest["render"] = result.to_dict(root=root)
    manifest["render"]["text_contrast_audit"] = [
        audit_rendered_text_contrast(path, page) for path, page in zip(image_paths, spec.pages, strict=True)
    ]
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    summary_path.write_text(
        "\n".join(
            [
                f"# {spec.title}",
                "",
                f"- Pages: {spec.page_count}",
                f"- Full-page illustrations: {len(image_paths)}",
                f"- PDF: `{output_path.relative_to(root)}`",
                f"- Image directory: `{image_paths[0].parent.relative_to(root)}`",
                f"- Contact sheet: `{contact_sheet_path.relative_to(root)}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return result
