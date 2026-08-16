"""Real-filesystem regressions for format-aware Stage 4/5 gates."""

from __future__ import annotations

import subprocess
import sys
import zipfile
import zlib
from pathlib import Path

import pytest

from infrastructure.core.pipeline.artifacts import collect_stable_output_inventory, output_inventory_mode_for_project
from infrastructure.project.discovery import resolve_project_root
from infrastructure.rendering._epub_package_validation import (
    MAX_EPUB_COMPRESSION_RATIO,
    MAX_EPUB_MEMBER_BYTES,
    validate_epub_package,
)
from infrastructure.validation.output.pipeline import (
    _build_core_checks,
    execute_validation_pipeline,
    verify_outputs_exist,
)
from infrastructure.validation.output.render_formats import (
    enabled_render_formats,
    load_effective_rendering_config,
    remove_disabled_render_outputs,
    validate_enabled_render_outputs,
)


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


def _patch_central_directory_size(
    path: Path, member: str, *, compressed: int | None = None, size: int | None = None
) -> None:
    """Patch one member's central-directory sizes without expanding payloads."""

    payload = bytearray(path.read_bytes())
    cursor = 0
    while True:
        header = payload.find(b"PK\x01\x02", cursor)
        if header < 0:
            raise AssertionError(f"ZIP central-directory member not found: {member}")
        name_length = int.from_bytes(payload[header + 28 : header + 30], "little")
        extra_length = int.from_bytes(payload[header + 30 : header + 32], "little")
        comment_length = int.from_bytes(payload[header + 32 : header + 34], "little")
        name_start = header + 46
        name_end = name_start + name_length
        if payload[name_start:name_end].decode("utf-8") == member:
            if compressed is not None:
                payload[header + 20 : header + 24] = compressed.to_bytes(4, "little")
            if size is not None:
                payload[header + 24 : header + 28] = size.to_bytes(4, "little")
            path.write_bytes(payload)
            return
        cursor = name_end + extra_length + comment_length


def _corrupt_member_payload(path: Path, member: str) -> None:
    """Corrupt one real member and prove that reading it cannot succeed."""

    with zipfile.ZipFile(path) as archive:
        info = archive.getinfo(member)
    payload = bytearray(path.read_bytes())
    local_header = info.header_offset
    name_length = int.from_bytes(payload[local_header + 26 : local_header + 28], "little")
    extra_length = int.from_bytes(payload[local_header + 28 : local_header + 30], "little")
    data_start = local_header + 30 + name_length + extra_length
    assert info.compress_size > 0
    payload[data_start + info.compress_size // 2] ^= 0xFF
    path.write_bytes(payload)

    with zipfile.ZipFile(path) as archive:
        try:
            corrupt_member = archive.testzip()
        except (zipfile.BadZipFile, zlib.error):
            return
    assert corrupt_member == member


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


def test_stage4_html_only_accepts_clean_tree(tmp_path) -> None:
    _html_only_project(tmp_path)

    checks = {check.name: check.run for check in _build_core_checks("demo", repo_root=tmp_path)}

    assert "PDF validation" not in checks
    assert "Transmission bookends" not in checks
    assert checks["Enabled render outputs"]() is True


def test_stage4_html_only_full_stage_succeeds_without_pdf(tmp_path) -> None:
    _html_only_project(tmp_path)
    recorded_checks = {}

    def report_writer(check_results, *_args, **_kwargs):
        recorded_checks.update(check_results)
        return {"timestamp": "1970-01-01T00:00:00Z"}

    assert execute_validation_pipeline("demo", repo_root=tmp_path, report_writer=report_writer) == 0
    assert recorded_checks["Output structure"] is True


def test_stage4_html_only_detailed_structure_does_not_invent_pdf(tmp_path) -> None:
    _html_only_project(tmp_path)

    valid, details = verify_outputs_exist(
        "demo",
        repo_root=tmp_path,
        require_pdf=False,
        enabled_formats={"html"},
    )

    assert valid is True
    assert details["structure"]["missing_files"] == []
    assert details["structure"]["directory_structure"]["combined_pdf"]["required"] is False
    assert details["structure"]["directory_structure"]["slides"]["required"] is False
    assert details["structure"]["directory_structure"]["docx"]["required"] is False
    assert details["structure"]["directory_structure"]["epub"]["required"] is False
    assert not any(
        name in message
        for message in details["issues_by_severity"]["info"]
        for name in ("pdf/", "slides/", "docx/", "epub/")
    )


def test_stage4_html_only_rejects_stale_disabled_pdf(tmp_path) -> None:
    project_root = _html_only_project(tmp_path)
    stale_pdf = project_root / "output" / "pdf" / "old_section.pdf"
    stale_pdf.parent.mkdir(parents=True)
    stale_pdf.write_bytes(_minimal_pdf())

    checks = {check.name: check.run for check in _build_core_checks("demo", repo_root=tmp_path)}

    assert checks["Enabled render outputs"]() is False


def test_stage4_pdf_requires_canonical_combined_pdf(tmp_path) -> None:
    project_root = tmp_path / "projects" / "active" / "demo"
    manuscript_dir = project_root / "manuscript"
    manuscript_dir.mkdir(parents=True)
    (manuscript_dir / "01_intro.md").write_text("# Intro\n", encoding="utf-8")
    (manuscript_dir / "config.yaml").write_text(
        "render:\n  formats:\n    pdf: true\n    html: false\n    slides: false\n",
        encoding="utf-8",
    )
    pdf_dir = project_root / "output" / "pdf"
    pdf_dir.mkdir(parents=True)
    (pdf_dir / "other_valid.pdf").write_bytes(_minimal_pdf())

    checks = {check.name: check.run for check in _build_core_checks("demo", repo_root=tmp_path)}

    assert checks["PDF validation"]() is True
    assert checks["Enabled render outputs"]() is False


def test_enabled_pdf_cannot_be_gitignored_publication_evidence(tmp_path) -> None:
    """Structural validity cannot substitute for a shippable PDF."""
    output_dir = tmp_path / "output"
    pdf = output_dir / "pdf" / "demo_combined.pdf"
    pdf.parent.mkdir(parents=True)
    pdf.write_bytes(_minimal_pdf())
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / ".gitignore").write_text("output/pdf/*.pdf\n", encoding="utf-8")

    assert (
        validate_enabled_render_outputs(
            output_dir,
            "demo",
            {"pdf"},
            pdf_validator=lambda: True,
        )
        is False
    )


def test_managed_external_project_accepts_valid_ignored_local_pdf(tmp_path) -> None:
    """A lifecycle sidecar's blanket output ignore is local scope, not absence."""
    repo_root = tmp_path / "template"
    external_project = tmp_path / "private" / "demo"
    manuscript = external_project / "manuscript"
    manuscript.mkdir(parents=True)
    (manuscript / "01_intro.md").write_text("# Intro\n", encoding="utf-8")
    (manuscript / "config.yaml").write_text(
        "render:\n  formats:\n    pdf: true\n    html: false\n    slides: false\n    docx: false\n    epub: false\n",
        encoding="utf-8",
    )
    pdf = external_project / "output" / "pdf" / "demo_combined.pdf"
    pdf.parent.mkdir(parents=True)
    pdf.write_bytes(_minimal_pdf())
    subprocess.run(["git", "init", "-q"], cwd=external_project, check=True, capture_output=True)
    (external_project / ".gitignore").write_text("output/\n", encoding="utf-8")
    managed_link = repo_root / "projects" / "working" / "demo"
    managed_link.parent.mkdir(parents=True)
    managed_link.symlink_to(external_project, target_is_directory=True)

    resolved = resolve_project_root(repo_root, "working/demo")
    inventory = collect_stable_output_inventory(
        resolved / "output",
        inventory_mode=output_inventory_mode_for_project(repo_root, resolved),
    )

    assert resolved == external_project.resolve()
    assert inventory.mode == "stable-local-output-v1"
    assert pdf.absolute() in inventory.files
    checks = {check.name: check.run for check in _build_core_checks("working/demo", repo_root=repo_root)}
    assert checks["Enabled render outputs"]() is True
    assert (
        validate_enabled_render_outputs(
            resolved / "output",
            "working/demo",
            {"pdf"},
            pdf_validator=lambda: True,
            inventory=inventory,
        )
        is True
    )


def test_public_template_blanket_ignore_cannot_downgrade_shippable_gate(tmp_path) -> None:
    """A public ignore-policy regression must expose an empty release inventory."""
    repo_root = tmp_path / "template"
    project = repo_root / "projects" / "templates" / "demo"
    pdf = project / "output" / "pdf" / "demo_combined.pdf"
    pdf.parent.mkdir(parents=True)
    pdf.write_bytes(_minimal_pdf())
    subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True, capture_output=True)
    (repo_root / ".gitignore").write_text("projects/templates/demo/output/\n", encoding="utf-8")

    inventory = collect_stable_output_inventory(
        project / "output",
        inventory_mode=output_inventory_mode_for_project(repo_root, project),
    )

    assert inventory.mode == "stable-shippable-output-v1"
    assert inventory.files == ()
    assert (
        validate_enabled_render_outputs(
            project / "output",
            "templates/demo",
            {"pdf"},
            pdf_validator=lambda: True,
            inventory=inventory,
        )
        is False
    )


def test_enabled_format_stability_accepts_relative_output_and_supplied_inventory(tmp_path, monkeypatch) -> None:
    """Relative callers and absolute inventory paths must share one identity."""
    monkeypatch.chdir(tmp_path)
    output_dir = Path("output")
    pdf = output_dir / "pdf" / "demo_combined.pdf"
    pdf.parent.mkdir(parents=True)
    pdf.write_bytes(_minimal_pdf())
    inventory = collect_stable_output_inventory(output_dir)

    assert (
        validate_enabled_render_outputs(
            output_dir,
            "demo",
            {"pdf"},
            pdf_validator=lambda: True,
            inventory=inventory,
        )
        is True
    )


def test_enabled_docx_cannot_be_gitignored_publication_evidence(tmp_path) -> None:
    """A valid ignored DOCX package must fail the release inventory gate."""
    output_dir = tmp_path / "output"
    docx = output_dir / "docx" / "demo_combined.docx"
    docx.parent.mkdir(parents=True)
    with zipfile.ZipFile(docx, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", "<document/>")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / ".gitignore").write_text("output/docx/*.docx\n", encoding="utf-8")

    assert validate_enabled_render_outputs(output_dir, "demo", {"docx"}) is False


def test_enabled_epub_cannot_be_gitignored_publication_evidence(tmp_path) -> None:
    """A valid ignored EPUB package must fail the release inventory gate."""
    output_dir = tmp_path / "output"
    epub = output_dir / "epub" / "demo_combined.epub"
    _write_epub(epub)
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / ".gitignore").write_text("output/epub/*.epub\n", encoding="utf-8")

    assert validate_enabled_render_outputs(output_dir, "demo", {"epub"}) is False


def test_enabled_epub_parses_container_opf_and_every_xhtml_document(tmp_path) -> None:
    """A complete, well-formed package satisfies the enabled EPUB gate."""

    output_dir = tmp_path / "output"
    _write_epub(output_dir / "epub" / "demo_combined.epub")

    assert validate_enabled_render_outputs(output_dir, "demo", {"epub"}) is True


def test_enabled_epub_rejects_malformed_declared_xhtml(tmp_path) -> None:
    """ZIP integrity cannot green an XHTML document that is not XML."""

    output_dir = tmp_path / "output"
    _write_epub(
        output_dir / "epub" / "demo_combined.epub",
        xhtml=(
            '<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Chapter</title></head>'
            "<body><p>Line break<br>is malformed XHTML.</p></body></html>"
        ),
    )

    assert validate_enabled_render_outputs(output_dir, "demo", {"epub"}) is False


def test_enabled_epub_rejects_xml_entity_declarations(tmp_path) -> None:
    """The lazy parser boundary retains defusedxml's entity protections."""

    output_dir = tmp_path / "output"
    _write_epub(
        output_dir / "epub" / "demo_combined.epub",
        xhtml=(
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<!DOCTYPE html [<!ENTITY injected "unsafe expansion">]>\n'
            '<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Chapter</title></head>'
            "<body><p>&injected;</p></body></html>"
        ),
    )

    assert validate_enabled_render_outputs(output_dir, "demo", {"epub"}) is False


def test_rendering_import_without_defusedxml_is_safe_but_epub_validation_fails_closed(tmp_path) -> None:
    """Standalone render imports do not require EPUB's optional safe parser."""

    project_root = tmp_path / "project"
    epub = project_root / "output" / "epub" / "demo_combined.epub"
    _write_epub(epub)
    repo_root = Path(__file__).resolve().parents[3]
    script = r"""
import sys
import zipfile
from pathlib import Path

class BlockDefusedXml:
    @staticmethod
    def find_spec(fullname, path=None, target=None):
        if fullname == "defusedxml" or fullname.startswith("defusedxml."):
            raise ModuleNotFoundError("defusedxml blocked for import-boundary regression", name=fullname)
        return None

sys.meta_path.insert(0, BlockDefusedXml())

import infrastructure.rendering
from infrastructure.rendering._epub_package_validation import validate_epub_package
from infrastructure.rendering._pipeline_summary import _verify_epub_output
from infrastructure.validation.output.render_formats import _validate_epub_output

print("rendering-import-ok")
with zipfile.ZipFile(sys.argv[1]) as archive:
    try:
        validate_epub_package(archive)
    except ValueError as exc:
        if "defusedxml" not in str(exc):
            raise
    else:
        raise AssertionError("EPUB validation passed without defusedxml")
print("epub-validation-failed-closed")
if _verify_epub_output(Path(sys.argv[2]), "demo") is not False:
    raise AssertionError("Stage 3 accepted EPUB without defusedxml")
if _validate_epub_output(Path(sys.argv[2]) / "output", "demo") is not False:
    raise AssertionError("Stage 4/5 accepted EPUB without defusedxml")
print("epub-callers-returned-false")
"""

    completed = subprocess.run(
        [sys.executable, "-c", script, str(epub), str(project_root)],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert "rendering-import-ok" in completed.stdout
    assert "epub-validation-failed-closed" in completed.stdout
    assert "epub-callers-returned-false" in completed.stdout


def test_enabled_epub_rejects_archive_escaping_rootfile(tmp_path) -> None:
    """Container references may not traverse outside the archive root."""

    output_dir = tmp_path / "output"
    _write_epub(output_dir / "epub" / "demo_combined.epub", rootfile="../content.opf")

    assert validate_enabled_render_outputs(output_dir, "demo", {"epub"}) is False


def test_enabled_epub_rejects_duplicate_xhtml_targets(tmp_path) -> None:
    """Two manifest identities cannot ambiguously bind the same XHTML member."""

    output_dir = tmp_path / "output"
    _write_epub(output_dir / "epub" / "demo_combined.epub", duplicate_target=True)

    assert validate_enabled_render_outputs(output_dir, "demo", {"epub"}) is False


@pytest.mark.parametrize(
    "manifest_item",
    [
        '<item id="image" href="../../escape.png" media-type="image/png"/>',
        '<item id="image" href="images/missing.png" media-type="image/png"/>',
    ],
)
def test_enabled_epub_rejects_unsafe_or_missing_non_xhtml_manifest_target(
    tmp_path,
    manifest_item: str,
) -> None:
    """Every local OPF manifest target is safe and present, not only XHTML."""

    output_dir = tmp_path / "output"
    _write_epub(
        output_dir / "epub" / "demo_combined.epub",
        extra_manifest_item=manifest_item,
    )

    assert validate_enabled_render_outputs(output_dir, "demo", {"epub"}) is False


@pytest.mark.parametrize("alt_attribute", ["", ' alt=""'])
def test_enabled_epub_rejects_missing_or_blank_non_decorative_image_alt(
    tmp_path: Path,
    alt_attribute: str,
) -> None:
    """Packaged XHTML images require explicit, non-blank accessibility text."""

    output_dir = tmp_path / "output"
    _write_epub(
        output_dir / "epub" / "demo_combined.epub",
        xhtml=(
            '<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Chapter</title></head>'
            f'<body><img src="../images/figure.png"{alt_attribute}/></body></html>'
        ),
        extra_manifest_item='<item id="figure" href="images/figure.png" media-type="image/png"/>',
        extra_members={"EPUB/images/figure.png": b"real-image-payload"},
    )

    assert validate_enabled_render_outputs(output_dir, "demo", {"epub"}) is False


def test_enabled_epub_rejects_pandoc_svg_cover_without_accessible_name(tmp_path: Path) -> None:
    """Regression: Pandoc's raw SVG cover shape cannot ship without config alt."""

    output_dir = tmp_path / "output"
    _write_epub(
        output_dir / "epub" / "demo_combined.epub",
        xhtml=(
            '<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Cover</title></head><body>'
            '<svg xmlns="http://www.w3.org/2000/svg" '
            'xmlns:xlink="http://www.w3.org/1999/xlink">'
            '<image xlink:href="../images/cover.png"/></svg></body></html>'
        ),
        extra_manifest_item=(
            '<item id="cover" href="images/cover.png" media-type="image/png" properties="cover-image"/>'
        ),
        extra_members={"EPUB/images/cover.png": b"real-cover-payload"},
    )

    assert validate_enabled_render_outputs(output_dir, "demo", {"epub"}) is False


def test_enabled_epub_accepts_named_svg_cover_with_hidden_bitmap_primitive(tmp_path: Path) -> None:
    """The cover SVG is one named graphic; its bitmap primitive is not re-announced."""

    output_dir = tmp_path / "output"
    _write_epub(
        output_dir / "epub" / "demo_combined.epub",
        xhtml=(
            '<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Cover</title></head><body>'
            '<svg xmlns="http://www.w3.org/2000/svg" '
            'xmlns:xlink="http://www.w3.org/1999/xlink" role="img" aria-labelledby="cover-title">'
            '<title id="cover-title">A meaningful cover description.</title>'
            '<image xlink:href="../images/cover.png" aria-hidden="true" focusable="false"/>'
            "</svg></body></html>"
        ),
        extra_manifest_item=(
            '<item id="cover" href="images/cover.png" media-type="image/png" properties="cover-image"/>'
        ),
        extra_members={"EPUB/images/cover.png": b"real-cover-payload"},
    )

    assert validate_enabled_render_outputs(output_dir, "demo", {"epub"}) is True


def test_enabled_epub_rejects_spine_reference_to_non_xhtml_item(tmp_path) -> None:
    """The reading order may reference only declared XHTML manifest items."""

    output_dir = tmp_path / "output"
    _write_epub(
        output_dir / "epub" / "demo_combined.epub",
        spine_idref="missing",
    )

    assert validate_enabled_render_outputs(output_dir, "demo", {"epub"}) is False


@pytest.mark.parametrize("directory_name", ["../escape/", "/absolute/", "C:/absolute/"])
def test_enabled_epub_rejects_unsafe_directory_entries(tmp_path, directory_name: str) -> None:
    """Directory ZipInfo names obey the same canonical confinement as files."""

    output_dir = tmp_path / "output"
    epub = output_dir / "epub" / "demo_combined.epub"
    _write_epub(epub)
    with zipfile.ZipFile(epub, "a") as archive:
        archive.writestr(directory_name, b"")

    assert validate_enabled_render_outputs(output_dir, "demo", {"epub"}) is False


def test_enabled_epub_rejects_zip_symlink_member(tmp_path) -> None:
    """Unix-mode symlink entries cannot masquerade as publication resources."""

    output_dir = tmp_path / "output"
    epub = output_dir / "epub" / "demo_combined.epub"
    _write_epub(epub)
    link = zipfile.ZipInfo("EPUB/link.png")
    link.create_system = 3
    link.external_attr = (0o120777 << 16) | 0xA000
    with zipfile.ZipFile(epub, "a") as archive:
        archive.writestr(link, b"../outside.png")

    assert validate_enabled_render_outputs(output_dir, "demo", {"epub"}) is False


def test_enabled_epub_rejects_file_used_as_parent_directory(tmp_path) -> None:
    """A file entry cannot also act as the parent of package members."""

    output_dir = tmp_path / "output"
    epub = output_dir / "epub" / "demo_combined.epub"
    _write_epub(epub)
    with zipfile.ZipFile(epub, "a") as archive:
        archive.writestr("EPUB", b"not a directory")

    assert validate_enabled_render_outputs(output_dir, "demo", {"epub"}) is False


def test_epub_oversized_metadata_fails_before_any_member_read(tmp_path) -> None:
    """A forged uncompressed size is rejected before CRC/decompression work."""

    epub = tmp_path / "oversized.epub"
    _write_epub(epub)
    _corrupt_member_payload(epub, "EPUB/text/chapter.xhtml")
    _patch_central_directory_size(
        epub,
        "EPUB/text/chapter.xhtml",
        size=MAX_EPUB_MEMBER_BYTES + 1,
    )

    with zipfile.ZipFile(epub) as archive:
        with pytest.raises(ValueError, match="exceeds size limit"):
            validate_epub_package(archive)


def test_epub_hostile_ratio_metadata_fails_before_any_member_read(tmp_path) -> None:
    """A forged compression-bomb ratio is rejected from metadata alone."""

    epub = tmp_path / "ratio.epub"
    _write_epub(epub)
    _corrupt_member_payload(epub, "EPUB/text/chapter.xhtml")
    hostile_size = MAX_EPUB_COMPRESSION_RATIO + 1
    _patch_central_directory_size(
        epub,
        "EPUB/text/chapter.xhtml",
        compressed=1,
        size=hostile_size,
    )

    with zipfile.ZipFile(epub) as archive:
        with pytest.raises(ValueError, match="compression-ratio limit"):
            validate_epub_package(archive)


def test_stage5_filter_removes_disabled_outputs_but_preserves_authored_web(tmp_path) -> None:
    output_dir = tmp_path / "output" / "active" / "demo"
    web_dir = output_dir / "web"
    web_dir.mkdir(parents=True)
    (web_dir / "index.html").write_text("<!doctype html><html><body>Current</body></html>\n", encoding="utf-8")
    (web_dir / "dashboard.html").write_text("<!doctype html><html><body>Dashboard</body></html>\n", encoding="utf-8")
    for directory, filename in (
        ("pdf", "old.pdf"),
        ("slides", "old_slides.pdf"),
        ("docx", "demo_combined.docx"),
        ("epub", "demo_combined.epub"),
    ):
        path = output_dir / directory / filename
        path.parent.mkdir(parents=True)
        path.write_bytes(b"stale")
    (output_dir / "demo_combined.pdf").write_bytes(_minimal_pdf())

    removed = remove_disabled_render_outputs(output_dir, "active/demo", {"html"})

    assert removed
    assert not (output_dir / "demo_combined.pdf").exists()
    assert not (output_dir / "pdf").exists()
    assert not (output_dir / "slides").exists()
    assert not (output_dir / "docx").exists()
    assert not (output_dir / "epub").exists()
    assert (web_dir / "index.html").is_file()
    assert (web_dir / "dashboard.html").is_file()
    assert validate_enabled_render_outputs(output_dir, "active/demo", {"html"}) is True


def test_stage5_filter_preserves_cross_format_composition_evidence(tmp_path) -> None:
    output_dir = tmp_path / "output" / "active" / "demo"
    web_dir = output_dir / "web"
    reports_dir = output_dir / "reports"
    web_dir.mkdir(parents=True)
    reports_dir.mkdir(parents=True)
    combined = web_dir / "_combined_manuscript.md"
    composition = reports_dir / "manuscript_composition.json"
    combined.write_text("# Current combined source\n", encoding="utf-8")
    composition.write_text('{"combined_path":"output/web/_combined_manuscript.md"}\n', encoding="utf-8")
    (web_dir / "index.html").write_text("<!doctype html><html></html>\n", encoding="utf-8")
    (web_dir / "manuscript__01_intro.html").write_text("<!doctype html><html></html>\n", encoding="utf-8")
    (web_dir / "favicon.ico").write_bytes(b"stale renderer favicon")

    remove_disabled_render_outputs(output_dir, "active/demo", {"docx"})

    assert combined.is_file()
    assert composition.is_file()
    assert not (web_dir / "index.html").exists()
    assert not (web_dir / "manuscript__01_intro.html").exists()
    assert not (web_dir / "favicon.ico").exists()


def test_disabled_html_rejects_renderer_owned_stale_favicon(tmp_path) -> None:
    output_dir = tmp_path / "output"
    docx = output_dir / "docx" / "demo_combined.docx"
    docx.parent.mkdir(parents=True)
    with zipfile.ZipFile(docx, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", "<document/>")
    favicon = output_dir / "web" / "favicon.ico"
    favicon.parent.mkdir(parents=True)
    favicon.write_bytes(b"stale renderer favicon")

    assert validate_enabled_render_outputs(output_dir, "demo", {"docx"}) is False


def test_enable_pdf_environment_override_remains_strict(tmp_path) -> None:
    project_root = _html_only_project(tmp_path)
    config = load_effective_rendering_config(project_root, env={"ENABLE_PDF": "1"})

    formats = enabled_render_formats(config)

    assert formats == {"html", "pdf"}
    assert validate_enabled_render_outputs(project_root / "output", "demo", formats) is False


def test_legacy_pdf_override_forces_same_pdf_only_contract_in_later_stages(tmp_path) -> None:
    project_root = _html_only_project(tmp_path)
    override = project_root / "scripts" / "_render_pdf_override.py"
    override.parent.mkdir(parents=True)
    override.write_text("raise SystemExit(0)\n", encoding="utf-8")

    config = load_effective_rendering_config(
        project_root,
        env={"ENABLE_HTML": "1", "ENABLE_SLIDES": "1", "ENABLE_DOCX": "1"},
    )

    assert enabled_render_formats(config) == {"pdf"}


def test_slides_enabled_requires_at_least_one_current_deck(tmp_path) -> None:
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    (manuscript_dir / "01_intro.md").write_text(
        "<!-- render:skip-beamer -->\n# Intro\n",
        encoding="utf-8",
    )
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    assert (
        validate_enabled_render_outputs(
            output_dir,
            "demo",
            {"slides"},
            manuscript_dir=manuscript_dir,
        )
        is False
    )


def test_slides_enabled_rejects_deck_for_deleted_source(tmp_path) -> None:
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    (manuscript_dir / "01_current.md").write_text("# Current\n", encoding="utf-8")
    slides_dir = tmp_path / "output" / "slides"
    slides_dir.mkdir(parents=True)
    (slides_dir / "01_current_slides.pdf").write_bytes(_minimal_pdf())
    (slides_dir / "00_deleted_slides.pdf").write_bytes(_minimal_pdf())

    assert (
        validate_enabled_render_outputs(
            tmp_path / "output",
            "demo",
            {"slides"},
            manuscript_dir=manuscript_dir,
        )
        is False
    )
