from __future__ import annotations

import subprocess
import sys

from PIL import Image

from storybook import build_storybook_pdf, load_storybook, render_story_number, render_story_page


def _pdf_page_count(data: bytes) -> int:
    return data.count(b"/Type /Page") - data.count(b"/Type /Pages")


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
    result = build_storybook_pdf(isolated_project)
    data = result.output_path.read_bytes()
    assert data.startswith(b"%PDF-")
    assert _pdf_page_count(data) == result.page_count
    assert result.manifest_path.is_file()
    assert result.summary_path.is_file()
    assert len(result.image_paths) == result.page_count


def test_build_storybook_pdf_removes_stale_page_images(isolated_project) -> None:
    stale_dir = isolated_project / "output" / "figures" / "storybook_pages"
    stale_dir.mkdir(parents=True)
    stale = stale_dir / "99_retired_page.png"
    stale.write_bytes(b"old page")

    build_storybook_pdf(isolated_project)

    assert not stale.exists()


def test_render_story_number_uses_configured_filename(isolated_project) -> None:
    path = render_story_number(isolated_project, 2)
    assert path.name == "02_square_house.png"
    assert path.is_file()


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
