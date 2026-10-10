"""Real OOXML package coverage for the versioned hardened Pitch layout digest."""

from __future__ import annotations

import hashlib
import re
from io import BytesIO
from zipfile import ZipFile

import pytest
from PIL import Image
from defusedxml.common import DefusedXmlException

from infrastructure.rendering.pptx_deck import render_pptx
from infrastructure.rendering.slide_deck import DeckContent, Slide
from infrastructure.reporting.native_pitch_source_layout import pitch_package_layout

SLIDE = "ppt/slides/slide2.xml"


@pytest.fixture(scope="module")
def actual_pitch_package(tmp_path_factory: pytest.TempPathFactory) -> bytes:
    directory = tmp_path_factory.mktemp("pitch-xml-layout")
    figure = directory / "source-figure.png"
    Image.new("RGB", (128, 64), "navy").save(figure)
    deck = DeckContent("Measurement", slides=(Slide("Observed", bullets=("Offset -3.25 mV.",), figure_path=figure),))
    return render_pptx(deck, directory / "source.pptx").read_bytes()


def _member(package: bytes, name: str = SLIDE) -> bytes:
    with ZipFile(BytesIO(package)) as archive:
        return archive.read(name)


def _replace_member(package: bytes, data: bytes, name: str = SLIDE) -> bytes:
    result = BytesIO()
    with ZipFile(BytesIO(package)) as archive, ZipFile(result, "w") as target:
        assert name in archive.namelist()
        for row in archive.infolist():
            target.writestr(row, data if row.filename == name else archive.read(row))
    return result.getvalue()


@pytest.mark.parametrize(
    "declaration",
    (
        b"<!DOCTYPE p:sld>",
        b'<!DOCTYPE p:sld [<!ENTITY injected "unadmitted">]>',
        b'<!DOCTYPE p:sld [<!ENTITY injected SYSTEM "file:///unadmitted-pitch-entity">]>',
        b'<!DOCTYPE p:sld SYSTEM "https://example.invalid/unadmitted-pitch.dtd">',
    ),
    ids=("dtd", "internal-entity", "external-entity", "external-dtd"),
)
def test_actual_pitch_xml_refuses_dtd_and_entities(actual_pitch_package: bytes, declaration: bytes) -> None:
    original = _member(actual_pitch_package)
    boundary = original.index(b"?>") + 2
    changed = original[:boundary] + declaration + original[boundary:]
    if b"<!ENTITY injected" in declaration:
        assert b"Observed" in changed
        changed = changed.replace(b"Observed", b"&injected;", 1)
    with pytest.raises(DefusedXmlException):
        pitch_package_layout(_replace_member(actual_pitch_package, changed))


def test_actual_pitch_xml_attribute_order_preserves_layout(actual_pitch_package: bytes) -> None:
    original = _member(actual_pitch_package)
    changed, count = re.subn(
        rb'<a:off x="([0-9]+)" y="([0-9]+)"',
        rb'<a:off y="\2" x="\1"',
        original,
        count=1,
    )
    assert count == 1 and changed != original
    assert pitch_package_layout(actual_pitch_package) == pitch_package_layout(
        _replace_member(actual_pitch_package, changed)
    )


def test_actual_pitch_xml_namespace_binding_remains_committed(actual_pitch_package: bytes) -> None:
    original = _member(actual_pitch_package)
    anchor = b"<p:sld "
    assert original.count(anchor) == 1
    left = original.replace(anchor, b'<p:sld xmlns:compat="urn:source:compatibility" ', 1)
    right = original.replace(anchor, b'<p:sld xmlns:compat="urn:changed:compatibility" ', 1)
    assert pitch_package_layout(_replace_member(actual_pitch_package, left)) != pitch_package_layout(
        _replace_member(actual_pitch_package, right)
    )


def test_actual_pitch_xml_namespace_declaration_order_is_irrelevant(actual_pitch_package: bytes) -> None:
    original = _member(actual_pitch_package)
    anchor = b"<p:sld "
    assert original.count(anchor) == 1
    left = original.replace(anchor, b'<p:sld xmlns:one="urn:one" xmlns:two="urn:two" ', 1)
    right = original.replace(anchor, b'<p:sld xmlns:two="urn:two" xmlns:one="urn:one" ', 1)
    assert pitch_package_layout(_replace_member(actual_pitch_package, left)) == pitch_package_layout(
        _replace_member(actual_pitch_package, right)
    )


def test_actual_pitch_xml_in_bounds_reposition_changes_layout(actual_pitch_package: bytes) -> None:
    original = _member(actual_pitch_package)
    match = re.search(rb'<a:off x="([0-9]+)"', original)
    assert match is not None
    start, end = match.span(1)
    changed = original[:start] + str(int(match[1]) + 9144).encode("ascii") + original[end:]
    assert pitch_package_layout(actual_pitch_package) != pitch_package_layout(
        _replace_member(actual_pitch_package, changed)
    )


def test_actual_pitch_layout_retains_every_presentation_part(actual_pitch_package: bytes) -> None:
    actual = pitch_package_layout(actual_pitch_package)
    with ZipFile(BytesIO(actual_pitch_package)) as archive:
        expected = {name for name in archive.namelist() if name.startswith("ppt/")}
        assert set(actual) == expected
        media = {name for name in expected if not name.endswith((".xml", ".rels"))}
        assert media
        for name in media:
            assert actual[name] == hashlib.sha256(archive.read(name)).hexdigest()


def test_actual_pitch_relationship_target_changes_layout(actual_pitch_package: bytes) -> None:
    name = "ppt/_rels/presentation.xml.rels"
    original = _member(actual_pitch_package, name)
    assert b'Target="slides/slide1.xml"' in original
    changed = original.replace(b'Target="slides/slide1.xml"', b'Target="slides/changed.xml"', 1)
    assert pitch_package_layout(actual_pitch_package) != pitch_package_layout(
        _replace_member(actual_pitch_package, changed, name)
    )


def test_actual_pitch_media_bytes_change_layout(actual_pitch_package: bytes) -> None:
    with ZipFile(BytesIO(actual_pitch_package)) as archive:
        media = sorted(name for name in archive.namelist() if name.startswith("ppt/media/") and name.endswith(".png"))
    assert media
    image = BytesIO()
    Image.new("RGB", (128, 64), "red").save(image, format="PNG")
    before = pitch_package_layout(actual_pitch_package)
    after = pitch_package_layout(_replace_member(actual_pitch_package, image.getvalue(), media[0]))
    assert before[media[0]] != after[media[0]]
    assert {name: value for name, value in before.items() if name != media[0]} == {
        name: value for name, value in after.items() if name != media[0]
    }
