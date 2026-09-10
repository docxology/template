"""EPUB/DOCX package integrity, security boundary, metadata-bomb, and safe-import fallback regressions."""

from __future__ import annotations
import subprocess
import sys
import zipfile
import zlib
from pathlib import Path
import pytest
from infrastructure.rendering._epub_package_validation import (
    MAX_EPUB_COMPRESSION_RATIO,
    MAX_EPUB_MEMBER_BYTES,
    validate_epub_package,
)
from infrastructure.validation.output.render_formats import validate_enabled_render_outputs
from tests.infra_tests.validation._render_formats_helpers import _write_epub


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


def test_enabled_epub_parses_container_opf_and_every_xhtml_document(tmp_path) -> None:
    """A complete, well-formed package satisfies the enabled EPUB gate."""

    output_dir = tmp_path / "output"
    _write_epub(output_dir / "epub" / "demo_combined.epub")

    assert validate_enabled_render_outputs(output_dir, "demo", {"epub"}) is True


def test_enabled_docx_rejects_nested_legacy_combined_package(tmp_path) -> None:
    """Stage 4 rejects a recursively nested combined DOCX with stale identity."""

    output_dir = tmp_path / "output"
    for path in (
        output_dir / "docx" / "demo_combined.docx",
        output_dir / "docx" / "templates" / "old_project_combined.docx",
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("[Content_Types].xml", "<Types/>")
            archive.writestr("word/document.xml", "<document/>")

    assert validate_enabled_render_outputs(output_dir, "demo", {"docx"}) is False


def test_enabled_epub_rejects_nested_legacy_combined_package(tmp_path) -> None:
    """Stage 4 rejects a recursively nested combined EPUB with stale identity."""

    output_dir = tmp_path / "output"
    _write_epub(output_dir / "epub" / "demo_combined.epub")
    _write_epub(output_dir / "epub" / "templates" / "old_project_combined.epub")

    assert validate_enabled_render_outputs(output_dir, "demo", {"epub"}) is False


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
