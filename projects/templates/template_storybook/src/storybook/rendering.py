from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen.canvas import Canvas

from .illustration import render_page_image
from .models import PageSpec, RenderResult, StorybookSpec
from .story import load_storybook, storybook_variables


def image_output_path(project_root: Path | str, page: PageSpec) -> Path:
    return Path(project_root) / "output" / "figures" / "storybook_pages" / page.filename


def render_story_page(project_root: Path | str, slug: str) -> Path:
    root = Path(project_root)
    spec = load_storybook(root)
    page = spec.page_by_slug(slug)
    return render_page_image(spec, page, image_output_path(root, page))


def render_story_number(project_root: Path | str, number: int) -> Path:
    root = Path(project_root)
    spec = load_storybook(root)
    page = spec.page_by_number(number)
    return render_page_image(spec, page, image_output_path(root, page))


def render_all_images(project_root: Path | str) -> tuple[Path, ...]:
    root = Path(project_root)
    spec = load_storybook(root)
    return tuple(render_page_image(spec, page, image_output_path(root, page)) for page in spec.pages)


def _ensure_images(spec: StorybookSpec, project_root: Path) -> tuple[Path, ...]:
    paths: list[Path] = []
    for page in spec.pages:
        path = image_output_path(project_root, page)
        if not path.is_file():
            render_page_image(spec, page, path)
        paths.append(path)
    return tuple(paths)


def build_storybook_pdf(project_root: Path | str) -> RenderResult:
    root = Path(project_root)
    spec = load_storybook(root)
    image_paths = _ensure_images(spec, root)
    output_path = root / spec.output_pdf
    output_path.parent.mkdir(parents=True, exist_ok=True)

    page_width, page_height = letter
    canvas = Canvas(str(output_path), pagesize=letter, invariant=True)
    canvas.setTitle(spec.title)
    canvas.setAuthor("Research Template Author")
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
