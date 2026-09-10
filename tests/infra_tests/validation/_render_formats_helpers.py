"""Shared minimal PDF/EPUB builders and HTML-only project fixtures for render-format gate tests."""

from __future__ import annotations
import zipfile
from pathlib import Path


def _minimal_pdf() -> bytes:
    return b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\nstartxref\n0\n%%EOF\n"


def _write_epub(
    path: Path,
    *,
    xhtml: str | None = None,
    rootfile: str = "EPUB/content.opf",
    item_href: str = "text/chapter.xhtml",
    duplicate_target: bool = False,
    extra_manifest_item: str = "",
    extra_members: dict[str, bytes] | None = None,
    spine_idref: str = "chapter",
) -> None:
    """Write a compact real EPUB package for format-gate regressions."""

    path.parent.mkdir(parents=True, exist_ok=True)
    chapter = xhtml or (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Chapter</title></head>'
        "<body><p>Current content.</p></body></html>"
    )
    duplicate_item = (
        f'<item id="chapter-copy" href="{item_href}" media-type="application/xhtml+xml"/>' if duplicate_target else ""
    )
    container = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
        f'<rootfiles><rootfile full-path="{rootfile}" '
        'media-type="application/oebps-package+xml"/></rootfiles></container>'
    )
    package = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="book-id">'
        '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">'
        '<dc:identifier id="book-id">urn:uuid:test</dc:identifier>'
        "<dc:title>Test</dc:title><dc:language>en</dc:language></metadata>"
        f'<manifest><item id="chapter" href="{item_href}" media-type="application/xhtml+xml"/>'
        f'{duplicate_item}{extra_manifest_item}</manifest><spine><itemref idref="{spine_idref}"/>'
        "</spine></package>"
    )
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        archive.writestr("META-INF/container.xml", container)
        archive.writestr("EPUB/content.opf", package)
        archive.writestr("EPUB/text/chapter.xhtml", chapter)
        for member, payload in sorted((extra_members or {}).items()):
            archive.writestr(member, payload)


def _html_only_project(tmp_path):
    project_root = tmp_path / "projects" / "active" / "demo"
    manuscript_dir = project_root / "manuscript"
    manuscript_dir.mkdir(parents=True)
    (manuscript_dir / "01_intro.md").write_text("# Intro\n\nCurrent prose.\n", encoding="utf-8")
    (manuscript_dir / "config.yaml").write_text(
        "render:\n  formats:\n    pdf: false\n    html: true\n    slides: false\n    docx: false\n    epub: false\n",
        encoding="utf-8",
    )
    web_dir = project_root / "output" / "web"
    web_dir.mkdir(parents=True)
    (web_dir / "index.html").write_text("<!doctype html><html><body>Current</body></html>\n", encoding="utf-8")
    return project_root
