"""Tests for EPUB renderer - no mocks, runs real pandoc."""

from __future__ import annotations

import shutil
import stat
import sys
import uuid
import zipfile
from pathlib import Path

import defusedxml.ElementTree as safe_et
import pytest

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering.epub_renderer import (
    EpubRenderResult,
    _epub_source_date_epoch,
    _normalize_epub_archive,
    render_epub,
)


pytestmark = pytest.mark.skipif(
    shutil.which("pandoc") is None,
    reason="pandoc not installed",
)


SAMPLE_MD = """---
title: "EPUB Renderer Smoke Test"
author: Template Test
lang: en
---

# Chapter 1

A paragraph of text in the first chapter.

# Chapter 2

A second chapter with **bold** and *italic* text.
"""

# 1x1 PNG — smallest real image, used for cover and body-media determinism.
_PNG_1x1 = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


def test_render_epub_produces_nonempty_file(tmp_path: Path) -> None:
    src = tmp_path / "combined.md"
    src.write_text(SAMPLE_MD, encoding="utf-8")
    out = tmp_path / "out.epub"

    result = render_epub(src, out)

    assert isinstance(result, EpubRenderResult)
    assert result.output_path == out
    assert out.exists()
    assert out.stat().st_size > 1024
    assert result.size_bytes == out.stat().st_size
    assert result.duration_seconds >= 0.0


def test_render_epub_contains_title(tmp_path: Path) -> None:
    """EPUB is a ZIP; verify pandoc emitted title metadata."""
    src = tmp_path / "combined.md"
    src.write_text(SAMPLE_MD, encoding="utf-8")
    out = tmp_path / "out.epub"

    render_epub(src, out)

    with zipfile.ZipFile(out) as zip_file:
        names = zip_file.namelist()
        opf_name = next((name for name in names if name.endswith(".opf")), None)
        assert opf_name is not None, f"no .opf manifest found in EPUB: {names}"
        opf = zip_file.read(opf_name).decode("utf-8")
    assert "<dc:title>EPUB Renderer Smoke Test</dc:title>" in opf or "EPUB Renderer Smoke Test" in opf


def test_render_epub_missing_source_raises(tmp_path: Path) -> None:
    out = tmp_path / "out.epub"
    with pytest.raises(FileNotFoundError):
        render_epub(tmp_path / "missing.md", out)


def _opf_text(epub_path: Path) -> str:
    with zipfile.ZipFile(epub_path) as zip_file:
        names = zip_file.namelist()
        opf_name = next((name for name in names if name.endswith(".opf")), None)
        assert opf_name is not None, f"no .opf manifest found in EPUB: {names}"
        return zip_file.read(opf_name).decode("utf-8")


def _package_identifiers(epub_path: Path) -> tuple[str, str]:
    """Return the OPF package identifier and NCX navigation UID."""

    with zipfile.ZipFile(epub_path) as archive:
        opf_name = next(name for name in archive.namelist() if name.endswith(".opf"))
        ncx_name = next(name for name in archive.namelist() if name.endswith(".ncx"))
        opf = safe_et.fromstring(archive.read(opf_name))
        ncx = safe_et.fromstring(archive.read(ncx_name))

    identifier = opf.find(".//{http://purl.org/dc/elements/1.1/}identifier")
    assert identifier is not None and identifier.text is not None
    navigation_uid = next(
        node.get("content")
        for node in ncx.findall(".//{http://www.daisy.org/z3986/2005/ncx/}meta")
        if node.get("name") == "dtb:uid"
    )
    assert navigation_uid is not None
    return identifier.text, navigation_uid


def _copy_epub_with_member_replacements(
    source_path: Path,
    destination_path: Path,
    *,
    member_suffix: str,
    replacements: tuple[tuple[bytes, bytes], ...],
) -> None:
    """Copy one EPUB while applying exact byte replacements to one member."""

    matched = False
    with zipfile.ZipFile(source_path) as source:
        with zipfile.ZipFile(destination_path, "w") as destination:
            destination.comment = source.comment
            for info in source.infolist():
                payload = b"" if info.is_dir() else source.read(info)
                if info.filename.endswith(member_suffix):
                    matched = True
                    for old, new in replacements:
                        assert payload.count(old) == 1
                        payload = payload.replace(old, new, 1)
                destination.writestr(info, payload)
    assert matched


def _write_executable(path: Path, body: str) -> Path:
    """Write one real caller-selected Pandoc substitute executable."""

    path.write_text(f"#!{sys.executable}\n{body}", encoding="utf-8")
    path.chmod(0o755)
    return path


def _write_hostile_pandoc(
    path: Path,
    *,
    archive_statements: str,
    payload_mutation: str = "",
) -> Path:
    """Write a success-exit binary whose ZIP has a corrupt first payload."""

    return _write_executable(
        path,
        "import sys\n"
        "import zipfile\n"
        "from pathlib import Path\n"
        "arguments = sys.argv[1:]\n"
        'target = Path(arguments[arguments.index("-o") + 1])\n'
        'with zipfile.ZipFile(target, "w") as archive:\n'
        f"{archive_statements}\n"
        "with zipfile.ZipFile(target) as archive:\n"
        '    mimetype = archive.getinfo("mimetype")\n'
        "payload = bytearray(target.read_bytes())\n"
        f"{payload_mutation}"
        "header = mimetype.header_offset\n"
        'name_length = int.from_bytes(payload[header + 26:header + 28], "little")\n'
        'extra_length = int.from_bytes(payload[header + 28:header + 30], "little")\n'
        "payload[header + 30 + name_length + extra_length] ^= 0xFF\n"
        "target.write_bytes(payload)\n",
    )


# Frontmatter-free source: real combined-manuscript markdown has no YAML
# frontmatter (title/author/language live only in the project's separate
# manuscript/config.yaml), which is exactly the gap that let a real EPUB
# ship with no dc:title/dc:creator and an invalid dc:language ("C", the
# POSIX locale name) — see 11_ebook_generation.py's _load_manuscript_metadata.
_NO_FRONTMATTER_MD = "# Chapter 1\n\nA paragraph with no YAML frontmatter at all.\n"


def test_render_epub_without_metadata_args_omits_title_and_creator(tmp_path: Path) -> None:
    """Regression: source markdown with no frontmatter must not silently ship untitled."""
    src = tmp_path / "combined.md"
    src.write_text(_NO_FRONTMATTER_MD, encoding="utf-8")
    out = tmp_path / "out.epub"

    render_epub(src, out)

    opf = _opf_text(out)
    assert "<dc:title>" not in opf
    assert "<dc:creator" not in opf


def test_render_epub_metadata_args_populate_title_and_creator(tmp_path: Path) -> None:
    """title=/author=/language= must reach the OPF even with frontmatter-free source."""
    src = tmp_path / "combined.md"
    src.write_text(_NO_FRONTMATTER_MD, encoding="utf-8")
    out = tmp_path / "out.epub"

    render_epub(src, out, title="Explicit Title", author="Explicit Author", language="en-US")

    opf = _opf_text(out)
    assert ">Explicit Title</dc:title>" in opf
    assert ">Explicit Author</dc:creator>" in opf
    assert "<dc:language>en-US</dc:language>" in opf


def test_render_epub_default_language_is_not_locale_dependent(tmp_path: Path) -> None:
    """Without an explicit language=, must default to 'en', never fall through to the host locale."""
    src = tmp_path / "combined.md"
    src.write_text(_NO_FRONTMATTER_MD, encoding="utf-8")
    out = tmp_path / "out.epub"

    render_epub(src, out)

    opf = _opf_text(out)
    assert "<dc:language>en</dc:language>" in opf


def test_render_epub_is_byte_deterministic_and_source_bound(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Two real Pandoc renders are identical and share one source-bound UUID."""

    monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
    monkeypatch.setenv("GIT_DIR", str(tmp_path / "poisoned-first.git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(tmp_path / "poisoned-first-tree"))

    src = tmp_path / "combined.md"
    src.write_text(SAMPLE_MD, encoding="utf-8")
    cover = tmp_path / "cover.png"
    cover.write_bytes(_PNG_1x1)
    first = tmp_path / "first.epub"
    second = tmp_path / "second.epub"
    changed = tmp_path / "changed.epub"
    first.touch()
    first.chmod(0o640)

    render_epub(
        src,
        first,
        author="Stable Author",
        cover_alt="A blue square used as a deterministic cover fixture.",
        cover_image=cover,
        title="Stable Title",
    )
    monkeypatch.setenv("GIT_DIR", str(tmp_path / "poisoned-second.git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(tmp_path / "poisoned-second-tree"))
    render_epub(
        src,
        second,
        author="Stable Author",
        cover_alt="A blue square used as a deterministic cover fixture.",
        cover_image=cover,
        title="Stable Title",
    )

    assert first.read_bytes() == second.read_bytes()
    assert stat.S_IMODE(first.stat().st_mode) == 0o640
    first_opf_id, first_ncx_id = _package_identifiers(first)
    second_opf_id, second_ncx_id = _package_identifiers(second)
    assert first_opf_id == first_ncx_id == second_opf_id == second_ncx_id
    assert first_opf_id.startswith("urn:uuid:")
    assert str(uuid.UUID(first_opf_id.removeprefix("urn:uuid:"))) in first_opf_id

    with zipfile.ZipFile(first) as archive:
        infos = archive.infolist()
        assert infos[0].filename == "mimetype"
        assert infos[0].compress_type == zipfile.ZIP_STORED
        assert {info.date_time for info in infos} == {(1980, 1, 1, 0, 0, 0)}
        opf_name = next(name for name in archive.namelist() if name.endswith(".opf"))
        assert "1980-01-01T00:00:00Z" in archive.read(opf_name).decode("utf-8")
    assert not list(tmp_path.glob(".*.epub.*.tmp"))

    src.write_text(SAMPLE_MD + "\nA source revision.\n", encoding="utf-8")
    render_epub(
        src,
        changed,
        author="Stable Author",
        cover_alt="A blue square used as a deterministic cover fixture.",
        cover_image=cover,
        title="Stable Title",
    )
    changed_opf_id, changed_ncx_id = _package_identifiers(changed)
    assert changed_opf_id == changed_ncx_id
    assert changed_opf_id != first_opf_id


def test_render_epub_honors_valid_source_date_epoch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A caller epoch controls OPF time and ZIP's two-second timestamp."""

    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000001")
    src = tmp_path / "combined.md"
    src.write_text(SAMPLE_MD, encoding="utf-8")
    output = tmp_path / "epoch.epub"
    changed_output = tmp_path / "changed-epoch.epub"

    render_epub(src, output)
    first_identifier, _ = _package_identifiers(output)

    with zipfile.ZipFile(output) as archive:
        assert {info.date_time for info in archive.infolist()} == {(2023, 11, 14, 22, 13, 20)}
        opf_name = next(name for name in archive.namelist() if name.endswith(".opf"))
        assert "2023-11-14T22:13:21Z" in archive.read(opf_name).decode("utf-8")

    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000002")
    render_epub(src, changed_output)
    changed_identifier, _ = _package_identifiers(changed_output)
    assert changed_identifier != first_identifier


@pytest.mark.parametrize(
    ("raw_epoch", "expected"),
    [
        (None, 315532800),
        ("", 315532800),
        ("1700000001", 1700000001),
        ("not-an-integer", 315532800),
        ("-1", 315532800),
        ("253402300800", 315532800),
    ],
)
def test_epub_source_date_epoch_accepts_only_supported_values(
    monkeypatch: pytest.MonkeyPatch,
    raw_epoch: str | None,
    expected: int,
) -> None:
    """Missing or invalid caller epochs resolve to the documented fixed value."""

    if raw_epoch is None:
        monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
    else:
        monkeypatch.setenv("SOURCE_DATE_EPOCH", raw_epoch)
    assert _epub_source_date_epoch() == expected


def test_normalize_epub_archive_preserves_container_metadata(tmp_path: Path) -> None:
    """ZIP normalization retains EPUB order, compression, attrs, and file mode."""

    source = tmp_path / "source.md"
    source.write_text(SAMPLE_MD, encoding="utf-8")
    rendered_path = tmp_path / "rendered.epub"
    render_epub(source, rendered_path)
    original_identifier, _ = _package_identifiers(rendered_path)

    epub_path = tmp_path / "fixture.epub"
    source_timestamp = (2026, 7, 8, 9, 10, 12)
    expected_external_attrs: list[int] = []
    with zipfile.ZipFile(rendered_path) as source_archive:
        with zipfile.ZipFile(epub_path, "w") as destination:
            destination.comment = b"fixture archive"
            for index, source_info in enumerate(source_archive.infolist()):
                target_info = zipfile.ZipInfo(source_info.filename, source_timestamp)
                target_info.compress_type = source_info.compress_type
                target_info.comment = b"required first member" if index == 0 else source_info.comment
                target_info.create_system = 3
                file_type = stat.S_IFDIR if source_info.is_dir() else stat.S_IFREG
                target_info.external_attr = (
                    0 if index == 1 else (file_type | (0o750 if source_info.is_dir() else 0o640)) << 16
                )
                target_info.internal_attr = source_info.internal_attr
                expected_external_attrs.append(target_info.external_attr)
                payload = b"" if source_info.is_dir() else source_archive.read(source_info)
                destination.writestr(target_info, payload)
                target_info.external_attr = expected_external_attrs[-1]
    epub_path.chmod(0o640)

    finalized_identifier = _normalize_epub_archive(epub_path, source_date_epoch=1700000001)

    assert finalized_identifier == original_identifier
    assert stat.S_IMODE(epub_path.stat().st_mode) == 0o640
    with zipfile.ZipFile(epub_path) as archive:
        infos = archive.infolist()
        assert archive.comment == b"fixture archive"
        assert infos[0].filename == "mimetype"
        assert infos[0].compress_type == zipfile.ZIP_STORED
        assert [info.external_attr for info in infos] == expected_external_attrs
        assert {info.create_system for info in infos} == {3}
        assert infos[0].comment == b"required first member"
        assert {info.date_time for info in infos} == {(2023, 11, 14, 22, 13, 20)}
    assert _package_identifiers(epub_path) == (original_identifier, original_identifier)
    assert not list(tmp_path.glob(".fixture.epub.*.tmp"))


def test_normalize_epub_archive_removes_temporary_after_crc_failure(tmp_path: Path) -> None:
    """An input read failure leaves the original archive and no rewrite residue."""

    source = tmp_path / "source.md"
    source.write_text(SAMPLE_MD, encoding="utf-8")
    epub_path = tmp_path / "corrupt.epub"
    render_epub(source, epub_path)
    with zipfile.ZipFile(epub_path) as archive:
        corrupt_info = archive.getinfo("mimetype")
    payload = bytearray(epub_path.read_bytes())
    header = corrupt_info.header_offset
    filename_length = int.from_bytes(payload[header + 26 : header + 28], "little")
    extra_length = int.from_bytes(payload[header + 28 : header + 30], "little")
    payload_offset = header + 30 + filename_length + extra_length
    payload[payload_offset] ^= 0xFF
    epub_path.write_bytes(payload)

    with pytest.raises(zipfile.BadZipFile, match="Bad CRC-32"):
        _normalize_epub_archive(epub_path, source_date_epoch=1700000000)

    assert epub_path.exists()
    assert not list(tmp_path.glob(".corrupt.epub.*.tmp"))


@pytest.mark.parametrize("malformation", ["unlinked-identifier", "invalid-ncx-root"])
def test_normalize_epub_archive_rejects_invalid_identity_structure(
    tmp_path: Path,
    malformation: str,
) -> None:
    """Canonicalization requires a linked OPF ID and actual NCX document root."""

    source = tmp_path / "source.md"
    source.write_text(SAMPLE_MD, encoding="utf-8")
    valid = tmp_path / "valid.epub"
    invalid = tmp_path / f"{malformation}.epub"
    render_epub(source, valid)

    if malformation == "unlinked-identifier":
        with zipfile.ZipFile(valid) as archive:
            opf_name = next(name for name in archive.namelist() if name.endswith(".opf"))
            package = safe_et.fromstring(archive.read(opf_name))
        identifier_id = package.get("unique-identifier")
        assert identifier_id
        replacements = (
            (f'unique-identifier="{identifier_id}"'.encode(), b'unique-identifier="bad id"'),
            (f'id="{identifier_id}"'.encode(), b'id="bad id"'),
        )
        suffix = ".opf"
        expected_error = "unique-identifier attribute"
    else:
        replacements = ((b"<ncx ", b"<invalid-ncx "), (b"</ncx>", b"</invalid-ncx>"))
        suffix = ".ncx"
        expected_error = "valid NCX document root"
    _copy_epub_with_member_replacements(
        valid,
        invalid,
        member_suffix=suffix,
        replacements=replacements,
    )

    with pytest.raises(ValueError, match=expected_error):
        _normalize_epub_archive(invalid, source_date_epoch=1700000000)

    assert invalid.exists()
    assert not list(tmp_path.glob(f".{invalid.name}.*.tmp"))


def test_render_epub_terminal_output_is_authoritative(tmp_path: Path) -> None:
    """A caller output option cannot redirect this renderer's fresh archive."""

    source = tmp_path / "source.md"
    source.write_text(SAMPLE_MD, encoding="utf-8")
    output = tmp_path / "authoritative.epub"
    redirected = tmp_path / "caller-selected.epub"

    render_epub(
        source,
        output,
        extra_args=["-o", str(redirected)],
    )

    package_identifier, navigation_identifier = _package_identifiers(output)
    assert package_identifier == navigation_identifier
    assert not redirected.exists()


def test_render_epub_rejects_extra_arg_identifier_override(tmp_path: Path) -> None:
    """Caller metadata cannot replace the renderer-owned package identifier."""

    source = tmp_path / "source.md"
    source.write_text(SAMPLE_MD, encoding="utf-8")
    output = tmp_path / "rejected-extra.epub"
    requested_identifier = "urn:uuid:11111111-1111-5111-8111-111111111111"

    with pytest.raises(RenderingError, match="identifier does not match"):
        render_epub(
            source,
            output,
            extra_args=[f"--metadata=identifier:{requested_identifier}"],
        )

    assert not output.exists()
    assert not list(tmp_path.glob(".rejected-extra.epub.*"))


def test_render_epub_rejects_filter_identifier_override(tmp_path: Path) -> None:
    """A filter that mutates the terminal placeholder cannot bypass finalization."""

    source = tmp_path / "source.md"
    source.write_text(SAMPLE_MD, encoding="utf-8")
    output = tmp_path / "rejected.epub"
    filter_path = tmp_path / "override-identifier.lua"
    filter_path.write_text(
        "function Meta(meta)\n"
        '  meta.identifier = pandoc.MetaString("urn:uuid:22222222-2222-5222-8222-222222222222")\n'
        "  return meta\n"
        "end\n",
        encoding="utf-8",
    )

    with pytest.raises(RenderingError, match="identifier does not match"):
        render_epub(source, output, extra_args=[f"--lua-filter={filter_path}"])

    assert not output.exists()
    assert not list(tmp_path.glob(".rejected.epub.*"))


def test_render_epub_rejects_nonwriting_success_without_accepting_stale_output(tmp_path: Path) -> None:
    """Exit zero without a fresh temp archive cannot validate an old destination."""

    source = tmp_path / "source.md"
    source.write_text(SAMPLE_MD, encoding="utf-8")
    output = tmp_path / "stale.epub"
    render_epub(source, output)
    stale_bytes = output.read_bytes()
    nonwriting_pandoc = _write_executable(tmp_path / "nonwriting-pandoc", "raise SystemExit(0)\n")

    with pytest.raises(RenderingError, match="was not created"):
        render_epub(source, output, pandoc_path=str(nonwriting_pandoc))

    assert output.read_bytes() == stale_bytes
    assert not list(tmp_path.glob(".stale.epub.*"))


@pytest.mark.parametrize(
    ("case_name", "archive_statements", "payload_mutation", "diagnostic"),
    [
        (
            "member-count",
            '    archive.writestr("mimetype", b"application/epub+zip", '
            "compress_type=zipfile.ZIP_STORED)\n"
            "    for index in range(4096):\n"
            '        archive.writestr(f"payload-{index}", b"x", '
            "compress_type=zipfile.ZIP_STORED)",
            "",
            "member-count limit",
        ),
        (
            "compression-ratio",
            '    archive.writestr("mimetype", b"application/epub+zip", '
            "compress_type=zipfile.ZIP_STORED)\n"
            '    archive.writestr("ratio.bin", b"A" * (1024 * 1024), '
            "compress_type=zipfile.ZIP_DEFLATED)",
            "",
            "compression-ratio limit",
        ),
        (
            "member-size",
            '    archive.writestr("mimetype", b"application/epub+zip", '
            "compress_type=zipfile.ZIP_STORED)\n"
            '    archive.writestr("oversized.bin", b"x", '
            "compress_type=zipfile.ZIP_DEFLATED)",
            'central_offset = payload.find(b"PK\\x01\\x02")\n'
            "while central_offset >= 0:\n"
            '    name_length = int.from_bytes(payload[central_offset + 28:central_offset + 30], "little")\n'
            '    extra_length = int.from_bytes(payload[central_offset + 30:central_offset + 32], "little")\n'
            '    comment_length = int.from_bytes(payload[central_offset + 32:central_offset + 34], "little")\n'
            "    name_start = central_offset + 46\n"
            "    member_name = bytes(payload[name_start:name_start + name_length])\n"
            '    if member_name == b"oversized.bin":\n'
            '        payload[central_offset + 24:central_offset + 28] = (128 * 1024 * 1024 + 1).to_bytes(4, "little")\n'
            "        break\n"
            "    central_offset += 46 + name_length + extra_length + comment_length\n"
            "else:\n"
            '    raise RuntimeError("oversized central-directory entry not found")\n',
            "member exceeds size limit",
        ),
    ],
    ids=["member-count", "compression-ratio", "member-size"],
)
def test_render_epub_preflights_hostile_archive_before_any_payload_read(
    tmp_path: Path,
    case_name: str,
    archive_statements: str,
    payload_mutation: str,
    diagnostic: str,
) -> None:
    """Count, ratio, and size limits reject before a corrupt payload is read."""

    source = tmp_path / "source.md"
    source.write_text(SAMPLE_MD, encoding="utf-8")
    output = tmp_path / f"hostile-{case_name}.epub"
    hostile_pandoc = _write_hostile_pandoc(
        tmp_path / f"hostile-{case_name}-pandoc",
        archive_statements=archive_statements,
        payload_mutation=payload_mutation,
    )

    with pytest.raises(RenderingError, match=diagnostic):
        render_epub(source, output, pandoc_path=str(hostile_pandoc))

    assert not output.exists()
    assert not list(tmp_path.glob(f".{output.name}.*"))


def test_render_epub_embeds_figures_via_resource_path(tmp_path: Path) -> None:
    """Relative ``figures/<name>`` refs must embed when resource-path is the parent.

    Regression: pandoc silently drops images (no error) when the resource-path
    does not make ``figures/x.png`` resolvable. See _combined_exports.py.
    """
    (tmp_path / "figures").mkdir()
    (tmp_path / "figures" / "x.png").write_bytes(_PNG_1x1)
    src = tmp_path / "combined.md"
    src.write_text("# Title\n\n![cap](figures/x.png)\n", encoding="utf-8")
    out = tmp_path / "out.epub"

    render_epub(src, out, extra_args=["--resource-path=" + str(tmp_path)])

    with zipfile.ZipFile(out) as zip_file:
        media = [n for n in zip_file.namelist() if n.lower().endswith(".png")]
    assert media, "expected the figure to be embedded in the EPUB"
