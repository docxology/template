"""Deterministic accessibility post-processing for Pandoc EPUB covers."""

from __future__ import annotations

import os
import stat
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import cast
from xml.etree.ElementTree import Element, register_namespace, tostring

from infrastructure.rendering._epub_package_validation import (
    _CONTAINER_MEMBER,
    _CONTAINER_NAMESPACE,
    _OPF_NAMESPACE,
    _XHTML_MEDIA_TYPE,
    _preflight_members,
    _read_xml_member,
    _resolve_reference,
)

_EPUB_NAMESPACE = "http://www.idpf.org/2007/ops"
_SVG_NAMESPACE = "http://www.w3.org/2000/svg"
_XLINK_NAMESPACE = "http://www.w3.org/1999/xlink"
_COVER_TITLE_ID = "template-epub-cover-title"


def _normalized_alt(value: str) -> str:
    """Return a single-line accessibility description."""

    return " ".join(value.split())


def _cover_members(archive: zipfile.ZipFile) -> tuple[str, str]:
    """Return the Pandoc cover XHTML and image members from a safe EPUB."""

    members = _preflight_members(archive.infolist())
    container = _read_xml_member(archive, members, _CONTAINER_MEMBER)
    rootfiles = container.findall(f".//{{{_CONTAINER_NAMESPACE}}}rootfile")
    package_members: list[str] = []
    for rootfile in rootfiles:
        if rootfile.get("media-type") != "application/oebps-package+xml":
            continue
        resolved = _resolve_reference(
            rootfile.get("full-path"),
            base=PurePosixPath(),
            allow_fragment=False,
        )
        if resolved is not None:
            package_members.append(resolved)
    if len(package_members) != 1:
        raise ValueError("EPUB cover post-processing requires exactly one OPF package")

    package_member = package_members[0]
    package = _read_xml_member(archive, members, package_member)
    manifest = package.find(f"{{{_OPF_NAMESPACE}}}manifest")
    if manifest is None:
        raise ValueError("EPUB OPF package has no manifest")

    xhtml_members: list[str] = []
    cover_images: list[str] = []
    for item in manifest.findall(f"{{{_OPF_NAMESPACE}}}item"):
        properties = set((item.get("properties") or "").split())
        resolved = _resolve_reference(
            item.get("href"),
            base=PurePosixPath(package_member).parent,
            allow_fragment=False,
        )
        if resolved is None:
            continue
        if item.get("media-type") == _XHTML_MEDIA_TYPE:
            xhtml_members.append(resolved)
        if "cover-image" in properties:
            cover_images.append(resolved)
    if len(cover_images) != 1:
        raise ValueError("EPUB cover post-processing requires exactly one cover-image manifest item")

    cover_image = cover_images[0]
    matching_xhtml: list[str] = []
    for xhtml_member in xhtml_members:
        document = _read_xml_member(archive, members, xhtml_member)
        for image in document.findall(f".//{{{_SVG_NAMESPACE}}}image"):
            source = image.get(f"{{{_XLINK_NAMESPACE}}}href") or image.get("href")
            resolved = _resolve_reference(
                source,
                base=PurePosixPath(xhtml_member).parent,
                allow_fragment=False,
            )
            if resolved == cover_image:
                matching_xhtml.append(xhtml_member)
                break
    if len(matching_xhtml) != 1:
        raise ValueError("EPUB cover image must be embedded by exactly one SVG cover document")
    return matching_xhtml[0], cover_image


def _accessible_cover_xhtml(payload: bytes, *, cover_image: str, cover_member: str, alt_text: str) -> bytes:
    """Return cover XHTML with one named SVG graphic and a hidden bitmap primitive."""

    try:
        from defusedxml import ElementTree as safe_et
        from defusedxml.common import DefusedXmlException
    except ImportError as exc:
        raise ValueError("safe EPUB cover processing requires the 'defusedxml' package") from exc
    try:
        root = safe_et.fromstring(payload)
    except (DefusedXmlException, safe_et.ParseError, UnicodeError) as exc:
        raise ValueError(f"malformed EPUB cover XHTML {cover_member}: {exc}") from exc

    matches: list[tuple[Element, Element]] = []
    for svg in root.findall(f".//{{{_SVG_NAMESPACE}}}svg"):
        for image in svg.findall(f".//{{{_SVG_NAMESPACE}}}image"):
            source = image.get(f"{{{_XLINK_NAMESPACE}}}href") or image.get("href")
            resolved = _resolve_reference(
                source,
                base=PurePosixPath(cover_member).parent,
                allow_fragment=False,
            )
            if resolved == cover_image:
                matches.append((svg, image))
    if len(matches) != 1:
        raise ValueError("EPUB cover XHTML must contain exactly one manifested cover image")

    svg, image = matches[0]
    title = svg.find(f"{{{_SVG_NAMESPACE}}}title")
    existing_ids = {node.get("id") for node in root.findall(".//*[@id]") if node is not title and node.get("id")}
    title_id = _COVER_TITLE_ID
    suffix = 2
    while title_id in existing_ids:
        title_id = f"{_COVER_TITLE_ID}-{suffix}"
        suffix += 1

    if title is None:
        title = Element(f"{{{_SVG_NAMESPACE}}}title")
        svg.insert(0, title)
    else:
        for child in list(title):
            title.remove(child)
    title.set("id", title_id)
    title.text = alt_text
    svg.set("role", "img")
    svg.set("aria-labelledby", title_id)
    svg.attrib.pop("aria-label", None)

    # The SVG is the single named graphic. Its bitmap child is an implementation
    # primitive, not a second screen-reader image with a duplicate announcement.
    image.set("aria-hidden", "true")
    image.set("focusable", "false")
    image.attrib.pop("aria-label", None)

    register_namespace("", "http://www.w3.org/1999/xhtml")
    register_namespace("epub", _EPUB_NAMESPACE)
    register_namespace("svg", _SVG_NAMESPACE)
    register_namespace("xlink", _XLINK_NAMESPACE)
    serialized = cast(bytes, tostring(root, encoding="utf-8"))
    return b'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE html>\n' + serialized + b"\n"


def apply_epub_cover_accessibility(epub_path: Path, cover_alt: str) -> None:
    """Inject source-owned cover alt text into Pandoc's SVG cover document.

    The archive is rewritten atomically while preserving member order and each
    member's compression metadata, including EPUB's required first, uncompressed
    ``mimetype`` entry.
    """

    alt_text = _normalized_alt(cover_alt)
    if not alt_text:
        raise ValueError("EPUB cover alternative text must be non-empty")
    if epub_path.is_symlink():
        raise ValueError(f"refusing to rewrite EPUB through symlink: {epub_path}")

    original_mode = stat.S_IMODE(epub_path.stat().st_mode)
    temporary_path: Path | None = None
    try:
        with zipfile.ZipFile(epub_path) as source:
            cover_member, cover_image = _cover_members(source)
            patched_cover = _accessible_cover_xhtml(
                source.read(cover_member),
                cover_image=cover_image,
                cover_member=cover_member,
                alt_text=alt_text,
            )
            with tempfile.NamedTemporaryFile(
                prefix=f".{epub_path.name}.",
                suffix=".tmp",
                dir=epub_path.parent,
                delete=False,
            ) as handle:
                temporary_path = Path(handle.name)
            with zipfile.ZipFile(temporary_path, "w") as destination:
                destination.comment = source.comment
                for info in source.infolist():
                    payload = patched_cover if info.filename == cover_member else source.read(info)
                    destination.writestr(info, payload)
        assert temporary_path is not None
        temporary_path.chmod(original_mode)
        os.replace(temporary_path, epub_path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


__all__ = ["apply_epub_cover_accessibility"]
