from __future__ import annotations

import json
from pathlib import Path

from reportlab.pdfgen.canvas import Canvas

from .illustration import render_page_image
from .models import PageSpec, RenderResult, StorybookSpec
from .story import load_storybook, storybook_variables


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
    result = RenderResult(
        output_path=output_path,
        page_count=spec.page_count,
        image_paths=image_paths,
        manifest_path=manifest_path,
        summary_path=summary_path,
    )
    manifest = storybook_variables(spec)
    manifest["render"] = result.to_dict()
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
                "",
            ]
        ),
        encoding="utf-8",
    )
    return result
